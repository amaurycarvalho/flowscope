## 1. Data padrão das atualizações

- [x] 1.1 Alterar `_data_efetiva` em `src/flowscope/presentation/cli_acoes.py` para devolver `date.today()` quando `--data` for omitido, removendo a consulta a `resolver_data_referencia`; atualizar as docstrings de `_data_efetiva` e `atualizar_fundamentos` e a ajuda de `--data`; verificar com teste unitário de `_data_efetiva(None)` e `_data_efetiva(date(...))`.
- [x] 1.2 Adicionar em `tests/test_presentation/test_cli_acoes.py` testes de despacho para `atualizar fundamentos`, `atualizar documentos` e `atualizar noticias` com `--data` omitido (ignorando `last_fundamentals`/`last_date`) e com `--data` explícito; executar `pytest tests/test_presentation/test_cli_acoes.py`.

## 2. Resumos de documentos de toda a watchlist

- [x] 2.1 Tornar o ticker de `resumir documentos` opcional no parser (`nargs="?"`, default `None`, ajuda indicando que omitido processa toda a watchlist) e ajustar `_despachar_resumir`; verificar com testes de `build_parser().parse_args(...)` com e sem ticker e com teste de que o despacho repassa `None`.
- [x] 2.2 Adicionar ao `_ContextoHeadless` o acúmulo dos erros recebidos em `erro()` e criar um helper por ticker que devolva `(desfecho, falhou)`, usando `_resumo_json` no sucesso e `{"erro": {"motivo": "falha_resumo", "detalhe": ...}}` quando houver exceção ou erro registrado; verificar com teste unitário do helper nos dois desfechos.
- [x] 2.3 Implementar `resumir_documentos(ticker: str | None)` sem ticker: validar `last_tickers`, montar o núcleo e checar a LLM uma única vez, normalizar/deduplicar tickers, iterar, capturar falha por ticker sem abortar o lote e devolver `{"resultados": {...}, "falha": <bool>}` com `falha` sempre presente; verificar com testes de lote completo, falha parcial, watchlist ausente, LLM ausente e de que o núcleo/LLM são acionados uma vez.
- [x] 2.4 Preservar o formato agregado de `resumir documentos <ticker>` (`pendentes`, `sem_texto`, `nao_conclusivos`, `apontadores`, sem `resultados`); verificar com teste de saída do modo com ticker.
- [x] 2.5 Garantir que o lote com falha encerre com código 1 via `executar_acao`; verificar com teste que captura `SystemExit` e confere o JSON com `falha: true`.

## 3. Documentação

- [x] 3.1 Atualizar a seção 8 de `docs/misc/mcp.md`: tabela de etapas com `resumir-documentos` = `flowscope resumir documentos`, entrypoint sem laço e sem checagem do arquivo de watchlist, `FLOWSCOPE_REFERENCE_DATE` opcional com `--data` condicional, exemplos da seção 8.5 sem `--data "$(date +%F)"` e com `resumir documentos` sem ticker, e tabela 8.6 com a variável opcional; verificar o snippet com `sh -n` e conferir os comandos com `flowscope --help`.
- [x] 3.2 Atualizar o `README.md`: comentar que as ações `atualizar ...` sem `--data` usam a data de hoje, adicionar `resumir documentos` sem ticker e mencionar que a inicialização do container pode executar as etapas opcionais; verificar os links e a consistência com `docs/misc/mcp.md`.
- [x] 3.3 Registrar em `docs/misc/mcp.md` que o default de hoje vale para os subcomandos `atualizar` (o `flowscope mcp` sem `--data` continua sem atualizar), que dia não útil grava a data de hoje no marcador e que `FLOWSCOPE_INIT_UPDATES=all` exige LLM e pode atrasar o handshake do MCP; verificar a leitura das seções 7 e 8.

## 4. Verificação da change

- [x] 4.1 Executar `make lint`, `make complexity` e `pytest tests/test_presentation/test_cli_acoes.py`; verificar que passam sem novas violações.
