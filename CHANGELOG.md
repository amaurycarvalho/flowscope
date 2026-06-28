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

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.2.0
See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
