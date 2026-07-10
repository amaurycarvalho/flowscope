# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional
- [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões
- [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado com gauge de concentração, card informativo e timeline AFT

## [0.6.0] — 2026-07-10

### [copiar-dados-csv](openspec/changes/archive/2026-07-10-copiar-dados-csv) Botão Copiar Dados passa a exportar dados brutos CSV da B3 em vez de indicadores agregados

#### Added
- `segment` e `trades_qty` adicionados ao `daily_data` no use case para viabilizar o CSV completo

#### Changed
- Lógica do botão "Copiar Dados" substituída para copiar dados brutos CSV (SgmtNm=CASH) com campos `RptDt;TckrSymb;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;FinInstrmQty;NtlFinVol`
- Na aba "Análise do Ticker": copia dados apenas do ticker selecionado; na "Análise Geral": copia de todos os tickers selecionados
- Período copiado reflete o selecionado nos comboboxes de período e amostragem
- Formato brasileiro: campo separado por `;`, decimal com `,` (vírgula)
- OperationGuard continua desabilitando/habilitando o botão durante cargas; atalho `Ctrl+Shift+C` mantido

### [sampling-strategy-selector](openspec/changes/archive/2026-07-10-sampling-strategy-selector) Comboboxes de período e amostragem para controle flexível da janela temporal de análise

#### Added
- Combobox de período (30/60/90 dias) na barra superior, ao lado do botão Copiar CSV
- Combobox de amostragem (Fibonacci, Fibonacci reverso, Fibonacci duplo, Monte Carlo, Monte Carlo duplo, Todos os dias)
- Tooltip único e fixo em cada combobox com explicação geral do controle
- Recarga automática de dados ao mudar seleção dos combos quando dados já estão carregados
- Se nenhum dado estiver carregado, mudar combos não tem efeito

#### Changed
- Barra de status exibe texto explicativo do item selecionado ao percorrer os comboboxes
- `calendar.py` com novas funções de geração de datas para cada combinação período × amostragem
- `DataRepository.get_available_dates()` recebe parâmetros de período e amostragem
- `B3Client.fetch_file()` aceita modo `cache_only` — período > 30 usa apenas cache
- Ajuste de cada data de amostragem para o próximo dia útil disponível no cache (±7 dias), com deduplicação
- `AnalyzeTickersUseCase.execute()` recebe config de período/amostragem e propaga ao repositório
- Dois comboboxes incluídos no OperationGuard (desabilitados durante carga/processamento)

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.6.0...HEAD

[0.6.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.6.0
See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
