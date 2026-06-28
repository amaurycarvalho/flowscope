# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.2.0
See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
