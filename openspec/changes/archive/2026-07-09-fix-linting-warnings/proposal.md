## Why

O repositório acumulou 75 warnings de linting (C901, F401, F841, E501, E306, E741, W391, E302, E127-E131) que poluem a saída do linter, mascaram problemas reais e indicam código não limpo após refatorações. Resolver esses warnings melhora a higiene do código, reduz ruído em CI e facilita identificar novos problemas.

## What Changes

- Extrair `_compute_stems` como função compartilhada entre `DominanceRankingChart` e `DominanceTimelineChart` (reduz complexidade C901 de 21→~16 e 12→~8)
- Extrair `_render_last_day_markers` do `PriceRangePanel._build_main_chart` (reduz complexidade de 16→~10)
- Extrair `_collect_ticker_data` e `_compute_violin_shapes` do `VWAPHistChart.update` (reduz complexidade de 14→~9)
- Extrair `_annotate_tickers` do `QuadrantChart.update` (reduz complexidade de 15→~12)
- Adicionar `# noqa: C901` nos `_generate_summary` (complexidade inerente de geração de texto narrativo)
- Remover 19 imports não usados (F401) e 4 variáveis não usadas (F841)
- Corrigir 37 problemas cosméticos (E501 linhas longas simples, E306, E741, W391, E302, E127-E131)

## Capabilities

### New Capabilities

Nenhuma — change puramente de refatoração e limpeza.

### Modified Capabilities

Nenhuma — nenhuma spec de capability existente. Mudanças são exclusivamente de implementação.

## Impact

- `src/flowscope/presentation/gui/charts/dominance_ranking.py`
- `src/flowscope/presentation/gui/charts/dominance_timeline.py`
- `src/flowscope/presentation/gui/charts/vwap_hist.py`
- `src/flowscope/presentation/gui/charts/quadrant_chart.py`
- `src/flowscope/presentation/gui/charts/price_range_panel.py`
- `src/flowscope/presentation/gui/charts/financial_flow_panel.py`
- `src/flowscope/presentation/gui/app.py`
- `src/flowscope/presentation/gui/widgets/ticker_list.py`
- `src/flowscope/presentation/cli.py`
- `src/flowscope/presentation/main.py`
- `src/flowscope/domain/indicators.py`
- `src/flowscope/domain/strategies/price.py`
- `src/flowscope/infrastructure/b3/client.py`
- `src/flowscope/infrastructure/cache.py`
- `src/flowscope/infrastructure/clipboard_image.py`
- `tests/conftest.py`
- `tests/test_domain/test_indicators.py`
- `tests/test_infrastructure/test_b3_repository.py`
- `tests/test_presentation/test_cli.py`
- `tests/test_presentation/test_controller.py`
- `tests/test_presentation/test_main.py`
- `tests/test_presentation/test_presenter.py`
- `tests/test_presentation/test_progress.py`