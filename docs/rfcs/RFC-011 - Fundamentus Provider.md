# RFC-011: Fundamentus Provider

**Status:** Proposta  
**Autor:** Equipe de Engenharia  
**Data:** 2026-09-10  
**Versão:** 1.0

---

## 1. Resumo Executivo

Esta RFC propõe a especificação e implementação de um **provider** em Python capaz de extrair, normalizar e disponibilizar os dados financeiros fundamentalistas de um ticker (ação ou FII) a partir do portal [Fundamentus](https://www.fundamentus.com.br). O objetivo é oferecer uma interface única, tipada e resiliente para consumo por outros sistemas (screener, dashboards, backtesting).

O portal Fundamentus disponibiliza páginas HTML em `https://www.fundamentus.com.br/detalhes.php?papel={TICKER}`, com estrutura que varia entre **empresas** (ações) e **Fundos Imobiliários (FIIs)**. O provider deve lidar com ambos os layouts e retornar um objeto de domínio consistente.

---

## 2. Motivação

- **Centralização:** hoje não há um componente padronizado que encapsule o parsing do Fundamentus.
- **Tipagem:** os dados retornados são strings formadas (“R$ 691.996.000.000”, “7,3%”, “-0,08%”), exigindo normalização.
- **Robustez:** o HTML muda com o tempo; precisamos de testes de contrato que detectem quebras.
- **Reuso:** um `Provider` bem definido permite que múltiplos consumidores (CLI, API, jobs) compartilhem a mesma lógica.

---

## 3. Escopo

### 3.1 Dentro do escopo

- Extração de dados de **ações** (ex.: `PETR3`) e **FIIs** (ex.: `FIIB11`, `TRXF11`, `KNCR11`, `KNCA11`).
- Parsing dos blocos:
  - Cabeçalho (papel, cotação, data última cotação, mín/máx 52 sem, volume médio 2m).
  - Oscilações (dia, mês, 30 dias, 12 meses, e por ano: 2026, 2025, ...).
  - Indicadores fundamentalistas (P/L, P/VP, DY, ROE, etc.).
  - Balanço Patrimonial.
  - Demonstrativos de Resultados (últimos 12 meses e últimos 3 meses).
  - Para FIIs: composição dos ativos, dados de imóveis.
- Normalização de números, percentuais e datas para tipos Python (`float`, `int`, `Decimal`, `date`).
- Objeto de retorno tipado (`dataclass`).

### 3.2 Fora do escopo

- Persistência em banco de dados.
- Cache distribuído (pode ser adicionado como camada opcional).
- Dados intraday ou séries históricas (o Fundamentus exibe apenas snapshot atual).
- Autenticação (a página é pública).

---

## 4. Requisitos

### 4.1 Funcionais

- RF1: `FundamentusProvider.get(ticker: str) -> Ativo` deve retornar um objeto tipado.
- RF2: O provider deve identificar automaticamente se o ticker é FII ou ação (pelo layout).
- RF3: Campos ausentes (ex.: FII sem imóveis) devem ser retornados como `None` ou valor padrão documentado.
- RF4: Deve haver tratamento de erros: ticker inexistente, HTML alterado, falha de rede.

### 4.2 Não-funcionais

- RNF1: Latência de parsing < 200 ms para uma página típica.
- RNF2: Dependências mínimas: `httpx`/`requests`, `beautifulsoup4`, `lxml`, `pydantic` (opcional).
- RNF3: Deve respeitar `robots.txt` e rate-limit (mínimo 1 req/s por padrão).
- RNF4: Cobertura de testes ≥ 80% com fixtures HTML estáticas.

---

## 5. Design Proposto

### 5.1 Arquitetura

```
+-------------------+        +----------------------+        +-----------------+
|   CLI / API       |  --->  |  FundamentusProvider |  --->  |   Fundamentus   |
|   (consumidor)    |        |  (este componente)   |        |   (HTML)        |
+-------------------+        +----------------------+        +-----------------+
                                      |
                                      v
                             +------------------+
                             |   Parser/Model   |
                             |  (dataclasses)   |
                             +------------------+
```

### 5.2 Modelo de Domínio

```python
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

@dataclass
class Indicadores:
    pl: Optional[float] = None
    pvp: Optional[float] = None
    dividend_yield: Optional[float] = None
    roe: Optional[float] = None
    # ... demais campos

@dataclass
class Demonstrativo:
    receita: Optional[float] = None
    ebit: Optional[float] = None
    lucro_liquido: Optional[float] = None

@dataclass
class Ativo:
    ticker: str
    tipo: str                       # "acao" | "fii"
    nome: str
    cotacao: Optional[float]
    data_ultima_cotacao: Optional[date]
    min_52_sem: Optional[float]
    max_52_sem: Optional[float]
    volume_medio_2m: Optional[float]
    oscilacoes: dict[str, float] = field(default_factory=dict)
    indicadores: Indicadores = field(default_factory=Indicadores)
    balanco: dict[str, float] = field(default_factory=dict)
    demonstrativos_12m: Demonstrativo = field(default_factory=Demonstrativo)
    demonstrativos_3m: Demonstrativo = field(default_factory=Demostrativo)
    # FII-específicos
    composicao_ativos: dict[str, float] = field(default_factory=dict)
    imoveis: dict[str, Optional[float]] = field(default_factory=dict)
    raw: dict[str, str] = field(default_factory=dict)  # fallback
```

---

## 6. Implementação de Referência (Python)

```python
"""
fundamentus_provider.py
Provider de dados financeiros do Fundamentus.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from decimal import Decimal, InvalidOperation

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.fundamentus.com.br/detalhes.php"
USER_AGENT = "Mozilla/5.0 (compatible; FundamentusProvider/1.0)"
DEFAULT_TIMEOUT = 15.0
DEFAULT_RATE_LIMIT_S = 1.0


# --------------------------------------------------------------------------- #
# Normalizadores
# --------------------------------------------------------------------------- #
_NUM_RE = re.compile(r"-?\d[\d\.]*(?:,\d+)?")


def _to_float(texto: str | None) -> Optional[float]:
    """Converte '1.234,56' ou '-0,08%' em float. Retorna None se vazio/'-'."""
    if texto is None:
        return None
    t = texto.strip().replace("\xa0", " ")
    if not t or t in {"-", "--"}:
        return None
    t = t.replace("%", "").replace("R$", "").strip()
    m = _NUM_RE.search(t)
    if not m:
        return None
    raw = m.group(0).replace(".", "").replace(",", ".")
    try:
        return float(Decimal(raw))
    except (InvalidOperation, ValueError):
        return None


def _to_int(texto: str | None) -> Optional[int]:
    v = _to_float(texto)
    return int(v) if v is not None else None


def _to_date(texto: str | None) -> Optional[date]:
    if not texto:
        return None
    t = texto.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(t, fmt).date()
        except ValueError:
            continue
    return None


# --------------------------------------------------------------------------- #
# Modelo
# --------------------------------------------------------------------------- #
@dataclass
class Ativo:
    ticker: str
    tipo: str
    nome: Optional[str] = None
    cotacao: Optional[float] = None
    data_ultima_cotacao: Optional[date] = None
    min_52_sem: Optional[float] = None
    max_52_sem: Optional[float] = None
    volume_medio_2m: Optional[float] = None
    oscilacoes: dict[str, float] = field(default_factory=dict)
    indicadores: dict[str, float] = field(default_factory=dict)
    balanco: dict[str, float] = field(default_factory=dict)
    demonstrativos_12m: dict[str, float] = field(default_factory=dict)
    demonstrativos_3m: dict[str, float] = field(default_factory=dict)
    composicao_ativos: dict[str, float] = field(default_factory=dict)
    imoveis: dict[str, Optional[float]] = field(default_factory=dict)
    raw: dict[str, str] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Provider
# --------------------------------------------------------------------------- #
class FundamentusProvider:
    """
    Extrai dados financeiros de um ticker no portal Fundamentus.

    Exemplo
    -------
    >>> p = FundamentusProvider()
    >>> ativo = p.get("PETR3")
    >>> ativo.cotacao
    53.69
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        rate_limit_s: float = DEFAULT_RATE_LIMIT_S,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._timeout = timeout
        self._rate_limit_s = rate_limit_s
        self._last_request = 0.0
        self._client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            follow_redirects=True,
        )

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #
    def get(self, ticker: str) -> Ativo:
        html = self._fetch(ticker)
        soup = BeautifulSoup(html, "lxml")
        return self._parse(ticker, soup)

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #
    def _fetch(self, ticker: str) -> str:
        elapsed = time.time() - self._last_request
        if elapsed < self._rate_limit_s:
            time.sleep(self._rate_limit_s - elapsed)

        resp = self._client.get(BASE_URL, params={"papel": ticker.upper()})
        self._last_request = time.time()
        resp.raise_for_status()

        if "Nenhum papel encontrado" in resp.text or "não encontrado" in resp.text.lower():
            raise ValueError(f"Ticker '{ticker}' não encontrado no Fundamentus.")
        return resp.text

    def _parse(self, ticker: str, soup: BeautifulSoup) -> Ativo:
        # Detecta tipo: se houver "FII" como rótulo → fii; senão → acao
        labels = [th.get_text(strip=True) for th in soup.find_all("th")]
        tipo = "fii" if "FII" in labels else "acao"

        ativo = Ativo(ticker=ticker.upper(), tipo=tipo)
        ativo.raw = self._collect_raw(soup)

        # Cabeçalho
        ativo.nome = self._first_match(soup, ["Nome", "Empresa"])
        ativo.cotacao = _to_float(self._first_match(soup, ["Cotação"]))
        ativo.data_ultima_cotacao = _to_date(self._first_match(soup, ["Data últ cot"]))
        ativo.min_52_sem = _to_float(self._first_match(soup, ["Min 52 sem"]))
        ativo.max_52_sem = _to_float(self._first_match(soup, ["Max 52 sem"]))
        ativo.volume_medio_2m = _to_float(self._first_match(soup, ["Vol $ méd (2m)"]))

        # Oscilações
        for rotulo in ("Dia", "Mês", "30 dias", "12 meses",
                       "2026", "2025", "2024", "2023", "2022", "2021"):
            v = _to_float(self._first_match(soup, [rotulo]))
            if v is not None:
                ativo.oscilacoes[rotulo] = v

        # Indicadores
        indicadores_labels = [
            "P/L", "P/VP", "P/EBIT", "PSR", "P/Ativos", "P/Cap. Giro",
            "P/Ativ Circ Liq", "Div. Yield", "EV / EBITDA", "EV / EBIT",
            "Cres. Rec (5a)", "LPA", "VPA", "Marg. Bruta", "Marg. EBIT",
            "Marg. Líquida", "EBIT / Ativo", "ROIC", "ROE", "Liquidez Corr",
            "Dív Líq / Patrim", "Giro Ativos",
            "FFO Yield", "FFO/Cota", "Dividendo/cota", "VP/Cota",
        ]
        for rotulo in indicadores_labels:
            v = _to_float(self._first_match(soup, [rotulo]))
            if v is not None:
                ativo.indicadores[rotulo] = v

        # Balanço
        for rotulo in ("Ativo", "Disponibilidades", "Ativo Circulante",
                       "Dív. Bruta", "Dív. Líquida", "Patrim. Líq",
                       "Ativos", "Patrim Líquido"):
            v = _to_float(self._first_match(soup, [rotulo]))
            if v is not None:
                ativo.balanco[rotulo] = v

        # Demonstrativos (12m e 3m) — mesma tabela, colunas diferentes
        ativo.demonstrativos_12m = self._parse_demonstrativos(soup, coluna=0)
        ativo.demonstrativos_3m = self._parse_demonstrativos(soup, coluna=1)

        # FII-específicos
        if tipo == "fii":
            ativo.composicao_ativos = self._parse_composicao(soup)
            ativo.imoveis = {
                "qtd_imoveis": _to_int(self._first_match(soup, ["Qtd imóveis"])),
                "area_m2": _to_float(self._first_match(soup, ["Área (m2)"])),
                "cap_rate": _to_float(self._first_match(soup, ["Cap Rate"])),
                "qtd_unidades": _to_int(self._first_match(soup, ["Qtd Unidades"])),
                "aluguel_m2": _to_float(self._first_match(soup, ["Aluguel/m2"])),
                "vacancia_media": _to_float(self._first_match(soup, ["Vacância Média"])),
                "imoveis_pl": _to_float(self._first_match(soup, ["Imóveis/PL do FII"])),
                "preco_m2": _to_float(self._first_match(soup, ["Preço do m2"])),
            }

        return ativo

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _collect_raw(soup: BeautifulSoup) -> dict[str, str]:
        """Mapeia rótulo → valor para todas as células da página."""
        raw: dict[str, str] = {}
        for tr in soup.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            for i in range(0, len(cells) - 1, 2):
                rotulo = cells[i].get_text(strip=True).lstrip("?")
                valor = cells[i + 1].get_text(strip=True)
                if rotulo and rotulo not in raw:
                    raw[rotulo] = valor
        return raw

    def _first_match(self, soup: BeautifulSoup, rotulos: list[str]) -> Optional[str]:
        raw = self._collect_raw(soup)
        for r in rotulos:
            if r in raw:
                return raw[r]
        return None

    def _parse_demonstrativos(self, soup: BeautifulSoup, coluna: int) -> dict[str, float]:
        """
        Extrai Receita/EBIT/Lucro Líquido (ações) ou Receita/FFO/Rend. Distribuído (FIIs)
        da tabela 'Dados demonstrativos de resultados'.
        coluna=0 → Últimos 12 meses; coluna=1 → Últimos 3 meses.
        """
        out: dict[str, float] = {}
        alvos = ("Receita Líquida", "Receita", "EBIT",
                 "Lucro Líquido", "FFO", "Rend. Distribuído", "Venda de ativos")
        for tr in soup.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            rotulo = cells[0].get_text(strip=True).lstrip("?")
            if rotulo in alvos and len(cells) >= 2 + coluna:
                # cada linha pode ter 2 pares (rótulo/valor) por coluna
                idx = 1 + coluna * 2
                if idx < len(cells):
                    v = _to_float(cells[idx].get_text(strip=True))
                    if v is not None:
                        out[rotulo] = v
        return out

    @staticmethod
    def _parse_composicao(soup: BeautifulSoup) -> dict[str, float]:
        """
        Composição dos ativos (FIIs) aparece como texto/barras.
        Estratégia simplificada: procura por percentuais próximos aos rótulos conhecidos.
        """
        composicao: dict[str, float] = {}
        alvos = ["Imóveis para Renda", "Imóveis em Construção", "Terrenos",
                 "Imóveis para Venda", "Caixa", "CRI / CRA", "LCI / LCA",
                 "Ações de Empresas do Segmento Imobiliário"]
        texto = soup.get_text(" ", strip=True)
        for alvo in alvos:
            idx = texto.find(alvo)
            if idx == -1:
                continue
            trecho = texto[idx: idx + 80]
            m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", trecho)
            if m:
                composicao[alvo] = _to_float(m.group(1))
        return composicao


# --------------------------------------------------------------------------- #
# Demonstração
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    provider = FundamentusProvider()

    for ticker in ("PETR3", "FIIB11", "TRXF11", "KNCR11", "KNCA11"):
        print(f"\n=== {ticker} ===")
        try:
            ativo = provider.get(ticker)
            print(f"tipo: {ativo.tipo}")
            print(f"nome: {ativo.nome}")
            print(f"cotação: {ativo.cotacao}")
            print(f"data últ cot: {ativo.data_ultima_cotacao}")
            print(f"mín/máx 52s: {ativo.min_52_sem} / {ativo.max_52_sem}")
            print(f"vol méd 2m: {ativo.volume_medio_2m}")
            print(f"oscilações: {ativo.oscilacoes}")
            print(f"indicadores: {ativo.indicadores}")
            print(f"balanço: {ativo.balanco}")
            print(f"dem. 12m: {ativo.demonstrativos_12m}")
            print(f"dem. 3m:  {ativo.demonstrativos_3m}")
            if ativo.tipo == "fii":
                print(f"composição: {ativo.composicao_ativos}")
                print(f"imóveis: {ativo.imoveis}")
        except Exception as e:
            print(f"ERRO: {e}")
```

---

## 7. Exemplos de Uso

### 7.1 Ação (PETR3)

```python
provider = FundamentusProvider()
petr = provider.get("PETR3")

assert petr.tipo == "acao"
assert petr.cotacao == 53.69
assert petr.indicadores["P/L"] == 5.19
assert petr.indicadores["ROE"] == 27.7
assert petr.balanco["Patrim. Líq"] == 480_950_000_000.0
assert petr.demonstrativos_12m["Lucro Líquido"] == 133_376_000_000.0
```

### 7.2 FII (FIIB11)

```python
fiib = provider.get("FIIB11")

assert fiib.tipo == "fii"
assert fiib.cotacao == 419.51
assert fiib.indicadores["FFO Yield"] == 10.26
assert fiib.indicadores["P/VP"] == 0.71
assert fiib.imoveis["qtd_imoveis"] == 11
assert fiib.imoveis["area_m2"] == 545_901
assert fiib.demonstrativos_12m["FFO"] == 29_476_100.0
```

### 7.3 FII de papel (KNCR11)

```python
kncr = provider.get("KNCR11")

assert kncr.tipo == "fii"
assert kncr.imoveis["qtd_imoveis"] == 0
assert kncr.composicao_ativos["CRI / CRA"] > 0
```

---

## 8. Estratégia de Testes

| Nível      | Descrição                                                     | Ferramenta             |
| ---------- | ------------------------------------------------------------- | ---------------------- |
| Unitário   | Normalizadores (`_to_float`, `_to_date`)                      | `pytest`               |
| Contrato   | Parsing com fixtures HTML estáticas (PETR3, FIIB11, etc.)     | `pytest` + `responses` |
| Integração | Requisição real (marcada `@pytest.mark.live`)                 | `pytest`               |
| Regressão  | Snapshot do dicionário `raw` para detectar mudanças de layout | `syrupy`               |

**Fixtures recomendadas:** salvar o HTML de `PETR3`, `FIIB11`, `TRXF11`, `KNCR11`, `KNCA11` em `tests/fixtures/` para rodar offline.

---

## 9. Tratamento de Erros

```python
class FundamentusError(Exception): ...
class TickerNotFound(FundamentusError): ...
class LayoutChanged(FundamentusError): ...   # quando campos obrigatórios desaparecem
class NetworkError(FundamentusError): ...
```

- Se `cotacao` e `nome` forem ambos `None` → levantar `LayoutChanged`.
- Se status HTTP ≥ 400 → `NetworkError`.
- Se página contiver “Nenhum papel encontrado” → `TickerNotFound`.

---

## 10. Limitações Conhecidas

1. **Parsing frágil por rótulo textual** — depende de strings exatas (“Vol $ méd (2m)”, “Patrim. Líq”). Mudanças no HTML exigem atualização dos rótulos.
2. **Composição dos ativos** — a extração por regex pode falhar em layouts com gráficos; para produção, considerar capturar via API interna do site ou via `selenium`/`playwright`.
3. **Sem histórico** — o Fundamentus exibe apenas o snapshot atual; séries históricas exigem outra fonte.
4. **Rate limiting** — 1 req/s por padrão. Para muitos tickers, usar fila com backoff exponencial.
5. **KLBN11** — a URL fornecida falhou ao carregar no exemplo; o provider deve tratar `NetworkError`/`TickerNotFound` graciosamente.

---

## 11. Roadmap

| Versão | Entrega                                                               |
| ------ | --------------------------------------------------------------------- |
| 0.1    | Provider básico (esta RFC) + testes unitários                         |
| 0.2    | Cache em disco (TTL 15 min)                                           |
| 0.3    | Exportação para JSON/Parquet                                          |
| 0.4    | CLI (`fundamentus get PETR3 --json`)                                  |
| 0.5    | Fallback via API interna (`/detalhes.php?papel=...&interface=mobile`) |

---

## 12. Alternativas Consideradas

- **Scraping com Selenium/Playwright:** mais robusto para JS, porém mais pesado. O Fundamentus é HTML estático → `httpx` + `BeautifulSoup` é suficiente.
- **Uso de API pública não oficial:** o site expõe variações `interface=mobile` e `interface=classic` que podem simplificar o parsing. Pode ser adotado como fallback.
- **Bibliotecas de terceiros (`fundamentus`, `investpy`):** algumas estão desatualizadas ou quebradas. Preferimos manter o provider sob nosso controle.

---

## 13. Conclusão

A implementação proposta entrega um `FundamentusProvider` simples, testável e extensível, cobrindo tanto ações quanto FIIs. Com fixtures estáticas e testes de contrato, é possível detectar quebras de layout rapidamente. A separação entre `fetch`, `parse` e `model` permite evoluir cada parte independentemente (ex.: adicionar cache sem tocar no parser).

**Próximos passos:**

1. Aprovar esta RFC.
2. Criar repositório `fundamentus-provider` com estrutura `src/`, `tests/fixtures/`, `tests/unit/`.
3. Implementar os testes com os HTMLs dos tickers citados.
4. Publicar versão 0.1 no PyPI interno.
