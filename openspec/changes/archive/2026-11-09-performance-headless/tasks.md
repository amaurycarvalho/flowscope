# Tasks

## 1. Snapshot e payload compartilhado

- [x] 1.1 Extrair a montagem do payload/snapshot para a camada de aplicação (`application/performance`), com versão de schema, `ref_date`, período, amostragem, base, `cached_at`, benchmarks e resultados; verificar com testes unitários em `tests/test_application/test_performance_snapshot.py`
- [x] 1.2 Implementar leitura e escrita atômica do snapshot `~/.cache/flowscope/performance/latest.json` em `infrastructure/performance`, tolerando ausência, JSON inválido, resultado não-dicionário e schema divergente; verificar com testes em `tests/test_infrastructure/test_performance_snapshot_store.py`
- [x] 1.3 Fazer o job de Performance da GUI usar o mesmo construtor e escritor de snapshot; verificar em `tests/test_presentation/test_controller_performance.py` que `latest.json` é gravado com o contexto da carga

## 2. Atualização headless

- [x] 2.1 Implementar `atualizar_performance` em `presentation/cli_acoes.py`: resolver a data, carregar watchlist, obter `daily_data`/classificação, executar `AnalyzePerformanceUseCase`, gravar cache e snapshot e isolar falhas por benchmark; verificar com testes de sucesso, watchlist ausente, nenhum elegível e índice indisponível em `tests/test_presentation/test_cli_acoes.py`
- [x] 2.2 Registrar o subcomando `flowscope atualizar performance [--data]` no parser e no despacho; verificar com `flowscope atualizar performance --help` e com a saída JSON estruturada nos testes de CLI
- [x] 2.3 Atualizar `_preparar_mcp` para executar `atualizar performance` logo após `atualizar fundamentos`, reutilizando a data resolvida e a watchlist resultante; verificar em `tests/test_presentation/test_mcp.py` que a ordem é respeitada e que falha recuperável não aborta o servidor
- [x] 2.4 Garantir a política de falha: erros duros com código 1 e falhas recuperáveis com `WARNING` e conclusão; verificar com testes de lock indisponível e falha de escrita do snapshot

## 3. Navegação e manifesto

- [x] 3.1 Implementar `FontePerformance` em `application/chat`, montando `/performance`, `/performance/configuracao`, `/performance/benchmarks/<benchmark>/resumo` e `/performance/benchmarks/<benchmark>/tickers/<ticker>` somente a partir do snapshot; verificar com testes de caminhos, ticker, resumo e evento suspeito em `tests/test_application/test_chat_performance.py`
- [x] 3.2 Integrar a fonte em `montar_core_navegacao` e em `ChatPanel.montar_arvore`; verificar com `tests/test_presentation/test_cli_nav.py` e com um teste de integração do chat que `/performance` aparece quando há snapshot e é omitido quando não há
- [x] 3.3 Anunciar `/performance` no manifesto (descrição, mapa de caminhos, playbook e, se aplicável, lista de benchmarks) apenas quando o ramo existir; verificar em `tests/test_application/test_chat_manifesto.py` os casos presente, ausente, teto de tokens e ausência de resultados por ticker nos metadados

## 4. Exportação CLI

- [x] 4.1 Implementar `flowscope exportar performance --formato <csv|json> [--benchmark ...] [--saida ...]` em `presentation/cli_consultas.py`, lendo somente o snapshot e emitindo CSV com `;` ou JSON estruturado; verificar com testes de CSV, JSON e filtro de benchmark
- [x] 4.2 Tratar snapshot ausente (`performance_ausente`), benchmark ausente (`benchmark_ausente`), formato inválido e falha de escrita; verificar com testes em `tests/test_presentation/test_cli_consultas_performance.py` e com a execução manual dos comandos de erro

## 5. Logging e edge cases

- [x] 5.1 Adicionar logs `INFO` de ciclo de vida e `WARNING` com contexto para índice indisponível, proventos, ticker sem preço, observações insuficientes, snapshot corrompido/divergente/defasado, falha de escrita e exportação sem snapshot; verificar com `caplog` nos testes de atualização, infraestrutura e exportação
- [x] 5.2 Evitar `WARNING` repetido por ausência de snapshot na montagem da árvore por mensagem do chat, usando `DEBUG` ou uma vez por assinatura; verificar com teste de log em `tests/test_presentation/test_chat_integration.py` ou equivalente
- [x] 5.3 Garantir que a preparação do MCP e a navegação não escrevem logs em `stdout`; verificar em `tests/test_presentation/test_mcp.py` que `stdout` contém apenas JSON-RPC e que `stderr` recebe o progresso

## 6. Documentação e ajuda

- [x] 6.1 Atualizar a documentação de comandos (README e docs aplicáveis) com `atualizar performance`, `exportar performance`, a preparação do MCP e a limitação de período/amostragem padrão; verificar que os comandos documentados executam como escrito
- [x] 6.2 Atualizar os textos de ajuda/`--help` dos novos subcomandos e do `flowscope mcp`; verificar com `flowscope atualizar performance --help`, `flowscope exportar performance --help` e `flowscope mcp --help`

## 7. Verificação da mudança

- [x] 7.1 Executar `make lint` e verificar que não há erros novos
- [x] 7.2 Executar `make complexity` e verificar que não há regressões
- [x] 7.3 Executar os testes impactados: `pytest tests/test_application/test_performance_snapshot.py tests/test_application/test_performance_use_case.py tests/test_application/test_chat_performance.py tests/test_application/test_chat_manifesto.py tests/test_infrastructure/test_performance_snapshot_store.py tests/test_presentation/test_cli_acoes.py tests/test_presentation/test_cli_consultas_performance.py tests/test_presentation/test_cli_nav.py tests/test_presentation/test_mcp.py tests/test_presentation/test_controller_performance.py tests/test_presentation/test_chat_integration.py` e verificar que passam
- [x] 7.4 Fazer um smoke test headless com cache temporário: `atualizar performance`, `nav listar /performance`, `nav obter /performance/benchmarks/<benchmark>/tickers/<ticker>` e `exportar performance --formato json`; verificar que todas as saídas são JSON e refletem o snapshot
- [x] 7.5 Fazer um smoke test do MCP: iniciar `flowscope mcp --watchlist <arquivo> --data <data>` e verificar que `tools/call` de `nav_listar` em `/performance` devolve o ramo e que `stdout` permanece limpo

## Workflow follow-up

- Verificação ampla opcional (manual, usuário): executar `make test` e/ou `make quality-gate` antes do archive, conforme a convenção do projeto.
- Arquivar a change após a revisão e a verificação exigidas pelo projeto.
