# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.3.0...HEAD

[0.3.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.3.0
See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
