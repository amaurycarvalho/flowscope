## 1. Data Layer — Propagar campos faltantes no daily_data

- [x] 1.1 Adicionar `segment` (t.segment) e `trades_qty` (t.trades_qty.value) ao dicionário `daily_data` no método `AnalyzeTickersUseCase.execute()` em `src/flowscope/application/use_cases.py`

## 2. GUI — Substituir lógica do botão "Copiar Dados"

- [x] 2.1 Criar método `_build_raw_csv()` em `app.py` que monta a string CSV com cabeçalho e dados brutos, detectando a aba ativa para determinar quais tickers incluir
- [x] 2.2 Substituir `_copy_data()` para usar `_build_raw_csv()` e copiar com `pyxclip`
- [x] 2.3 Substituir `_fallback_clipboard_text()` para usar `_build_raw_csv()` e copiar com Tkinter clipboard
