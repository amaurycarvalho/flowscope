# Changelog Archive

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [0.4.0] — 2026-07-01

### [orientation-add-question-field](openspec/changes/archive/2026-07-01-orientation-add-question-field) Pergunta-guia adicionada ao conteúdo de orientação de cada sub-aba

#### Changed
- Conteúdo do OrientationPanel passa a incluir "Responde a pergunta" entre Objetivo e Indicadores envolvidos
- Ordem dos campos: **Objetivo → Responde a pergunta → Indicadores envolvidos → Como interpretar**

### [orientation-richtext-formatting](openspec/changes/archive/2026-07-01-orientation-richtext-formatting) Formatação rica nativa (negrito/itálico) no OrientationPanel via tags tk.Text

#### Added
- Formatação rica: cabeçalhos de seção em **negrito** e perguntas em itálico via tags nativas `tk.Text`
- Configuração das tags `"bold"` (TkDefaultFont 9 bold) e `"italic"` (TkDefaultFont 9 italic)

#### Changed
- `set_content` alterado de `(title: str, body: str)` para `(title: str, body: list[tuple[str, str]])`
- Todas as 9 sub-abas refatoradas para usar lista de tuplas `(segmento, tag)`
- `_on_quadrant_summary` atualizado para anexar resumo como tupla à lista body

### [unify-price-amplitude-chart](openspec/changes/archive/2026-07-01-unify-price-amplitude-chart) Três métricas correlatas unificadas num único axes com camadas visuais de posição, amplitude e eficiência

#### Changed
- Price Range Timeline, Range % Histórico e Eficiência Diária unificados num único axes matplotlib com 3 camadas visuais por row (eficiência como barra de fundo, timeline como scatter, amplitude como tamanho do marcador)
- Tooltip expandida com Amplitude Relativa (Range %)
- Nomenclatura atualizada: título "Amplitude de Preço — {ticker}", "Range %" → "Amplitude Relativa"
- Texto de orientação atualizado com as três perguntas "Onde / Quanto / Se andou com convicção" e significado interpretativo das classificações
- Setas de trajetória (ax.arrow) substituídas por linhas (ax.plot) — eliminou artefatos visuais de traçado extra
- Labels "← Vendedores" e "Compradores →" adicionados abaixo do gauge CLV
- Título do CLV alterado para "CLV (data mais recente)"
- Labels "Min:" e "Max:" separados e posicionados abaixo de 0% e 100%
- Altura do gauge CLV reduzida em ~20%

#### Removed
- Sub-gráfico "Range % Histórico" — substituído pelo tamanho do marcador de fechamento (●)
- Sub-gráfico "Eficiência Diária" — substituído por barra horizontal de fundo por row (eficiência visível em todos os dias, não apenas no último)

## [0.3.1] — 2026-06-29

### [statusbar-progress-indicator](openspec/changes/archive/2026-06-29-statusbar-progress-indicator) Barra de progresso determinate na statusbar com fases ponderadas, cache e falhas; ProgressReporter injetado nas camadas application/infrastructure

#### Added
- **Barra de progresso determinate** (`ttk.Progressbar`) com label textual lado a lado na statusbar, substituindo o texto animado cego
- **ProgressReporter**: classe com sistema de fases ponderadas, throttling de updates e contagem de falhas
- **Progresso em múltiplas fases**: download de dados históricos (7 datas Fibonacci), processamento de indicadores (DAG engine) e carregamento de portfólio
- **Cache refletido no progresso**: datas em cache são avançadas imediatamente sem delay perceptível
- **Falhas contabilizadas**: datas com erro são contadas no progresso com label indicando "N/M (X falhas)"
- **Portfolio loading textual**: exibe "Baixando portfólio IBOV..." como etapa da progressão
- **Callback de progresso** injetado via `UseCase` → `Repository` → `Client` → `Engine`, permitindo reporte em todas as camadas

#### Changed
- **Statusbar**: de `tk.Label` com texto animado para `tk.Frame` contendo `tk.Label` + `ttk.Progressbar` determinate
- **`_animate_loading()`**: removido em favor do sistema de progresso via `ProgressReporter`

## [0.3.0] — 2026-06-29

### [dominancia-pregao-stem-mfv](openspec/changes/archive/2026-06-29-dominancia-pregao-stem-mfv) Stem horizontal substitui círculo do MFV nos gráficos de Dominância; botões Mover/Ampliar da toolbar tornam-se mutuamente exclusivos

#### Changed
- **DominanceRankingChart**: círculo de MFV substituído por stem horizontal que parte de x=0 com comprimento proporcional ao MFV; label do ticker reposicionado após o stem; "Vendedores"/"Compradores" movidos para y=-0.08
- **DominanceTimelineChart**: mesma substituição círculo→stem (stem_max_data=0.15); "Vendedores"/"Compradores" movidos para y=-0.10
- **ToolbarBR**: botões Mover e Ampliar tornam-se mutuamente exclusivos (apenas um ativo por vez); Início desmarca ambos
- **OrientationPanel**: textos de orientação atualizados de "círculo" para "traço horizontal"

### [painel-dominancia-pregao](openspec/changes/archive/2026-06-29-painel-dominancia-pregao) Painéis de Dominância do Pregão (ranking) e Evolução da Dominância (timeline) com barras divergentes, classificadores e indicadores de fluxo

#### Added
- **Painel "Dominância do Pregão" na aba Análise Geral**: ranking visual de todos os tickers usando CLV do último pregão, com barras horizontais divergentes, classificação qualitativa e indicador de Money Flow Volume acumulado.
- **Painel "Evolução da Dominância" na aba Análise do Ticker**: gráfico temporal de barras divergentes (um dia por barra) com overlay de Daily Efficiency e indicador de Money Flow diário.
- **Duas novas strategies no engine**: `daily_money_flow` (MFV por dia, não acumulado) e `dominance_score` (CLV × Daily Efficiency).
- **Módulo de classificadores** (`domain/strategies/classifiers/`): `classify_dominance(clv)` e `classify_conviction(efficiency)` com tipagem forte e saída textual + score numérico.

#### Changed
- **Aba "Dominância do Pregão" renomeada para "Amplitude de Preço"** no notebook de Análise do Ticker (conteúdo atual são indicadores de amplitude).
- **Painel de orientação**: textos de ajuda para os novos painéis.
- **`_format_all_indicators`**: incluído `dominance_score` na listagem exibida.

### [multi-ticker-selector](openspec/changes/archive/2026-06-29-multi-ticker-selector) Modo visualização com Listbox de seleção múltipla, lazy refresh híbrido e remoção dos comboboxes da Análise Geral

#### Added
- **Modo visualização com Listbox(EXTENDED)**: toggle "Editar lista de tickers" alterna entre Text (edição) e Listbox (seleção múltipla via Ctrl+Click e Shift+Click)
- **Botões "Selecionar Todos" e "Desmarcar Todos"** na barra superior, ao lado direito do toggle, visíveis apenas no modo visualização
- **Preservação de seleção ao transitar entre modos**: tickers existentes mantêm marcação; novos entram marcados; remoções desaparecem; se lista mudou, recarga de dados é disparada
- **Separadores verticais** entre Salvar/Editar e entre grupo de seleção/índices
- **Lazy refresh híbrido**: aba ativa renderiza imediatamente após carga/filtro; demais abas renderizam apenas ao serem selecionadas

#### Changed
- `get_tickers()` retorna apenas tickers selecionados no modo visualização (todos no modo edição)
- `_ensure_tickers()` usa `get_all_listbox_tickers()` — carga de dados usa todos os tickers, independente da seleção
- `_on_load_data()` não substitui `self._tickers` nem chama `set_tickers()` (preserva lista original do usuário)
- Regra de quiver mantida no painel Quadrantes: setas exibidas quando apenas 1 ticker selecionado

#### Removed
- **Botão "Filtrar"** removido (seleção no Listbox já funciona como filtro)
- **Comboboxes de ticker da Análise Geral** (VWAP, Quadrantes, Dominância) removidos; seleção via Listbox controla todos os gráficos

### [refactor-analise-ticker-ui](openspec/changes/archive/2026-06-29-refactor-analise-ticker-ui) Combobox de seleção substituído por TickerList; painel Evolução da Dominância simplificado sem resumo lateral e linha de eficiência

#### Added
- **Labels "Compradores/Vendedores"** no QuadrantChart, abaixo do eixo CLV

#### Changed
- **Sub-abas reordenadas**: "Evolução da Dominância" como primeira aba da "Análise do Ticker", antes de "Amplitude de Preço"
- **DominanceTimelineChart redesenhado**: painel lateral de resumo removido; linha de eficiência (twiny) removida; informações movidas para o tooltip de cada barra (Data, Dominância, Convicção, MFV); percentuais adicionados nos labels "Compradores" e "Vendedores"
- **Spec `ticker-analysis` atualizada**: mecânica de seleção sem combobox
- **Spec `dominance-timeline-panel` atualizada**: design sem painel lateral, sem linha de eficiência, tooltip expandido

#### Removed
- **Combobox de seleção de ticker** na aba "Análise do Ticker"; ticker analisado agora deriva da TickerList (primeiro selecionado, ou primeiro da lista, ou "Selecione um ticker" se vazia)

#### Fixed
- **Hover nos charts de barra**: tooltip detecta mouse em qualquer ponto da barra (entre 0 e CLV), não apenas no endpoint
- **Zorder do tooltip**: tooltip renderiza acima dos stems MFV em ambos os charts de barra
- **Ordenação das datas**: DominanceTimelineChart ordena mais antiga no topo, mais recente na base
- **TickerList**: `exportselection=False` evita que seleção externa (X11 PRIMARY) limpe seleção interna
- **Lazy refresh**: `_on_tab_changed()` sempre atualiza a aba atual ao navegar, não apenas quando `_charts_dirty` está True

## [0.2.1] — 2026-06-28

### [quadrantes-ticker-sync](openspec/changes/archive/2026-06-28-quadrantes-ticker-sync) Sincronização de comboboxes e visibilidade condicional de setas nos quadrantes

#### Added
- **Sincronização bidirecional de comboboxes:** combobox do Quadrantes e da Análise do Ticker sincronizam valores entre si. "Todos" no Quadrantes limpa o combobox da Análise do Ticker.

#### Changed
- **Quadrantes — setas (quiver):** ocultas quando o ticker está como "Todos"; exibidas apenas para o ticker selecionado.
- **`QuadrantChart.update()`:** adicionado parâmetro `show_arrows` para controle explícito das setas.

## [0.2.0] — 2026-06-28

### [index-portfolio-buttons](openspec/changes/archive/2026-06-28-index-portfolio-buttons) Botões para IBOV, IDIV e IFIX com cliente B3 genérico e parser reutilizável

#### Added

- Botões "IBOV", "IDIV" e "IFIX" no `TickerList` (fileira abaixo dos botões existentes)

#### Changed

- `B3Client.fetch_idiv_portfolio()` generalizado para `fetch_portfolio(index: str)` que aceita qualquer código de índice
- `parse_idiv_csv()` generalizado para `parse_index_csv()` que funciona para qualquer índice
- `B3DataRepository.get_idiv_tickers()` substituído por `get_index_tickers(index: str)`
- Lógica de autopreenchimento extraída para `_fill_with_index("IDIV")` e reusada em `_ensure_tickers()` e `_on_ticker_edit()`

#### Removed

- `fetch_idiv_portfolio()` e `parse_idiv_csv()` (substituídos)

### [quadrant-chart-panel](openspec/changes/archive/2026-06-28-quadrant-chart-panel) Painel Quadrantes com CLV × VWAP Distance, quiver de trajetória e resumo automático

#### Added

- **Novo indicador `vwap_distance`**: derivado do VWAP, calculado como `(last_price - avg_price) / avg_price` por ticker-por-data
- **Painel "Quadrantes"**: bubble chart (CLV × VWAP Distance) com quiver de trajetória temporal, colormap RdYlGn e bolhas dimensionadas por `fin_instr_qty`
- **Resumo textual automático**: análise da distribuição das bolhas entre os quadrantes
- **Seletor de ticker por chart**: Combobox nos gráficos VWAP e Quadrantes (opção "Todos")
- **Atalho Ctrl+A**: selecionar todos os filtros no TickerList

#### Changed

- **Documentação**: `panels.md` e `indicators.md` atualizados (descrição do Quadrantes e VWAP Distance)
- **Título da janela**: removida alteração ao carregar dados (título fixo "FlowScope v0.2.0")

## [0.1.0] — 2026-06-28

### Added

- **Estrutura do projeto**: Clean Architecture (domain, application, infrastructure, presentation), pyproject.toml, Makefile, flowscope.spec para PyInstaller
- **Ingestão de dados B3**: Download de arquivos TradeInformationConsolidated via API two-step da B3, parser de CSV com schema definido, janela temporal com offsets de Fibonacci (d-1, d-2, d-3, d-5, d-8, d-13, d-21) e ajuste para dias úteis, cache local em `~/.cache/flowscope/`
- **Indicadores de fluxo**: Cálculo de Cumulative Volume Delta (CVD), Volume Weighted Average Price (VWAP) e Volume Profile por ticker, seleção automática dos 15 tickers com maior volume financeiro
- **Interface gráfica (Tkinter)**: Janela principal com seleção de data (tkcalendar), gráficos matplotlib (histogramas VWAP/CVD, scatter plot VWAP×CVD com setas temporais), campo multilinha de seleção de tickers com load/save .txt, botões de cópia para clipboard
- **Interface CLI**: argparse com flags `--gui`, `--tickers`, `--vwap`, `--cvd`, `--version`, `--create-shortcut`
- **Exportação para clipboard**: Cópia de dados CSV (pyxclip + fallback Tkinter) e cópia de gráfico como imagem PNG (xclip/Linux, win32clipboard/Windows, osascript/macOS)
- **Atalho desktop**: Geração de `.desktop` no Linux via `--create-shortcut`
- **Cache com TTL**: Método `get_or_fetch()` no CacheManager com suporte a TTL (usado para cache do portfólio IDIV)
- **Download automático do IDIV**: Novo método `fetch_idiv_portfolio()` no B3Client que baixa a carteira do IDIV (base64 → decode Latin-1 → parse) via endpoint da B3, com cache de 7 dias
- **Filtro CASH no parser**: Parâmetro `segment_filter="CASH"` em `parse_csv()` — linhas de outros segmentos (BMF, FUTURE) são ignoradas durante o parsing
- **Preenchimento automático do filtro**: Quando o campo de tickers está vazio e o usuário clica em "Carregar" ou "Filtrar", o sistema busca automaticamente a carteira IDIV e a usa como filtro padrão

### Changed

- **UI/UX — Proteção de carga**: Controles desabilitados durante carregamento, cursor "watch", indicador animado com pontos (`Carregando.` → `Carregando..` → `Carregando...`)
- **UI/UX — Feedback visual**: Statusbar com ícones Unicode (✓ ⏳ ⚠ ℹ), mensagens temporárias com auto-limpeza (2.5s), confirmação em ações de cópia
- **UI/UX — Atalhos de teclado**: Enter aciona "Carregar", Ctrl+Shift+C copia dados, F5 recarrega
- **UI/UX — Tooltips**: Em todos os controles interativos (botões, radio buttons, campos)
- **UI/UX — Contagem de tickers**: Label "Tickers (N)" e "Exibindo M de N ativos"
- **UI/UX — Layout**: Padding consistente (PAD_SMALL=4, PAD=8, PAD_LARGE=12), LabelFrame em "Visualização" e "Exportação", separador entre botões
- **UI/UX — Título dinâmico**: Janela exibe "FlowScope — YYYY-MM-DD — N ativos"
- **UI/UX — Menu de contexto**: Botão direito no campo de tickers com Copiar, Remover, Selecionar todos, Limpar seleção
- **UI/UX — Estado vazio**: Mensagem "Nenhum ticker corresponde ao filtro." quando filtro remove todos ativos
- **UI/UX — Preferências persistentes**: Geometria da janela, posição do sash, última data e último gráfico salvos em `~/.flowscope/config.json`
- **Filtro de tickers**: Alterado de automático (ao digitar) para manual via botão "Filtrar"
- **Barra de status**: Movida para abaixo dos botões de ação
- **Exportação CSV**: Colunas de VWAP/CVD diários adicionadas ao output (uma coluna por data da janela)
- **CLI export**: Flag `--tickers` agora filtra corretamente nas exportações `--vwap` e `--cvd`
- **Scatter plot**: Setas temporais (quiver) conectando posição d-1 → d de cada ticker implementadas
- **Ícone da aplicação**: Carregado na barra de título/tarefa (`.png` Linux, `.ico` Windows)

### Fixed

- **Especificações vs implementação**: Alinhamento de docs — descrição da API B3 corrigida de POST para GET, datas Fibonacci no spec corrigidas, fallback Tkinter documentado, `requests>=2.28` adicionado ao `requirements.txt`, seção vazia "Interface desktop" removida do README
- **Exit code do `--create-shortcut`**: Agora retorna 0 (sucesso) em plataformas não-Linux em vez de 1
- **Auto-refresh após load de tickers**: Gráficos atualizados ao carregar tickers de arquivo `.txt`

### Removed

- Filtro automático ao digitar no campo de tickers (substituído por botão "Filtrar" manual)

### [chart-interactivity](openspec/changes/archive/2026-06-27-chart-interactivity) Toolbox com zoom/pan/reset/save, hover tooltips com coordenadas X/Y e botão de navegação rápida Hoje

#### Added

- **Botão "Hoje"**: Resetar DateEntry para a data atual com um clique
- **Toolbox com zoom/pan/reset/save**: NavigationToolbar2Tk em cada chart com labels em português
- **Hover tooltip no scatter plot**: Ticker, VWAP, CVD e volume ao passar o mouse
- **Hover tooltip no CVD histogram**: Valor exato do CVD por barra
- **Hover tooltip no VWAP histogram**: Faixa de preço e volume do bucket

### [vwap-enhancement](openspec/changes/archive/2026-06-27-vwap-enhancement) VWAP recalculado com peso por quantidade de instrumentos e gráfico substituído por violin plot com perfil de volume

#### Changed

- **BREAKING**: VWAP geral calculado como Σ(TradAvrgPric × FinInstrmQty) / Σ(FinInstrmQty) — peso por quantidade de instrumentos, não por volume financeiro
- **VWAP Histogram**: Substituído por violin plot horizontal com perfil de volume, errorbar (VWAP, MinPric, MaxPric) e scatter (LastPric da data mais recente)
- **AnalyzeTickersUseCase**: Incluídos dados diários adicionais (FinInstrmQty, MinPric, MaxPric, LastPric) necessários ao novo gráfico
- **Tooltip do Radiobutton VWAP**: Atualizada com descrição completa do novo gráfico

### [improve-button-behavior](openspec/changes/archive/2026-06-27-improve-button-behavior) Hoje carrega dados automaticamente; persistência da última pasta nos diálogos de ticker

#### Added

- Preferência `last_ticker_dir` em `~/.flowscope/config.json` para persistir o último diretório usado nos diálogos de ticker

#### Changed

- Botão "Hoje" agora também executa carregamento automático de dados (antes apenas resetava a data)
- Botões "Hoje" e "Carregar" desabilitados durante o carregamento (loading guard estendido)
- `TickerList._save()` e `TickerList._load()` usam `initialdir` a partir da preferência persistida
- `TickerList` recebe parâmetros `initialdir` e `on_dir_changed` callback (baixo acoplamento)

### [redesign-gui-notebook](openspec/changes/archive/2026-06-28-redesign-gui-notebook) RadioButton chart selector replaced by two-level notebook with general and per-ticker analysis

#### Added

- Main `ttk.Notebook` replacing the "Visualização" RadioButton frame with tabs "Análise Geral" and "Análise do Ticker"
- Sub-notebook in "Análise Geral" with "VWAP" (existing chart) and "Quadrantes" (placeholder)
- Sub-notebook in "Análise do Ticker" with 5 placeholder tabs (Dominância, Fluxo, Participação, Eficiência, Resumo)
- `ttk.Combobox` in "Análise do Ticker" for selecting a single ticker
- `OrientationPanel` widget with fixed explanatory text per sub-tab

#### Changed

- `_show_current_chart()` adapted to control notebook tabs instead of pack/forget
- `_update_charts()` simplified to update only VWAP chart
- `_copy_chart()` simplified to copy only VWAP chart
- `config.json` persistence: `last_chart` → `last_tab` + `last_subtab`
- TickerList changes propagate to combobox in "Análise do Ticker"

#### Removed

- **BREAKING**: RadioButton group and "Visualização" frame
- **BREAKING**: `CVDHistChart` (GUI chart)
- **BREAKING**: `ScatterChart` (GUI scatter plot)
- **BREAKING**: `--cvd` CLI flag and `export_cvd_csv()`
- **BREAKING**: `ExportCVDUseCase` from application layer
- `AnalysisText` widget (replaced by `OrientationPanel`)

### [implementacao-indicadores-especificacao](openspec/changes/archive/2026-06-28-implementacao-indicadores-especificacao) Motor de cálculo DAG e 15 novos indicadores

#### Added

- Motor de cálculo baseado em DAG: cada indicador é uma estratégia independente que declara dependências; o engine resolve ordem de execução automaticamente e cacheia resultados
- 15 novos indicadores da especificação FS001–FS403: Range, Range%, Typical Price, Median Price, Weighted Close, CLV, Money Flow Multiplier, Money Flow Volume, Buying Pressure, Selling Pressure, Daily Efficiency, Financial Density, Trade Density, Volume Density, Average Trade Size, Average Financial Ticket
- Abas "Dominância do Pregão", "Fluxo Financeiro", "Participação Institucional", "Eficiência do Movimento" e "Resumo Geral" populadas com valores reais dos indicadores
- OrientationPanel com textos explicativos para cada grupo de indicadores

#### Changed

- Indicadores existentes (VWAP, Volume Profile, Top Tickers) refatorados para o novo padrão `IndicatorStrategy`
- **BREAKING**: Preço Referência definido como `avg_price` (desambigua Range% e Daily Efficiency)

#### Removed

- **BREAKING**: Indicador CVD (substituído por Money Flow Volume, que usa CLV contínuo em vez de sinal binário)

### [move-copy-buttons](openspec/changes/archive/2026-06-28-move-copy-buttons) Botões Copiar Dados/Gráfico realocados e frame Exportação eliminado

#### Added

- Botão "Copiar Gráfico" adicionado ao toolbar nativo do matplotlib (`ToolbarBR`), disponível em todos os charts
- Botão "Copiar Dados" na barra superior ao lado de "Carregar", iniciando desabilitado até o primeiro carregamento de dados

#### Changed

- `_copy_chart()` agora recebe o `Figure` como parâmetro (desacoplado do VWAP chart específico)
- `ToolbarBR` aceita `copy_chart_callback` via construtor (callback opcional)

#### Fixed

- `pyxclip` import corrigido (`pyxclip.main` não existe; usa `pyxclip.copy()` direto)
- `print()` substituído por `logging.warning()` com NullHandler na GUI para evitar vazamento de erros da API B3 no terminal
- URLs da API B3 removidas de mensagens de erro (sanitizadas no `B3Client`)

#### Removed

- Frame `Exportação` (LabelFrame + botões + separador) do `self._left_pw`
- Dependência do `_vwap_chart.get_figure()` em `_copy_chart()`

### [normalize-vwap-y-axis](openspec/changes/archive/2026-06-28-normalize-vwap-y-axis) Eixo Y do VWAP normalizado para desvio percentual com baseline em 0%

#### Changed

- **Eixo Y do VWAP**: Substituído preço absoluto (R$) por `(preço - VWAP) / VWAP × 100`
- **Baseline VWAP**: Linha horizontal tracejada em Y = 0% adicionada como referência visual
- **Violin plot, errorbar e scatter**: Todos os elementos visuais usam escala normalizada (%)
- **Errorbar → vlines**: Barra MinPric–MaxPric trocada para `ax.vlines()` + scatter em 0 (mais robusto em casos extremos)
- **Bucket size**: Heurística adaptada para ranges percentuais (0.01%–0.50%)
- **Tooltip hover**: Agora exibe delta percentual (Δ Máx/Mín) + LastPric % + VWAP absoluto (R$)
- **Rótulo do eixo Y**: Alterado para "Diferença do VWAP (%)"
- **Limites do eixo Y**: Configurados simetricamente em torno de 0%

### [fix-desktop-shortcut](openspec/changes/archive/2026-06-28-fix-desktop-shortcut) Atalho .desktop com caminho absoluto, ícone permanente e botão na GUI

#### Added

- Botão "Criar atalho no desktop" na barra superior da GUI (Linux) quando nenhum atalho existe, some após criar com sucesso
- Função compartilhada `_resolve_icon_path()` para resolução de ícone em modo dev e frozen (PyInstaller)
- `StartupNotify=true` e flag `--gui` no arquivo .desktop

#### Fixed

- `Exec` no .desktop agora usa caminho absoluto (`Path(sys.argv[0]).resolve()`), antes era relativo (`./flowscope`)
- Ícone no .desktop copiado para `~/.local/share/icons/flowscope.png` (permanente), antes resolvia para `/tmp/...` que sumia após fechar o app
- Resolução de ícone do toolbar (copy.png) corrigida para builds PyInstaller

#### Changed

- `_create_desktop_shortcut()` retorna `bool` em vez de chamar `sys.exit()` (reutilizável pela GUI)
- CLI `--create-shortcut` passou a verificar plataforma no `main()` e retornar exit code 0 em não-Linux

[0.4.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.4.0

[0.3.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.3.1
[0.3.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.3.0
[0.2.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.2.1
[0.2.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.2.0
[0.1.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.1.0

See main [CHANGELOG](CHANGELOG.md) for newer releases.
