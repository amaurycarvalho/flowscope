## 1. Generalizar parser

- [x] 1.1 Renomear `parse_idiv_csv()` para `parse_index_csv()` no `parser.py`, removendo a verificação `startswith("IDIV -")` e usando detecção genérica (uppercase+ascii, pular linhas de totalização)
- [x] 1.2 Atualizar testes em `test_b3_parser.py`: renomear testes, adicionar casos com CSV de IBOV e IFIX, verificar que linhas "Quantidade Teórica Total" e "Redutor" são ignoradas

## 2. Generalizar B3Client

- [x] 2.1 Adicionar método `_build_portfolio_url(index, language)` que constrói URL via base64 do payload JSON
- [x] 2.2 Adicionar método `fetch_portfolio(index, language)` que substitui `fetch_idiv_portfolio()`, usando `parse_index_csv` e cache por índice
- [x] 2.3 Remover `fetch_idiv_portfolio()` e a constante `_IDIV_URL`

## 3. Generalizar B3DataRepository

- [x] 3.1 Substituir `get_idiv_tickers()` por `get_index_tickers(index: str) -> list[str]`
- [x] 3.2 Atualizar chamadas em `app.py` para usar `get_index_tickers()`

## 4. Adicionar botões IBOV/IDIV/IFIX no TickerList

- [x] 4.1 Adicionar parâmetro `on_index_click: dict[str, callable]` no construtor do `TickerList`
- [x] 4.2 Criar segunda fileira de botões (btn_frame2) com IBOV, IDIV, IFIX, cada um chamando seu callback
- [x] 4.3 Em `app.py`, criar método `_fill_with_index(index)` que chama `repo.get_index_tickers()` + `ticker_list.set_tickers()`
- [x] 4.4 Passar callbacks para `TickerList`: `{"IBOV": lambda: self._fill_with_index("IBOV"), ...}`
- [x] 4.5 Atualizar `_ensure_tickers()` para chamar `self._fill_with_index("IDIV")`
- [x] 4.6 Atualizar `_on_ticker_edit()` para chamar `self._fill_with_index("IDIV")`

## 5. Verificação final

- [x] 5.1 Rodar testes existentes e garantir que não quebraram
- [x] 5.2 Rodar `ruff` (linter) e garantir que não há warnings
- [x] 5.3 Verificar manualmente que os 3 botões carregam as carteiras corretas
