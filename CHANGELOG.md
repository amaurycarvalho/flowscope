# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.1] — 2026-07-03

### [sem-dados-empty-state](openspec/changes/archive/2026-07-03-sem-dados-empty-state) Estado vazio "Sem dados" com lazy rendering por sub-tab

#### Added
- Todos os 6 charts passam a exibir "Sem dados" centralizado com `ax.axis("off")` na inicialização e quando não há dados disponíveis
- Utility function compartilhada para o estado vazio (`create_empty`, `show_empty`, `hide_empty`)
- Registry mapping em `app.py` para coordenar qual chart renderizar por sub-tab, eliminando o `if/elif` atual

#### Changed
- Renderização dos charts passa a ser lazy por sub-tab: apenas o chart da sub-tab visível é atualizado ao carregar/recarregar dados
- Ao recarregar dados, todos os charts não-visíveis voltam ao estado "Sem dados" (Opção A)
- Charts multi-eixos (PriceRangePanel, FinancialFlowPanel) usam `fig.text()` centralizado em vez de labels por subplot (Opção B)

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.5.1...HEAD

[0.5.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.5.1
See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
