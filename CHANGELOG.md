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

### [performance-vs-indice](openspec/changes/performance-vs-indice) Sub-aba "Performance" compara o retorno dos ativos com o seu índice de referência, com ingestão da série diária de IBOV, IDIV e IFIX, cache por resultado e aviso de evento societário suspeito

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
