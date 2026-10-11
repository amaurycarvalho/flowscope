## Why

Nenhum acesso HTTP do FlowScope trata explicitamente os códigos 403, 429, 502/504 e 520–524: a classificação atual é binária (`b3/retry.py`: só 400/404 são permanentes; todo o resto é repetido) e só cobre uma parte dos acessos. Na prática, 403 é repetido inutilmente, 429 é repetido sem respeitar `Retry-After`, e downloads (PDF da CVM, notícias, B3, short interest) não repetem nada — um 502/504/520–524 vira `None` silencioso e perde o item. Falta uma política única, por status, aplicada a todos os acessos de leitura/download.

## What Changes

- **Política central por código de status**: classificador puro com quatro categorias — `PERMANENTE` (não repetir), `THROTTLE` (429; 503 com `Retry-After`), `TRANSITORIO` (408, 425, 500, 502, 503, 504, 507, 508, 510) e `GATEWAY` (520–524, com backoff maior). Regra de default: `4xx` permanente (exceto 408/425/429) e `5xx` transitório (exceto 501/505/506/511 permanentes).
- **Motor de retry central (função)**: evolui `executar_com_retry` para usar o classificador, honrar `Retry-After` (com teto), aplicar backoff com jitter e oferecer gancho de cancelamento. Repete apenas métodos idempotentes e POSTs read-only por allowlist explícita.
- **Adoção A–F**: aplica o motor aos acessos de aquisição/download — `funds_client` (JSON B3), programas/censuras/condições regulatórios, documento vinculado de notícias, e os downloads hoje sem retry (PDF da CVM, corpo de notícias, BDR/B3Client, short interest, releases).
- **Exceções explícitas**: probes de cache condicional (304/HEAD) e o provedor de LLM ficam de fora da política comum. O endpoint de programas de aquisição mantém o retry de 404 intermitente por override documentado.
- **403 é permanente** (recurso proibido): não é repetido, inclusive onde hoje é tratado como transitório.

## Capabilities

### New Capabilities
- `politica-erros-http`: classificação de status HTTP e motor de retry uniforme para os acessos de rede (exclui probes de cache condicional e o provedor de LLM).

### Modified Capabilities
- `b3-fii-extraction`: a requirement "Retry e rate-limit na aquisição" deixa de nomear apenas 400/404 e passa a referenciar as categorias da política (403 permanente, 429/5xx/gateway) mantendo a serialização por host.
- `noticias-acquisition`: explicita que o retry do endpoint de programas (404 intermitente) é um override documentado da política, e que o download do corpo do item adota o motor central.

## Impact

- Código: novo `src/flowscope/infrastructure/http_retry.py` (classificador + motor); `b3/retry.py` e `funds_client/base.py` passam a consumi-lo; call sites de `funds_client/regulatorio.py`, `b3/noticias_vinculo.py`, `cvm/pdf.py`, `b3/noticias_aquisicao.py`, `b3/bdr/client.py`, `b3/client.py`, `b3/emprestimos.py`, `funds_client/noticias.py`, `releases/client.py`.
- Comportamento observável: 403 e demais 4xx deixam de ser repetidos; 429 passa a respeitar `Retry-After`; 502/504/520–524 passam a ser repetidos também nos downloads; a serialização "1 requisição por host" é preservada.
- Testes: `tests/test_infrastructure` (classificador e sequências 429→200, 520→200, 403 sem retry) e `tests/test_infrastructure/test_b3_acquisition.py`.
