## Context

Ver `proposal.md - Why`. O estado atual relevante:

- `CacheManager` (`src/flowscope/infrastructure/cache.py`) oferece `get_or_fetch(key, ttl_days, fetch_fn)` (TTL puro) e cache de CSV por data com `put`/`get`/`find_nearest` e escrita atômica (`tmp` + `rename`).
- O `FundamentusProvider` usa `get_or_fetch` com `_TTL_DIAS = 7`, guardando o HTML cru (`provider.py:45`). O `FundamentusClient.fetch` devolve `str` e não expõe headers (`client.py:42`).
- `CvmDatasetDownloader.baixar_ano` e `CvmMonthlyDownloader.baixar_ano` retornam o arquivo local se o caminho existir, sem nenhuma revalidação remota (`datasets.py:99`, `downloader.py:52`). Metadados já são gravados (`dataset`, `year`, `url`, `downloaded_at`, `sha256`, `parser_version`), mas não são usados para decidir rebaixamento.
- A GUI já tem `_flash_status`/`set_status` (`app_status.py:40`, `presenter.py:158`) e o caso de uso aceita `progress_callback` (`fundamental_analysis.py:81`).

Restrições: manter a API pública dos providers; reutilizar `requests` e o diretório `~/.cache/flowscope/`; não introduzir dependência externa; não acoplar infraestrutura à apresentação.

## Goals / Non-Goals

**Goals:**

- Um mecanismo único de cache condicional reutilizável pelas fontes, com validadores plugáveis e políticas de frescor/revalidação/retenção independentes.
- Corrigir a frescura do arquivo anual da CVM (ano corrente) com revalidação remota e comportamento stale-on-failure.
- Revalidar o snapshot do Fundamentus pela `Data últ cot` (primário) e headers HTTP (secundário), com coalescência de rede.
- Reportar o resultado do cache de forma que a GUI possa sinalizar "Dados atualizados".

**Non-Goals:**

- Cache distribuído (Redis/Memcached) e métricas Prometheus (propostas na RFC-012, fora do escopo atual).
- Alterar a camada B3 e o motor de FFO (tratados em change futura).
- Cache de resultado negativo (ticker inexistente) — permanece sem cache nesta change.
- Reescrita do `CacheManager` existente ou remoção de `get_or_fetch` (permanecem por compatibilidade).

## Decisions

### 1. Evoluir a base existente em vez de criar um subsistema paralelo

Novo módulo `src/flowscope/infrastructure/conditional_cache.py` com a mecânica genérica, reaproveitando o `CacheManager` para diretório padrão e escrita atômica.

**Alternativas:** adotar `CacheBackend`/`MemoryCache`/`DiskCache` da RFC-012 (duplica o `CacheManager`, fixa `~/.cache/fundamentus` e ignora paths por plataforma) → rejeitada.

```text
+---------------------------+        +-----------------------------+
|  FundamentusProvider      |        |  Cvm*Downloader             |
|  (get_or_revalidate)      |        |  (file_or_revalidate)       |
+-------------+-------------+        +--------------+--------------+
              |                                     |
              v                                     v
      +-------------------------------------------------------+
      |        conditional_cache (novo módulo)                |
      |  get_or_revalidate(key, validators, parse, policies)  |
      |  get_file_or_revalidate(path, validators, fetch)      |
      +----------------------------+--------------------------+
                                   |
                    +--------------+--------------+
                    v                             v
             HttpValidator                  DateValidator
             (ETag/Last-Modified/304)       (Data últ cot)
                                   |
                    +--------------+--------------+
                    v                             v
             CacheManager (diretório, escrita atômica, metadados)
```

### 2. Protocolo de validador e resultado de revalidação

```python
class RevalidationStatus(Enum):
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    UNKNOWN = "unknown"

class CacheOutcome(Enum):
    HIT = "hit"                 # servido do cache, sem rede
    REVALIDATED = "revalidated" # confirmado igual à fonte
    UPDATED = "updated"         # substituído por valor novo
    MISS = "miss"               # não havia cache

class Validator(Protocol):
    def revalidate(self, record: CacheRecord) -> RevalidationResult: ...
```

`CacheRecord` carrega `payload`, `validators` (ex.: `etag`, `last_modified`), `fetched_at` e `parser_version`. O cache itera os validadores na ordem informada e usa a primeira resposta definitiva; se todos retornarem `UNKNOWN`, cai na política de TTL.

**Alternativas:** validador que já retorna o payload parseado (acopla parser ao validador) → rejeitada; comparação de hash do HTML completo (exige GET completo, sem ganho sobre a data) → rejeitada.

### 3. Fundamentus: cachear HTML cru versionado, não o modelo parseado

Guardar o HTML cru com `parser_version` na chave/metadados. Evita a serialização frágil de `AtivoFundamental` (frozen, `Decimal`, `date`, dicionários aninhados) e preserva fidelidade; re-parsear é barato.

**Alternativas:** serializar `AtivoFundamental` com `asdict`/`dataclasses` (perde tipo de `Decimal` e não reconstrói aninhados) → rejeitada.

### 4. Fundamentus: data de cotação como validador primário, HTTP como secundário

`DateValidator` extrai a `Data últ cot` do HTML remoto e considera `UNCHANGED` quando a data remota não é posterior à armazenada. `HttpValidator` tenta `If-None-Match`/`If-Modified-Since` e trata `304` como `UNCHANGED`. O `FundamentusClient` ganha um método que devolve `requests.Response` (headers + texto), mantendo `fetch` para compatibilidade.

### 5. Políticas independentes com coalescência

- `freshness`: idade máxima para servir sem rede (default por fonte).
- `revalidate_after`: intervalo mínimo entre checagens remotas (coalescência; default Fundamentus 1 h, CVM 6 h).
- `retention`: quando evictar do disco (default 2× o TTL de segurança).

Isso corrige a contradição da RFC-012, que faria GET condicional a cada chamada.

### 6. CVM: revalidar o arquivo anual por validadores HTTP

Antes de reutilizar o ZIP local, fazer probe remoto (HEAD com `If-Modified-Since` a partir dos metadados; fallback para GET condicional) e comparar `Last-Modified`/`Content-Length`/`ETag`. Só baixar quando mudou. Em falha do probe, servir o arquivo local (stale-on-failure) e registrar aviso. Atualizar `last_modified`/`etag`/`revalidated_at` nos metadados.

**Alternativas:** hash remoto publicado pela CVM (não existe); rebaixar sempre (desperdício de banda); manter existência-only (é o bug).

### 7. Resultado do cache sobe como dado, não como acoplamento

Os providers ganham um método que devolve o valor junto do `CacheOutcome` (ex.: `get_with_outcome`), preservando `get`/`patrimonio`. A aplicação agrega "houve atualização?" e a apresentação decide exibir "Dados atualizados" via `set_status`.

**Alternativas:** infraestrutura chamar a statusbar diretamente → rejeitada (vazamento de camada).

## Risks / Trade-offs

- **[Risco] Fundamentus pode não enviar `ETag`/`Last-Modified`** → a validação primária é a `Data últ cot`; sem headers, ainda há GET completo, mas evita re-parse/re-store. Confirmar em spike (ver Open Questions).
- **[Risco] Servidor pode não responder bem a `HEAD`** → fallback para GET condicional com `Range` mínimo ou GET completo.
- **[Risco] Comparar `Last-Modified` da CVM pode gerar falso "alterado"** (regeneração do ZIP sem mudança de conteúdo) → aceitável: rebaixa uma vez e atualiza metadados; pode ser refinado com hash depois.
- **[Risco] Cachear HTML cru acopla invalidação à versão do parser** → `parser_version` obrigatório na chave; testes cobrem a troca de versão.
- **[Trade-off] Coalescência reduz requisições mas pode atrasar a percepção de um dado novo** → intervalos configuráveis; o `force_refresh` cobre necessidade imediata.
- **[Risco] Duplicação entre `CvmMonthlyDownloader` e `CvmDatasetDownloader`** → aplicar a mesma estratégia aos dois e, se trivial, unificar a revalidação num helper compartilhado.

## Migration Plan

1. Adicionar o mecanismo genérico e os validadores sem alterar chamadas existentes (`get_or_fetch` continua).
2. Migrar o `FundamentusProvider` para revalidação condicional e expor o resultado.
3. Migrar os downloaders CVM para revalidação remota com stale-on-failure.
4. Ligar o resultado à statusbar na apresentação.
5. **Ordenação de archive**: `fundamentus-fundamental-provider` e `cvm-monthly-fund-data` precisam estar sincronizadas/arquivadas em `openspec/specs/` antes desta change, pois os deltas usam `ADDED Requirements` sobre capabilities ainda não arquivadas.

**Rollback:** remover o uso do cache condicional nos providers e voltar a `get_or_fetch`/existência de arquivo; o mecanismo novo é aditivo e pode permanecer sem uso.

## Open Questions

- O Fundamentus envia `ETag`/`Last-Modified`? Um spike com uma requisição real responde; não altera o design, que já tem a data como validador primário.
- Vale unificar `CvmMonthlyDownloader` e `CvmDatasetDownloader` nesta change ou apenas aplicar a mesma estratégia aos dois? Decisão de implementação que não muda specs nem abordagem.
- Intervalos padrão de frescor/revalidação podem ser calibrados após observação em produção.
