## 1. Extrair `_compute_stems` compartilhado

- [x] 1.1 Criar função `_compute_stems` em `dominance_ranking.py` (ou módulo de utilidades compartilhadas) que recebe `(ys, values, clvs, max_val, scale=0.10)` e retorna `(stem_ys, stem_xmins, stem_xmaxs, stem_colors)`
- [x] 1.2 Refatorar `DominanceRankingChart.update` para usar `_compute_stems`
- [x] 1.3 Refatorar `DominanceTimelineChart.update` para usar `_compute_stems`
- [x] 1.4 Verificar que `classify_dominance` continua sendo chamado corretamente nos dois charts

## 2. Extrair `_render_last_day_markers` do PriceRangePanel

- [x] 2.1 Extrair bloco `is_last` (scatters + annots + hover_data) para `_render_last_day_markers(self, d, i, typical_dict, median_dict, weighted_dict, range_pct_dict)`
- [x] 2.2 Chamar o novo método em `_build_main_chart` substituindo o bloco condicional
- [x] 2.3 Remover variável `today_range_text` não usada (F841)

## 3. Extrair `_collect_ticker_data` e `_compute_violin_shapes` do VWAPHistChart

- [x] 3.1 Extrair loop de coleta de dados para `_collect_ticker_data(self, data)` que retorna `(tickers, violin_data, vwap_values_abs, min_prices_pct, max_prices_pct, last_prices_pct)`
- [x] 3.2 Extrair processamento de buckets/violin para `_compute_violin_shapes(self, violin_data)` que retorna `(violin_shapes, max_vol, bucket_size)`
- [x] 3.3 Refatorar `VWAPHistChart.update` para usar ambos os métodos

## 4. Extrair `_annotate_tickers` do QuadrantChart

- [x] 4.1 Extrair loop de anotações para `_annotate_tickers(self)` que itera sobre `self._hover_data` e adiciona anotações
- [x] 4.2 Refatorar `QuadrantChart.update` para chamar `_annotate_tickers` após o scatter

## 5. Adicionar `# noqa: C901` nos `_generate_summary`

- [x] 5.1 Adicionar `# noqa: C901` na assinatura de `FinancialFlowPanel._generate_summary`
- [x] 5.2 Adicionar `# noqa: C901` na assinatura de `QuadrantChart._generate_summary`

## 6. Remover imports não usados (F401) e variáveis não usadas (F841)

- [x] 6.1 `src/flowscope/domain/indicators.py` — remover `IndicatorStrategy` do import
- [x] 6.2 `src/flowscope/domain/strategies/price.py` — remover `from collections import defaultdict`
- [x] 6.3 `src/flowscope/infrastructure/clipboard_image.py` — remover `import sys`
- [x] 6.4 `src/flowscope/presentation/cli.py` — remover `from decimal import Decimal` e `from flowscope import __version__`
- [x] 6.5 `src/flowscope/presentation/main.py` — remover `import os`
- [x] 6.6 `src/flowscope/infrastructure/cache.py` — remover ou prefixar `local_appdata` (F841 linha 17)
- [x] 6.7 `src/flowscope/presentation/gui/charts/financial_flow_panel.py` — remover `n_days` e `mfv_line` (F841)
- [x] 6.8 `src/flowscope/presentation/gui/charts/price_range_panel.py` — remover `today_range_text` (F841)
- [x] 6.9 `tests/conftest.py` — remover `import responses` e `from flowscope.infrastructure.cache import CacheManager`
- [x] 6.10 `tests/test_domain/test_indicators.py` — remover `Any` dos imports locais (linhas 52, 87)
- [x] 6.11 `tests/test_infrastructure/test_b3_repository.py` — remover `from unittest.mock import MagicMock`
- [x] 6.12 `tests/test_presentation/test_cli.py` — remover `import sys` e `from unittest.mock import patch`
- [x] 6.13 `tests/test_presentation/test_controller.py` — remover `patch` do import e `import pytest`
- [x] 6.14 `tests/test_presentation/test_main.py` — remover `import sys`, `import pytest`, e `as real_create`
- [x] 6.15 `tests/test_presentation/test_presenter.py` — remover `call` do import

## 7. Limpeza cosmética

- [x] 7.1 Corrigir W391 (blank line at end of file) em `entities.py`, `cli.py`, `test_main.py`
- [x] 7.2 Corrigir E306 (blank line before nested def) em `test_progress.py` (6 ocorrências) e `price_range_panel.py` (1)
- [x] 7.3 Corrigir E302 (expected 2 blank lines) em `main.py`
- [x] 7.4 Corrigir E741 (ambiguous `l`) em `ticker_list.py` (2 ocorrências)
- [x] 7.5 Corrigir E127/E128/E129/E131 em `app.py` (5 ocorrências)
- [x] 7.6 Quebrar linhas E501 que podem ser quebradas em `app.py` e `ticker_list.py`; adicionar `# noqa: E501` nas que não podem

## 8. Verificação final

- [x] 8.1 Executar linter e confirmar zero warnings
- [x] 8.2 Executar testes e confirmar que todos passam