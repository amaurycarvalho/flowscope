# RFC-012: Cache Condicional para o Fundamentus Provider

**Status:** Proposta  
**Autor:** Equipe de Engenharia  
**Data:** 2026-09-10  
**Versão:** 1.0  
**Depende de:** RFC-011 (Provider de Dados Financeiros do Fundamentus)

---

## 1. Resumo Executivo

Esta RFC propõe uma estratégia de **cache condicional** para o `FundamentusProvider` (RFC-001). A ideia central é evitar requisições HTTP desnecessárias armazenando localmente o último snapshot de cada ticker e usando o campo **“Data últ cot”** (data da última cotação) como _cache validator_. Se a página remota ainda se refere à mesma data de cotação já armazenada, o provider devolve o dado em cache sem reprocessar o HTML. Caso contrário, baixa e atualiza o cache.

Complementarmente, propomos um **TTL de segurança** e um mecanismo de **validação por `ETag`/`Last-Modified`** quando disponível, cobrindo situações em que a data de cotação não muda (ex.: FIIs com baixa liquidez, fins de semana, feriados).

Ao final da carga dos dados em background, deverá ter uma mensagem no statusbar de "Dados atualizados".

---

## 2. Motivação

- **Economia de banda e latência:** o Fundamentus é HTML denso (~100–300 KB por página). Reprocessar dezenas de tickers por dia é custoso e desnecessário, pois os dados só mudam após o fechamento do pregão.
- **Redução de risco de bloqueio:** menos requisições ⇒ menor chance de rate-limit/IP-ban.
- **Determinismo:** consumidores ganham previsibilidade — se o snapshot em cache já reflete a última data de cotação, ele é considerado “fresco”.
- **Resiliência:** se o site cair, o cache continua servindo.

### Observação empírica

Nos exemplos da RFC-001, todos os tickers (`FIIB11`, `PETR3`, `TRXF11`, `KNCR11`, `KNCA11`) exibiam `Data últ cot = 09/09/2026`. Ou seja, no dia 10/09/2026, a data de última cotação é **D-1** (dia útil anterior). Isso confirma que o campo é um bom _validator_ de “dado já consolidado”.

---

## 3. Escopo

### 3.1 Dentro do escopo

- Camada de cache plugável (`CacheBackend`).
- Backends padrão: **memória** (LRU) e **disco** (JSON em `~/.cache/fundamentus`).
- Política de invalidação baseada em:
  1. `data_ultima_cotacao` (primária).
  2. `ETag`/`Last-Modified` (secundária, se o servidor enviar).
  3. TTL máximo de segurança (ex.: 24 h).
- API `FundamentusProvider.get(ticker, force_refresh=False)`.

### 3.2 Fora do escopo

- Cache distribuído (Redis, Memcached) — deixamos a interface `CacheBackend` extensível.
- Compressão de payload em disco (pode ser adicionada depois).
- Invalidação baseada em conteúdo do balanço (o Fundamentus não expõe hash).

---

## 4. Estratégia de Invalidação

### 4.1 Chave de cache

```
chave = f"fundamentus:{ticker.upper()}"
```

### 4.2 Registro armazenado

```json
{
  "ticker": "PETR3",
  "data_ultima_cotacao": "2026-09-09",
  "fetched_at": "2026-09-10T08:12:33Z",
  "etag": "W/\"abc123\"",
  "last_modified": "Wed, 09 Sep 2026 18:00:00 GMT",
  "payload": { ... objeto Ativo serializado ... }
}
```

### 4.3 Algoritmo de decisão

```
1. Carrega registro do cache.
2. Se NÃO existe → baixa, parseia, salva.
3. Se existe:
   a. Se force_refresh=True → baixa, parseia, salva.
   b. Se (agora - fetched_at) > TTL_MAX (padrão 24h) → baixa, parseia, salva.
   c. Caso contrário, faz HEAD/GET condicional:
      - Se etag e/ou last_modified existem no cache:
          envia If-None-Match / If-Modified-Since.
          - 304 Not Modified → devolve cache.
          - 200 OK → compara nova data_ultima_cotacao:
              · igual à do cache → devolve cache (atualiza fetched_at).
              · diferente → salva novo cache e devolve.
      - Se não há validators HTTP:
          faz GET completo e compara data_ultima_cotacao.
```

### 4.4 Regra da “data de última cotação”

> **Regra de ouro:** se `nova_data_ult_cot <= cached_data_ult_cot`, o cache é considerado fresco.

Isso cobre:

- Fins de semana e feriados (data não avança).
- FIIs sem negócio no dia.
- Reprocessamento no mesmo dia.

**Exceção:** se `nova_data_ult_cot == cached_data_ult_cot` mas algum campo do balanço mudou (raro, ex.: ajuste retroativo), não temos como detectar sem hash. Por isso o TTL de segurança (24 h) força uma atualização periódica mesmo quando a data não muda.

---

## 5. Arquitetura

```
+---------------------+        +---------------------+        +-------------------+
|  FundamentusProvider|  --->  |    CacheBackend      |  --->  |  Memória / Disco  |
|  (RFC-001 + cache)  |        |  (interface)         |        |  / Redis / ...    |
+---------------------+        +---------------------+        +-------------------+
          |
          v
   +--------------+
   |  httpx.Client|
   |  (condicional|
   |   GET/HEAD)  |
   +--------------+
```

### 5.1 Interface `CacheBackend`

```python
class CacheBackend(Protocol):
    def get(self, key: str) -> Optional[dict]: ...
    def set(self, key: str, value: dict, ttl_s: Optional[int] = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def clear(self) -> None: ...
```

---

## 6. Implementação de Referência (Python)

```python
"""
fundamentus_cache.py
Cache condicional para o FundamentusProvider (RFC-002).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional, Protocol

import httpx
from bs4 import BeautifulSoup

from fundamentus_provider import Ativo, FundamentusProvider, _to_date


# --------------------------------------------------------------------------- #
# Interface de cache
# --------------------------------------------------------------------------- #
class CacheBackend(Protocol):
    def get(self, key: str) -> Optional[dict]: ...
    def set(self, key: str, value: dict, ttl_s: Optional[int] = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def clear(self) -> None: ...


class MemoryCache:
    """Cache LRU simples em memória."""

    def __init__(self, max_size: int = 512) -> None:
        from collections import OrderedDict
        self._store: "OrderedDict[str, tuple[dict, Optional[float]]]" = OrderedDict()
        self._max = max_size

    def get(self, key: str) -> Optional[dict]:
        item = self._store.get(key)
        if not item:
            return None
        value, expires_at = item
        if expires_at is not None and time.time() > expires_at:
            self._store.pop(key, None)
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: dict, ttl_s: Optional[int] = None) -> None:
        expires_at = time.time() + ttl_s if ttl_s else None
        self._store[key] = (value, expires_at)
        self._store.move_to_end(key)
        while len(self._store) > self._max:
            self._store.popitem(last=False)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


class DiskCache:
    """Cache em disco, um arquivo JSON por chave."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = Path(root or os.path.expanduser("~/.cache/fundamentus"))
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = key.replace(":", "__").replace("/", "_")
        return self.root / f"{safe}.json"

    def get(self, key: str) -> Optional[dict]:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        exp = data.get("_expires_at")
        if exp is not None and time.time() > exp:
            p.unlink(missing_ok=True)
            return None
        return data

    def set(self, key: str, value: dict, ttl_s: Optional[int] = None) -> None:
        data = dict(value)
        data["_expires_at"] = time.time() + ttl_s if ttl_s else None
        self._path(key).write_text(
            json.dumps(data, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def clear(self) -> None:
        for f in self.root.glob("*.json"):
            f.unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# Provider com cache condicional
# --------------------------------------------------------------------------- #
DEFAULT_TTL_MAX_S = 24 * 60 * 60  # 24h


@dataclass
class CachedAtivo:
    ativo: Ativo
    data_ultima_cotacao: Optional[date]
    fetched_at: datetime
    etag: Optional[str] = None
    last_modified: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "ticker": self.ativo.ticker,
            "data_ultima_cotacao": (
                self.data_ultima_cotacao.isoformat()
                if self.data_ultima_cotacao else None
            ),
            "fetched_at": self.fetched_at.astimezone(timezone.utc).isoformat(),
            "etag": self.etag,
            "last_modified": self.last_modified,
            "payload": _ativo_to_dict(self.ativo),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CachedAtivo":
        return cls(
            ativo=_ativo_from_dict(d["payload"]),
            data_ultima_cotacao=(
                date.fromisoformat(d["data_ultima_cotacao"])
                if d.get("data_ultima_cotacao") else None
            ),
            fetched_at=datetime.fromisoformat(d["fetched_at"]),
            etag=d.get("etag"),
            last_modified=d.get("last_modified"),
        )


def _ativo_to_dict(a: Ativo) -> dict:
    d = asdict(a)
    if a.data_ultima_cotacao:
        d["data_ultima_cotacao"] = a.data_ultima_cotacao.isoformat()
    return d


def _ativo_from_dict(d: dict) -> Ativo:
    if d.get("data_ultima_cotacao"):
        d["data_ultima_cotacao"] = date.fromisoformat(d["data_ultima_cotacao"])
    return Ativo(**d)


class CachedFundamentusProvider(FundamentusProvider):
    """
    Provider com cache condicional.

    Uso
    ---
    >>> p = CachedFundamentusProvider(cache=DiskCache())
    >>> ativo = p.get("PETR3")             # baixa se necessário
    >>> ativo2 = p.get("PETR3")            # devolve do cache
    >>> ativo3 = p.get("PETR3", force_refresh=True)
    """

    def __init__(
        self,
        cache: Optional[CacheBackend] = None,
        ttl_max_s: int = DEFAULT_TTL_MAX_S,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.cache = cache or MemoryCache()
        self.ttl_max_s = ttl_max_s

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #
    def get(self, ticker: str, force_refresh: bool = False) -> Ativo:
        key = f"fundamentus:{ticker.upper()}"

        if force_refresh:
            return self._fetch_and_store(ticker, key)

        cached = self._load_cache(key)
        if cached is None:
            return self._fetch_and_store(ticker, key)

        # TTL de segurança
        idade = (datetime.now(timezone.utc) - cached.fetched_at).total_seconds()
        if idade > self.ttl_max_s:
            return self._fetch_and_store(ticker, key)

        # GET condicional
        resp = self._conditional_get(ticker, cached)

        # 304 Not Modified → cache fresco
        if resp.status_code == 304:
            self._touch(key, cached)
            return cached.ativo

        resp.raise_for_status()

        # 200 OK → comparar data de última cotação
        soup = BeautifulSoup(resp.text, "lxml")
        nova = self._parse(ticker, soup)
        nova_data = nova.data_ultima_cotacao

        if (
            cached.data_ultima_cotacao is not None
            and nova_data is not None
            and nova_data <= cached.data_ultima_cotacao
        ):
            # Dado ainda é o mesmo → devolve cache, atualiza metadados
            self._touch(key, cached, resp=resp)
            return cached.ativo

        # Dado novo → salva
        return self._store(key, nova, resp)

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #
    def _load_cache(self, key: str) -> Optional[CachedAtivo]:
        raw = self.cache.get(key)
        if not raw or "payload" not in raw:
            return None
        try:
            return CachedAtivo.from_dict(raw)
        except (KeyError, ValueError, TypeError):
            return None

    def _store(
        self,
        key: str,
        ativo: Ativo,
        resp: Optional[httpx.Response] = None,
    ) -> Ativo:
        cached = CachedAtivo(
            ativo=ativo,
            data_ultima_cotacao=ativo.data_ultima_cotacao,
            fetched_at=datetime.now(timezone.utc),
            etag=(resp.headers.get("ETag") if resp else None),
            last_modified=(resp.headers.get("Last-Modified") if resp else None),
        )
        self.cache.set(key, cached.to_dict(), ttl_s=self.ttl_max_s * 2)
        return ativo

    def _touch(
        self,
        key: str,
        cached: CachedAtivo,
        resp: Optional[httpx.Response] = None,
    ) -> None:
        """Atualiza apenas metadados (fetched_at, etag, last_modified)."""
        cached.fetched_at = datetime.now(timezone.utc)
        if resp is not None:
            cached.etag = resp.headers.get("ETag", cached.etag)
            cached.last_modified = resp.headers.get("Last-Modified", cached.last_modified)
        self.cache.set(key, cached.to_dict(), ttl_s=self.ttl_max_s * 2)

    def _fetch_and_store(self, ticker: str, key: str) -> Ativo:
        html = self._fetch(ticker)
        soup = BeautifulSoup(html, "lxml")
        ativo = self._parse(ticker, soup)
        # Nota: para capturar ETag/Last-Modified, o _fetch precisaria
        # retornar a Response. Ver §7 (refatoração sugerida).
        return self._store(key, ativo)

    def _conditional_get(
        self,
        ticker: str,
        cached: CachedAtivo,
    ) -> httpx.Response:
        headers: dict[str, str] = {}
        if cached.etag:
            headers["If-None-Match"] = cached.etag
        if cached.last_modified:
            headers["If-Modified-Since"] = cached.last_modified

        return self._client.get(
            "https://www.fundamentus.com.br/detalhes.php",
            params={"papel": ticker.upper()},
            headers=headers,
        )
```

> **Nota de refatoração:** para que `_fetch_and_store` também capture `ETag`/`Last-Modified`, sugerimos alterar `_fetch` na RFC-001 para devolver `httpx.Response` e obter `resp.text` no chamador. Mantivemos o exemplo acima compatível com a assinatura atual, mas é uma melhoria natural.

---

## 7. Uso

```python
from fundamentus_cache import (
    CachedFundamentusProvider, DiskCache, MemoryCache,
)

# Cache em memória (rápido, volátil)
p = CachedFundamentusProvider(cache=MemoryCache(max_size=256))

# Cache em disco (persistente entre execuções)
p = CachedFundamentusProvider(cache=DiskCache())

# Primeira chamada → baixa e armazena
petr = p.get("PETR3")

# Segunda chamada no mesmo dia → cache (ou 304 se servidor suportar)
petr2 = p.get("PETR3")
assert petr2.cotacao == petr.cotacao

# Forçar atualização
petr3 = p.get("PETR3", force_refresh=True)
```

---

## 8. Considerações sobre o Fundamentus

### 8.1 O servidor envia `ETag`/`Last-Modified`?

O Fundamentus é servido por Apache/PHP. Historicamente **não** envia `ETag`, mas pode enviar `Last-Modified` dependendo da configuração. Nossa estratégia **não depende** disso: a validação primária é pela `data_ultima_cotacao`.

**Plano B (fallback):** se não houver validators HTTP e o TTL de segurança ainda não expirou, ainda fazemos GET completo, mas evitamos salvar se a data não mudou — economizando I/O de disco, não banda.

### 8.2 Quando a data muda?

- **Ações (PETR3, KLBN11):** a cada dia útil, após o fechamento (~18h B3). Em fins de semana e feriados, permanece D-1.
- **FIIs (FIIB11, KNCR11):** mesma regra, mas FIIs sem negócio no dia podem manter a data anterior por vários dias.
- **Casos especiais:** FIIs recém-listados ou suspensos podem ter `Data últ cot` igual à data de listagem por semanas.

### 8.3 E se o balanço for atualizado sem mudar a cotação?

Raro, mas acontece (ex.: reapresentação de ITR). Nesses casos, apenas o **TTL de segurança de 24 h** garante atualização. Se isso for crítico, podemos:

- Adicionar um hash do bloco `<table>` do balanço ao registro de cache.
- Ou reduzir o TTL para 6 h para tickers “sensíveis”.

Recomendamos começar com 24 h e ajustar conforme observação.

---

## 9. Estratégia de Testes

| Teste                          | Descrição                                                        |
| ------------------------------ | ---------------------------------------------------------------- |
| `test_cache_hit_mesma_data`    | Cache retorna sem nova requisição quando `data_ult_cot` é igual. |
| `test_cache_miss_data_nova`    | Nova `data_ult_cot` ⇒ cache é substituído.                       |
| `test_force_refresh`           | Ignora cache e baixa.                                            |
| `test_ttl_expirado`            | Após TTL, força download mesmo com mesma data.                   |
| `test_etag_304`                | Mock de `304 Not Modified` ⇒ devolve cache.                      |
| `test_disk_cache_persistencia` | Escreve, recria provider, lê cache.                              |
| `test_limpeza_memoria_lru`     | Excede `max_size` ⇒ item mais antigo é removido.                 |
| `test_payload_corrompido`      | JSON inválido em disco ⇒ tratado como miss.                      |

Fixtures: usar `responses` ou `respx` para simular `ETag`, `304` e variações de `data_ult_cot`.

---

## 10. Métricas Sugeridas

- `fundamentus_cache_hit_total` (counter)
- `fundamentus_cache_miss_total` (counter)
- `fundamentus_http_304_total` (counter)
- `fundamentus_http_200_total` (counter)
- `fundamentus_cache_idade_segundos` (histogram)

Úteis para calibrar TTL e detectar mudanças de comportamento do site.

---

## 11. Alternativas Consideradas

| Alternativa                       | Prós                     | Contras                                                           | Decisão                            |
| --------------------------------- | ------------------------ | ----------------------------------------------------------------- | ---------------------------------- |
| Cache só por TTL fixo (ex.: 24 h) | Simples                  | Ignora mudanças intra-dia; baixa sem necessidade                  | Rejeitada como estratégia primária |
| Cache só por `data_ult_cot`       | Ótimo custo/benefício    | Não detecta ajustes retroativos                                   | Adotada + TTL de segurança         |
| Comparar hash do HTML completo    | Detecta qualquer mudança | Requer GET completo; sem ganho sobre `data_ult_cot` no caso comum | Rejeitada                          |
| `HEAD` antes do `GET`             | Não baixa corpo          | Fundamentus pode não responder bem a `HEAD`                       | Não prioritária                    |
| Webhook/push do Fundamentus       | Ideal                    | Não existe                                                        | Fora de escopo                     |

---

## 12. Roadmap

| Versão | Entrega                                                                                   |
| ------ | ----------------------------------------------------------------------------------------- |
| 0.1    | `MemoryCache` + `DiskCache` + `CachedFundamentusProvider`                                 |
| 0.2    | Suporte a `ETag`/`Last-Modified` (depende de refatorar `_fetch` para devolver `Response`) |
| 0.3    | Backend Redis opcional                                                                    |
| 0.4    | CLI `fundamentus get PETR3 --cache-dir ~/.cache --force`                                  |
| 0.5    | Métricas Prometheus                                                                       |

---

## 13. Conclusão

O cache condicional proposto resolve o problema central: **baixar dados do Fundamentus apenas quando há dados novos**. A chave é usar o campo `Data últ cot` como _validator_ primário, complementado por `ETag`/`Last-Modified` quando disponíveis e por um TTL de segurança de 24 h para cobrir casos exóticos (ajustes retroativos, servidor sem headers condicionais).

A solução é:

- **Simples:** ~200 linhas somando cache + provider.
- **Plugável:** `CacheBackend` permite trocar memória ↔ disco ↔ Redis sem tocar no provider.
- **Testável:** todos os caminhos (hit, miss, 304, TTL, corrupção) cobertos por testes determinísticos.
- **Compatível:** mantém a API `get(ticker)` da RFC-001, adicionando apenas `force_refresh`.

**Próximos passos:**

1. Aprovar esta RFC.
2. Refatorar `_fetch` da RFC-001 para devolver `httpx.Response` (pré-requisito para capturar `ETag`).
3. Implementar `MemoryCache` e `DiskCache` com testes.
4. Medir taxa de acerto em produção por 1 semana antes de reduzir TTL.
