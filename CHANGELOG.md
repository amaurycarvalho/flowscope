# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] — 2026-06-28

### [quadrantes-ticker-sync](openspec/changes/archive/2026-06-28-quadrantes-ticker-sync) Sincronização de comboboxes e visibilidade condicional de setas nos quadrantes

#### Added
- **Sincronização bidirecional de comboboxes:** combobox do Quadrantes e da Análise do Ticker sincronizam valores entre si. "Todos" no Quadrantes limpa o combobox da Análise do Ticker.

#### Changed
- **Quadrantes — setas (quiver):** ocultas quando o ticker está como "Todos"; exibidas apenas para o ticker selecionado.
- **`QuadrantChart.update()`:** adicionado parâmetro `show_arrows` para controle explícito das setas.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.2.1
See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
