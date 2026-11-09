# Proposal

## Why

Hoje a Performance só é calculada pela interface gráfica e o resultado fica em um cache com nome hasheado, sem contexto de período, amostragem ou data. Chat AI, `flowscope nav` e servidor MCP não conseguem navegar esses resultados, e não há exportação pela CLI. Um usuário que opera sem GUI precisa abrir o aplicativo apenas para calcular a Performance.

Esta mudança permite atualizar, navegar e exportar a Performance sem abrir a GUI, mantendo a preparação opcional do MCP como o caminho para iniciar o servidor com os dados já atualizados.

## What Changes

- Novo subcomando `flowscope atualizar performance [--data <AAAA-MM-DD>]`, autossuficiente, sob o lock global de ação. Ele calcula a Performance da watchlist com a configuração headless padrão (30 dias, Fibonacci), grava o cache pré-calculado existente e um snapshot estável e auto-descritivo em `~/.cache/flowscope/performance/latest.json`.
- A preparação do MCP (`flowscope mcp --watchlist ... --data ...`) passa a executar `atualizar performance` logo após `atualizar fundamentos`, reutilizando a watchlist e a data de referência resolvida. Falha suave da Performance não aborta a inicialização: o servidor sobe e a árvore expõe o estado indisponível.
- Novo ramo navegável `/performance` na árvore de conhecimento, montado exclusivamente a partir do snapshot local, com `configuracao` (`ref_date`, período, amostragem, base), `benchmarks/<benchmark>/resumo` e `benchmarks/<benchmark>/tickers/<ticker>`.
- O manifesto anuncia `/performance` apenas quando o ramo existe, com os caminhos canônicos e uma linha no playbook de intenção. O conteúdo pesado não entra no manifesto.
- Novo subcomando `flowscope exportar performance --formato <csv|json> [--benchmark <IFIX|IBOV|IDIV>] [--saida <ARQUIVO>]`, somente leitura do snapshot, sem recalcular e sem rede.
- Nenhuma tool MCP nova: as tools `nav_*` já navegam o ramo. Uma tool de exportação dedicada fica fora desta mudança.
- Logs `INFO`/`WARNING` cobrem preparação, classificação, cache/snapshot, série do índice, proventos, exportação e edge cases. No modo MCP, nada é escrito em `stdout`.
- O job de Performance da GUI usa o mesmo escritor de snapshot, de modo que GUI, chat, `flowscope nav` e MCP compartilhem a mesma visão do resultado mais recente.

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: a mudança estende comportamentos existentes. -->

### Modified Capabilities

- `performance-index-panel`: snapshot headless auto-descritivo, atualização via CLI e consistência entre cálculo da GUI e do headless.
- `cli-acoes-atualizacao`: novo subcomando de ação `atualizar performance`.
- `cli-interface`: novo subcomando de leitura `exportar performance`.
- `mcp-server`: preparação opcional chama `atualizar performance` após os fundamentos e expõe o ramo pela navegação.
- `llm-chat-tree`: ramo `/performance` e anúncio dos caminhos no manifesto/playbook.
- `logging`: registro de problemas recuperáveis da Performance headless, da leitura do snapshot e da exportação.

## Impact

- `application/performance/`: montagem/serialização do snapshot e reuso do payload pela GUI e pelo headless.
- `application/chat/`: nova fonte de ramo `FontePerformance`, alimentada pelo snapshot já carregado.
- `infrastructure/performance/`: leitura/escrita atômica do snapshot, tolerante a corrupção e schema divergente.
- `presentation/cli_acoes.py`: novo subcomando `atualizar performance`.
- `presentation/cli_consultas.py`: novo subcomando `exportar performance`.
- `presentation/cli.py`: preparação do MCP em ordem fundamentos → performance e montagem da árvore com a data resolvida.
- `presentation/gui/controller_performance.py`: compartilhar o escritor de snapshot.
- `application/chat/manifesto.py`: descrição, mapa de caminhos e playbook do ramo `/performance`.
- Cache novo `~/.cache/flowscope/performance/latest.json`; o cache hasheado existente continua válido.
- Testes de aplicação, infraestrutura, apresentação, CLI, MCP e árvore de conhecimento.
- Nenhuma dependência externa nova; a série do índice e os proventos reusam os provedores existentes.
