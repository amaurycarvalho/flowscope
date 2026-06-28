# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] — 2026-06-28

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

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.1.1
[0.1.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.1.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
