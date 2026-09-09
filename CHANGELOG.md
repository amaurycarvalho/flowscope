# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional
- [documentos-relevantes](openspec/changes/documentos-relevantes) Extração de documentos relevantes (PDFs) da B3 via GetReportsRelevants com cache e integração com VectorStore
- [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões
- [informe-mensal](openspec/changes/informe-mensal) Extração de Informes Mensais Estruturados (type=40) da B3 com entidades próprias e parsing multi-tabela
- [llm-chat](openspec/changes/llm-chat) Assistente RAG integrado à GUI com VectorStore SQLite, embeddings e chat LLM via liteLLM
- [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado com gauge de concentração, card informativo e timeline AFT
- [regulacao-mercado](openspec/changes/regulacao-mercado) Dados regulatórios e de mercado da B3 (fatos relevantes, notícias, censuras, condições excepcionais) integrados ao llm-chat
- [structured-earnings](openspec/changes/structured-earnings) Extração de rendimentos e amortizações de FIIs via API B3 com entidades de domínio, cache e CLI

## [0.8.0] — 2026-09-09

### [fundamental-metrics-table](openspec/changes/fundamental-metrics-table) Tabela fundamentalista "Fundamentos" na aba "Análise Geral" com FFO Yield, Dividend Yield, P/FFO e P/VP para FIIs elegíveis

#### Added

- Nova sub-aba "Fundamentos" no sub-notebook da aba "Análise Geral", com uma tabela (`ttk.Treeview`) alimentada pela watchlist de tickers
- Colunas de identidade para todos os tickers: ticker, nome, tipo (ação/FII/ETF/BDR) e sub-tipo (FII: tijolo/papel/híbrido/fiagro/fiinfra; ação: ordinária/preferencial/ETF)
- Classificação de tipo/sub-tipo: tipo e sub-tipo de ação derivados sintaticamente do ticker e cruzados com `code-cvm-resolution`; sub-tipo de FII via taxonomia versionada
- Colunas de dividendo para todos os tickers: última data-com, último dividendo (somente `Rendimento`; amortização excluída) e tendência do dividendo (último vs. anterior, banda de ±5% configurável, `N/A` sem dividendo anterior)
- Colunas fundamentalistas apenas para FIIs elegíveis (tijolo/híbrido): FFO Yield, Dividend Yield 12m, P/FFO, P/VP, FFO Trend, nº de cotistas + classe e patrimônio + classe — conforme RFC-006/007; ações/ETF/papel/fiagro exibem `N/A`
- Adapter CVM para NAV, nº de cotas e nº de cotistas; provedor Fundamentus para FFO 12m/3m
- Camada de domínio isolada (funções puras, `decimal.Decimal`, evidência por métrica) conforme RFC-007

#### Changed

- Reuso do preço de fechamento dos dados B3 já baixados (sem novo adapter de mercado)

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.8.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
