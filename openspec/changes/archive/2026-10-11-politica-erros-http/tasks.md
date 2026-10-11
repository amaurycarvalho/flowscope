## 1. Módulo central e classificador

- [x] 1.1 Criar `src/flowscope/infrastructure/http_retry.py` com o enum `Categoria` e `classificar(status, headers)`, movendo `RETRY_DELAYS`; verificar com testes unitários dos códigos 403, 404, 408, 425, 429, 500, 501, 502, 503 (com e sem Retry-After), 504 e 520–524.
- [x] 1.2 Atualizar os importadores de `flowscope.infrastructure.b3.retry` (`funds_client/base.py` e `tests/test_infrastructure/test_b3_acquisition.py`) para o novo módulo e remover `b3/retry.py`; verificar que a suíte de aquisição continua verde.

## 2. Motor de retry

- [x] 2.1 Implementar `executar_com_retry(fn, *, metodo, repetivel, transitorios_extra, delays, sleep, cancelar)` no módulo central, repetindo só categorias repetíveis e só métodos idempotentes (ou `repetivel=True`); verificar com testes de GET repetido, POST marcado repetido e POST não marcado não repetido.
- [x] 2.2 Implementar o respeito ao `Retry-After` (segundos e data HTTP) com teto `ESPERA_MAXIMA_S`, e o backoff com jitter, com base maior para `GATEWAY`; verificar com testes de espera (sleep injetado) para 429 com `Retry-After` e para 522.
- [x] 2.3 Adicionar o override `transitorios_extra` e o gancho `cancelar` (que pode levantar `OperacaoCancelada`); verificar com teste de 404 repetido por override e de cancelamento interrompendo a espera.
- [x] 2.4 Registrar status e categoria ao descartar repetição permanente ou esgotar tentativas; verificar com teste que captura o log.

## 3. Adoção no grupo A (JSON B3)

- [x] 3.1 Trocar `_permanente` pelo classificador central em `funds_client/base._requisicao_get`, mantendo o retry dentro da serialização por host; verificar com testes de aquisição que 403 não repete e 502 repete.

## 4. Adoção nos grupos B e C (regulatórios)

- [x] 4.1 Substituir o laço de `regulatorio._get_programas_json` pelo motor central com `transitorios_extra={404}`; verificar com `tests/test_infrastructure/test_regulacao/test_programas_client.py`.
- [x] 4.2 Envolver o GET de `regulatorio._html_cacheado` no motor central (censuras e condições); verificar com `test_regulacao_html.py` (502→retry→sucesso).

## 5. Adoção no grupo D (documento vinculado)

- [x] 5.1 Substituir o laço de `noticias_vinculo._obter` pelo motor central e marcar o POST `ExibirPDF` como `repetivel=True`; verificar com os testes de documento vinculado cobrindo 5xx e 429.

## 6. Adoção no grupo F (downloads)

- [x] 6.1 Envolver `cvm/pdf.baixar_pdf_cvm` no motor com `repetivel=True`; verificar com `tests/test_infrastructure/test_cvm_pdf.py` (502→retry→PDF válido; 403 sem retry).
- [x] 6.2 Envolver `noticias_aquisicao.baixar_noticia` no motor; verificar com `tests/test_infrastructure/test_regulacao/test_noticias_aquisicao.py`.
- [x] 6.3 Envolver `bdr/client` (detalhe e notícias) e `b3/client` (token, CSV e portfólio) no motor; verificar com `test_bdr.py` e `test_b3_client.py`.
- [x] 6.4 Envolver `emprestimos._baixar` (`repetivel=True`) e `funds_client/noticias` e `releases/client` no motor; verificar com os testes de short interest, notícias e releases.

## 7. Isenções preservadas

- [x] 7.1 Confirmar que os probes de cache condicional (`cvm/downloader._probe_http`, `cvm/datasets._probe_http`, `fundamentus/client.fetch_response`) e o adaptador LLM não usam o motor central; verificar com os testes de cache condicional e do adaptador LLM inalterados e verdes.

## 8. Verificação integrada

- [x] 8.1 Rodar `pytest` (marker padrão) e confirmar a suíte verde, incluindo os novos testes de política.
- [x] 8.2 Rodar `openspec validate politica-erros-http --strict`.
- [x] 8.3 Conferir manualmente que um 403 não gera retry e que um 502/504/520 em download agora é repetido e, se falhar após as tentativas, é registrado com a categoria.
