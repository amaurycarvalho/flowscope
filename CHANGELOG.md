# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.3.1...HEAD

[0.3.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.3.1
See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
