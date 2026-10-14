## Why

As ações de atualização do FlowScope — carregar a watchlist, atualizar fundamentos, documentos e notícias, e resumir pendentes — só existem pela interface gráfica. Não há forma de agendá-las externamente (cron, systemd, CI), o que impede manter os caches atualizados sem abrir a GUI. Esta change expõe essas ações pela CLI, mantendo o servidor MCP estritamente somente-leitura, e adiciona uma leitura consultiva da data de referência dos fundamentos.

## What Changes

- Novo grupo de subcomandos CLI de ação (`carregar`, `atualizar`, `resumir`) para agendamento externo:
  - `flowscope carregar watchlist <arquivo>` — valida e persiste a watchlist em `config.json` (`last_tickers`).
  - `flowscope atualizar fundamentos --data <AAAA-MM-DD>` — atualiza os fundamentos da watchlist carregada (roda a análise de mercado antes, para preservar Preço Típico e fallbacks), grava o histórico e o marcador da última carga.
  - `flowscope atualizar documentos <ticker>` — exige `ticker ∈ last_tickers`.
  - `flowscope atualizar noticias`.
  - `flowscope resumir documentos <ticker>` — lote de pendentes (resumos + guidance de RG).
  - `flowscope resumir noticias` — lote de pendentes.
- Marcador `last_fundamentals` (`{data, fetched_at}`) em `config.json`, com resolução `marcador → fallback last_date`, escrito pela CLI e pela GUI ao carregar fundamentos.
- Leitura consultiva da data de referência: nó `/fundamentos/data-referencia` na árvore de conhecimento (visível ao Chat AI), operação `data_referencia` no núcleo de navegação, tool MCP `nav_data_referencia` e comando `flowscope nav data-referencia`.
- Núcleo de composição neutro `montar_nucleo()` reusado por GUI e CLI, e extração do núcleo do lote de resumos para a camada de aplicação.
- Segurança de escrita concorrente: escrita atômica com temporário único, lock global de ação na CLI e participação da GUI no mesmo lock nas fases de escrita.

## Capabilities

### New Capabilities

- `cli-acoes-atualizacao`: subcomandos CLI de ação para agendamento externo (carregar watchlist, atualizar fundamentos/documentos/notícias, resumir pendentes de documentos/notícias).
- `data-referencia-fundamentos`: marcador `last_fundamentals`, resolução com fallback e exposição consultiva (nó da árvore, operação, tool e comando).
- `escrita-concorrente`: escrita atômica segura entre processos, lock global de ação e participação da GUI.

### Modified Capabilities

- `cli-interface`: inclui o subcomando `flowscope nav data-referencia` entre as operações de navegação.
- `mcp-server`: inclui a tool somente-leitura `nav_data_referencia` no catálogo.
- `navegacao-core`: inclui a operação `data_referencia` no conjunto canônico.
- `ticker-list-persistence`: a watchlist DEVE poder ser carregada de um arquivo pela CLI e persistida em `last_tickers`.

## Impact

- **Código**: `presentation/cli.py` (subcomandos e composição), `presentation/navegacao.py` (tool), `application/navegacao/core.py` (operação), `application/chat/fundamentos.py` e `application/chat/arvore.py` (nó), `presentation/gui/chat/chat_panel.py` (nó), `presentation/gui/app_wiring.py` (núcleo neutro), `presentation/gui/documentos_job.py`/`resumos_job.py` e mixins de painel (lote headless), `infrastructure/conditional_cache_types.py` (tmp único), `infrastructure/fii/fundamental_history_store.py` e stores JSON (lock), `presentation/gui/app.py` (marcador e lock).
- **Dados**: `config.json` ganha o bloco `last_fundamentals`; nenhum formato de cache existente muda.
- **Docs**: `README.md` e `docs/misc/mcp.md`.
- **Sem dependências novas**: locking via `fcntl`/`msvcrt` da biblioteca padrão.
- **MCP permanece somente-leitura**: nenhuma tool de ação é exposta.
