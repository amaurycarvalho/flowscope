# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui o placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional

### [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões

### [llm-chat-rag](openspec/changes/llm-chat-rag) Recuperação vetorial como evolução da `llm-chat`, com VectorStore SQLite, embeddings e indexação de documentos consultada pela aba "Chat AI"

### [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado, com gauge de concentração, card informativo e timeline AFT

## [1.8.0] - 2026-11-09

### [performance-headless](openspec/changes/archive/2026-11-09-performance-headless) Performance calculada, navegada e exportada sem GUI, com snapshot auto-descritivo compartilhado por CLI, chat, `flowscope nav` e MCP

#### Added

- Novo subcomando `flowscope atualizar performance [--data <AAAA-MM-DD>]`, autossuficiente, sob o lock global de ação. Ele calcula a Performance da watchlist com a configuração headless padrão (30 dias, Fibonacci), grava o cache pré-calculado existente e um snapshot estável e auto-descritivo em `~/.cache/flowscope/performance/latest.json`.
- Novo ramo navegável `/performance` na árvore de conhecimento, montado exclusivamente a partir do snapshot local, com `configuracao` (`ref_date`, período, amostragem, base), `benchmarks/<benchmark>/resumo` e `benchmarks/<benchmark>/tickers/<ticker>`.
- Novo subcomando `flowscope exportar performance --formato <csv|json> [--benchmark <IFIX|IBOV|IDIV>] [--saida <ARQUIVO>]`, somente leitura do snapshot, sem recalcular e sem rede.

#### Changed

- A preparação do MCP (`flowscope mcp --watchlist ... --data ...`) passa a executar `atualizar performance` logo após `atualizar fundamentos`, reutilizando a watchlist e a data de referência resolvida. Falha suave da Performance não aborta a inicialização: o servidor sobe e a árvore expõe o estado indisponível.
- O manifesto anuncia `/performance` apenas quando o ramo existe, com os caminhos canônicos e uma linha no playbook de intenção. O conteúdo pesado não entra no manifesto.
- Logs `INFO`/`WARNING` cobrem preparação, classificação, cache/snapshot, série do índice, proventos, exportação e edge cases. No modo MCP, nada é escrito em `stdout`.
- O job de Performance da GUI usa o mesmo escritor de snapshot, de modo que GUI, chat, `flowscope nav` e MCP compartilhem a mesma visão do resultado mais recente.

### [performance-vs-indice](openspec/changes/archive/2026-11-09-performance-vs-indice) Sub-aba "Performance" compara o retorno dos ativos com o seu índice de referência, com ingestão da série diária de IBOV, IDIV e IFIX, cache por resultado e aviso de evento societário suspeito

#### Added

- Adicionar a sub-aba "Performance" na "Análise Geral", entre "Dominância do Pregão" e "Rede de Correlação", com barras de excesso de retorno em pontos percentuais e o zero representando o índice.
- Adicionar o combobox de benchmark (IFIX para FIIs; IBOV e IDIV para ações), com default pelo primeiro ticker e elegibilidade restrita ao tipo correspondente; ETF, BDR e desconhecido ficam fora.
- Calcular retorno de preço (IBOV) e retorno total (IFIX/IDIV), com proventos reinvestidos na primeira observação alinhada igual ou posterior à data ex derivada da data-com.
- Ingerir automaticamente a série diária de fechamento dos índices pelo endpoint B3 `indexStatisticsProxy/IndexCall/GetPortfolioDay`, com cache por índice e ano, TTL de 1 dia no ano corrente e anos anteriores imutáveis.
- Manter cache pré-calculado dos resultados por schema, índice, data de referência, período, amostragem, conjunto de tickers e base de retorno.
- Sinalizar no hover quando um salto de preço for compatível com split, grupamento ou bonificação, sem alterar o retorno calculado.
- Adicionar testes de cliente, parsing, repositório, cache, aplicação, controlador e painel, além da documentação em `docs/misc/datasources.md` e `docs/misc/panels.md`.

#### Changed

- Reexecutar o job de performance após a carga principal e quando a análise fundamentalista atualizar a classificação dos tickers, gravando `_performance_data` sem tocar em `_current_data`.
- Reutilizar a `ToolbarBR` do VWAP, com "Copiar Gráfico", e respeitar os combos globais de período e amostragem, recalculando quando eles mudam.
- Registrar em log o ciclo do job de performance e os edge cases: agendamento, cache reutilizado/inválido/falha de escrita, benchmarks calculados, tickers fora por tipo, tickers sem preço, observações insuficientes, índice indisponível, resposta vazia/JSON inválido/série vazia, dia/valor/data inválidos no parser, falha de proventos, falha isolada de benchmark e excesso inválido no painel.
- Registrar no log o cancelamento de jobs do gerenciador de background, com grupo e identificador, e o pedido de interrupção do usuário.

#### Fixed

- Reconhecer FIIs fora da taxonomia determinística — como o `TVRI11` — pela classificação do Fundamentus (`classificacao_exibicao`), para que apareçam corretamente na sub-aba Performance sob o IFIX.
- Não exibir "Processamento interrompido" quando um job é substituído por uma submissão mais nova (`LATEST_WINS`), incluindo a segunda execução de performance disparada após a análise fundamentalista; a substituição e o cancelamento continuam registrados no log.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.8.0...HEAD
[1.8.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.8.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
