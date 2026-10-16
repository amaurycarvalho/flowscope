## Why

As ações de atualização do FlowScope — carregar a watchlist, atualizar fundamentos, documentos e notícias, e resumir pendentes — só existem pela interface gráfica. Não há forma de agendá-las externamente (cron, systemd, CI), o que impede manter os caches atualizados sem abrir a GUI. Esta change expõe essas ações pela CLI, mantendo o servidor MCP estritamente somente-leitura, e adiciona uma leitura consultiva da data de referência dos fundamentos. Além disso, a execução headless não deixa rastro: o log em arquivo só é configurado no modo gráfico, então um agendador não tem como auditar o que executou nem com que argumentos.

## What Changes

- Novo grupo de subcomandos CLI de ação (`carregar`, `atualizar`, `resumir`) para agendamento externo:
  - `flowscope carregar watchlist <arquivo>` — valida e persiste a watchlist em `config.json` (`last_tickers` e `last_ticker_file`).
  - `flowscope atualizar fundamentos --data <AAAA-MM-DD>` — atualiza os fundamentos da watchlist carregada (roda a análise de mercado antes, para preservar Preço Típico e fallbacks), grava o histórico e o marcador da última carga.
  - `flowscope atualizar documentos [<ticker>]` — com `<ticker>`, exige `ticker ∈ last_tickers`; sem `<ticker>`, itera a watchlist carregada e atualiza os documentos de todos os tickers.
  - `flowscope atualizar noticias`.
  - `flowscope resumir documentos <ticker>` — lote de pendentes (resumos + guidance de RG).
  - `flowscope resumir noticias` — lote de pendentes.
- Auditoria de chamadas CLI: toda invocação registra no log da aplicação o comando, os argumentos permitidos, o início e o fim, a duração e o código de saída, omitindo segredos e preservando o `stdout`.
- Subcomando `flowscope mcp [--watchlist <arquivo>] [--data <AAAA-MM-DD>]` (com alias `--mcp`): sem parâmetros, apenas lê o cache para montar a árvore; com `--watchlist` e/ou `--data`, executa antes as mesmas etapas de `flowscope carregar watchlist` e `flowscope atualizar fundamentos --data` e só então inicia o servidor MCP, que permanece somente-leitura. A árvore carrega os fundamentos na data de referência resolvida.
- Marcador `last_fundamentals` (`{data, fetched_at}`) em `config.json`, com resolução `marcador → fallback last_date`, escrito pela CLI e pela GUI ao carregar fundamentos.
- Leitura consultiva da data de referência: nó `/fundamentos/data-referencia` na árvore de conhecimento (visível ao Chat AI), operação `data_referencia` no núcleo de navegação, tool MCP `nav_data_referencia` e comando `flowscope nav data-referencia`.
- Núcleo de composição neutro `montar_nucleo()` reusado por GUI e CLI, e extração do núcleo do lote de resumos para a camada de aplicação.
- Segurança de escrita concorrente: escrita atômica com temporário único, lock global de ação na CLI e participação da GUI no mesmo lock nas fases de escrita; as gravações de `config.json` (CLI e GUI) passam a ser atômicas e sob o mesmo lock.

## Capabilities

### New Capabilities

- `cli-acoes-atualizacao`: subcomandos CLI de ação para agendamento externo (carregar watchlist, atualizar fundamentos/documentos/notícias, resumir pendentes de documentos/notícias).
- `cli-audit-logging`: registro auditável de cada invocação da CLI (comando, argumentos permitidos, tempo e desfecho), com segredos omitidos e canal `stdout` preservado.
- `data-referencia-fundamentos`: marcador `last_fundamentals`, resolução com fallback, carga da árvore na data de referência e exposição consultiva (nó da árvore, operação, tool e comando).
- `escrita-concorrente`: escrita atômica segura entre processos, lock global de ação e participação da GUI.

### Modified Capabilities

- `cli-interface`: inclui o subcomando `flowscope nav data-referencia` entre as operações de navegação.
- `mcp-server`: inclui a tool somente-leitura `nav_data_referencia` no catálogo, o subcomando `flowscope mcp` com preparação opcional na inicialização e o escopo de leitura restrito ao servidor durante o atendimento.
- `navegacao-core`: inclui a operação `data_referencia` no conjunto canônico.
- `ticker-list-persistence`: a watchlist DEVE poder ser carregada de um arquivo pela CLI e persistida em `last_tickers` e `last_ticker_file`.

## Impact

- **Código**: `presentation/main.py` (bootstrap de auditoria e despacho do subcomando `mcp`), `presentation/cli.py` (subcomandos, composição, carga date-aware e preparação do `mcp`), `presentation/navegacao.py` (tool), `application/navegacao/core.py` (operação), `application/chat/fundamentos.py` e `application/chat/arvore.py` (nó), `presentation/gui/chat/chat_panel.py` (nó), `presentation/gui/app_wiring.py` (núcleo neutro), `presentation/gui/documentos_job.py`/`resumos_job.py` e mixins de painel (lote headless), `infrastructure/conditional_cache_types.py` (tmp único), `infrastructure/fii/fundamental_history_store.py` (consulta por data de referência), stores JSON (lock), `presentation/gui/app.py` (marcador, lock e escrita atômica de `config.json`).
- **Dados**: `config.json` ganha o bloco `last_fundamentals` e passa a ser gravado de forma atômica sob o lock global; nenhum formato de cache existente muda.
- **Docs**: `README.md` e `docs/misc/mcp.md`.
- **Sem dependências novas**: locking via `fcntl`/`msvcrt` da biblioteca padrão.
- **MCP permanece somente-leitura**: nenhuma tool de ação é exposta; a preparação na inicialização ocorre antes do servidor e reusa os núcleos das ações da CLI.
