## 1. Data Layer — Propagar campos faltantes no daily_data

- [x] 1.1 Adicionar `segment` (t.segment) e `trades_qty` (t.trades_qty.value) ao dicionário `daily_data` no método `AnalyzeTickersUseCase.execute()` em `src/flowscope/application/use_cases.py`

## 2. GUI — Substituir lógica do botão "Copiar Dados"

- [x] 2.1 Criar método `_build_raw_csv()` em `app.py` que monta a string CSV com cabeçalho e dados brutos, detectando a aba ativa para determinar quais tickers incluir
- [x] 2.2 Substituir `_copy_data()` para usar `_build_raw_csv()` e copiar com `pyxclip`
- [x] 2.3 Substituir `_fallback_clipboard_text()` para usar `_build_raw_csv()` e copiar com Tkinter clipboard

## 3. Propagação de sampling_dates

- [x] 3.1 Adicionar `_sampling_dates: list[date]` no dict resultado do `AnalyzeTickersUseCase.execute()`
- [x] 3.2 Em `set_current_data()`, extrair `_sampling_dates` do data dict e armazenar em `self._sampling_dates`, removendo chaves `_` de `self._current_data`

## 4. CSV com todas as datas de amostragem

- [x] 4.1 Em `_build_raw_csv()`, iterar sobre `self._sampling_dates` (com fallback para datas extraídas do daily_data)
- [x] 4.2 Para cada data de amostragem sem trade do ticker, emitir linha com `;;;;;;;` (valores vazios)
