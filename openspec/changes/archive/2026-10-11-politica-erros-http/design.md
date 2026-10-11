## Context

Ver `proposal.md` — Why. Hoje a classificação vive em `src/flowscope/infrastructure/b3/retry.py`: `ERROS_PERMANENTES = {400, 404}`, `_permanente(exc)` lê `exc.response.status_code`, e `executar_com_retry(fn, delays, sleep)` repete o resto com esperas fixas `(0,1,3,10)`, sem jitter e sem `Retry-After`. Só `funds_client/base._requisicao_get` usa esse motor; `regulatorio._get_programas_json` e `noticias_vinculo._obter` têm laços próprios; os downloads (`cvm/pdf.baixar_pdf_cvm`, `noticias_aquisicao.baixar_noticia`, `bdr/client`, `b3/client`, `emprestimos`, `funds_client/noticias`, `releases/client`) fazem uma tentativa e caem no `except requests.RequestException`. Probes condicionais em `cvm/downloader`, `cvm/datasets` e `fundamentus/client` interpretam 304/403/404 como estado de validação. O adaptador LLM classifica por nome de exceção. Decisões fechadas com o usuário: 403 é permanente; integração por função central; adoção em A–F, com G (probes) e E (LLM) de fora.

## Goals / Non-Goals

**Goals:**
- Uma tabela de classificação única e uma função central de retry usadas por todos os acessos A–F.
- Repetir 429 respeitando `Retry-After`, e 502/504/520–524 onde hoje não há retry.
- Não repetir 403 nem outros permanentes; manter a serialização por host.

**Non-Goals:**
- Não alterar a política do provedor de LLM nem os probes de cache condicional.
- Não introduzir uma subclasse de `requests.Session` nem `HTTPAdapter`/urllib3 (o caminho escolhido é a função central).
- Não mudar os contratos de tolerância a falhas (quem captura continua capturando).

## Decisions

### 1. Módulo canônico `infrastructure/http_retry.py`

Mover a implementação de `b3/retry.py` para um módulo transversal `src/flowscope/infrastructure/http_retry.py`, expondo `Categoria`, `classificar(status, headers)`, `executar_com_retry(...)` e `RETRY_DELAYS`. Atualizar os importadores (`funds_client/base.py` e o teste). Alternativa: manter `b3/retry.py` como fachada — rejeitada por perpetuar um nome enganoso (a política não é da B3) para apenas dois importadores.

### 2. Classificação pura separada do motor

`classificar(status, headers)` é uma função pura (sem I/O) e `executar_com_retry` é o motor. A partir da resposta/erro, o motor deriva a categoria e decide. Alternativa: classificar por exceção do litellm — não se aplica (E é isento). Alternativa: embutir a tabela no motor — piora testabilidade.

### 3. Retry-After, jitter e teto

No ramo `THROTTLE`, ler `Retry-After` (segundos ou data HTTP via `email.utils.parsedate_to_datetime`), capar em `ESPERA_MAXIMA_S = 60` e usar esse valor no lugar do backoff. No ramo `TRANSITORIO`/`GATEWAY`, backoff base `(0,1,3,10)` com jitter multiplicativo proporcional (reusar o padrão do adaptador LLM); `GATEWAY` usa base maior `(0,2,6,18)`. Alternativa: usar só `Retry-After` — rejeitada porque nem sempre vem.

### 4. Método repetível explícito

`executar_com_retry(fn, *, metodo="GET", repetivel=None, ...)`: repete `GET/HEAD/OPTIONS/PUT/DELETE`; para outros métodos, só repete se `repetivel=True` no ponto de chamada. Os POSTs de leitura atuais (`cvm/pdf.baixar_pdf_cvm`, `emprestimos._baixar`) passam `repetivel=True`. Alternativa: inferir pelo método — impossível a partir de um callable opaco.

### 5. Override de códigos por ponto de chamada

`executar_com_retry(..., transitorios_extra=frozenset({404}))` para o endpoint de programas, cujo 404 é intermitente. O override é local e explícito. Alternativa: rebaixar o default de 404 — rejeitada (quebraria a semântica de "recurso inexistente" nos demais).

### 6. Cancelamento e espera limitada

O motor aceita `cancelar: Callable[[], None] | None` e um `sleep` injetável; antes/após cada espera chama `cancelar`, que pode levantar `OperacaoCancelada`. Onde o ponto de chamada não tem token (clientes B3 de JSON), a espera é apenas capada. Threading end-to-end do token de aquisição até o cliente HTTP fica como melhoria incremental: os call sites que já recebem token (aquisição de documentos/notícias) podem passá-lo; os demais mantêm o teto. Alternativa: threading completo agora — rejeitada por ampliar o escopo além do pedido.

### 7. Integração por grupo (A–F) sem mexer em G/E

- A `funds_client/base`: trocar `_permanente` pelo classificador; retry dentro da serialização por host (como hoje).
- B `regulatorio._get_programas_json`: substituir o laço próprio por `executar_com_retry(..., transitorios_extra={404})`.
- C `regulatorio._html_cacheado`: envolver o GET no motor.
- D `noticias_vinculo._obter`: substituir o laço próprio; o POST `ExibirPDF` passa `repetivel=True`.
- F downloads (`cvm/pdf`, `noticias_aquisicao.baixar_noticia`, `bdr/client`, `b3/client`, `emprestimos`, `funds_client/noticias`, `releases/client`): envolver no motor; POSTs de leitura com `repetivel=True`.
- G probes e E LLM: sem alteração.

### 8. Observabilidade

Ao descartar uma repetição `PERMANENTE` ou esgotar tentativas, registrar `status` e categoria via `logger.warning` sem traceback (o `_CommunicationAwareFormatter` já resume `RequestException`). Alternativa: silêncio — mantém o diagnóstico ruim atual.

## Risks / Trade-offs

- [403 permanente pode ser WAF mascarando rate-limit] → Decisão do usuário: 403 é permanente; se um host específico se comportar de outra forma, adiciona-se override pontual.
- [Retry em download de PDF grande aumenta tráfego/tempo] → Mitigação: no máximo 4 tentativas, só em `THROTTLE`/`TRANSITORIO`/`GATEWAY`, nunca em 4xx.
- [Retry-After alto trava operação] → Mitigação: teto de 60 s e gancho de cancelamento.
- [Mudança de comportamento em ~25 call sites] → Mitigação: faseamento A → D/B → F → C, com testes de sequência por grupo.
- [Mover o módulo quebra imports] → Mitigação: só dois importadores; atualizar junto e cobrir com o teste existente de retry.

## Migration Plan

Sem migração de dados. Rollout por grupos, cada um com testes de sequência (`responses` mockando 429→200, 522→200, 403 sem retry). Rollback: restaurar `b3/retry.py` como implementação e os call sites correspondentes. A allowlist de fronteiras de camadas não é afetada (módulo permanece em `infrastructure`).

## Open Questions

Nenhuma pendente.
