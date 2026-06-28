## Why

Atualmente o sistema só consegue baixar a carteira do IDIV para preenchimento automático de tickers. O endpoint da B3 é genérico (qualquer índice via `GetDownloadPortfolioDay`), mas o código está travado em IDIV. Adicionar botões para IBOV, IDIV e IFIX permite ao usuário carregar rapidamente qualquer uma dessas carteiras, eliminando a necessidade de digitar tickers manualmente.

## What Changes

- **Generalizar** `B3Client.fetch_idiv_portfolio()` → `fetch_portfolio(index: str)` que aceita qualquer código de índice
- **Generalizar** `parse_idiv_csv()` → `parse_index_csv()` que funciona para qualquer índice
- **Substituir** `B3DataRepository.get_idiv_tickers()` → `get_index_tickers(index: str)`
- **Adicionar** botões "IBOV", "IDIV" e "IFIX" no `TickerList` (fileira abaixo dos botões existentes)
- **Extrair** lógica de autopreenchimento para `_fill_with_index("IDIV")` e reusar em `_ensure_tickers()` e `_on_ticker_edit()`
- **Remover** `fetch_idiv_portfolio()` e `parse_idiv_csv()` (substituídos de uma vez)

## Capabilities

### New Capabilities
- `index-portfolio-download`: Download da carteira teórica de qualquer índice da B3 via endpoint `GetDownloadPortfolioDay`, com parser genérico e cache por índice

### Modified Capabilities
- `data-ingestion`: Generalizar requirement de "Download da carteira do IDIV" para "Download da carteira de qualquer índice". Cache passa a ser por `(índice, data)` em vez de só IDIV.
- `gui-interface`: Generalizar requirement de "Preenchimento automático com IDIV" para "Botões de índice + preenchimento automático via IDIV". Adicionar requirement dos botões IBOV/IDIV/IFIX.

## Impact

- `src/flowscope/infrastructure/b3/client.py` — substituir `fetch_idiv_portfolio()` por `fetch_portfolio(index)`
- `src/flowscope/infrastructure/b3/parser.py` — substituir `parse_idiv_csv()` por `parse_index_csv()`
- `src/flowscope/infrastructure/b3/repository.py` — substituir `get_idiv_tickers()` por `get_index_tickers(index)`
- `src/flowscope/presentation/gui/widgets/ticker_list.py` — adicionar botões IBOV/IDIV/IFIX com callbacks
- `src/flowscope/presentation/gui/app.py` — atualizar `_ensure_tickers()` e `_on_ticker_edit()` para usar `_fill_with_index("IDIV")`
- `tests/test_infrastructure/test_b3_parser.py` — atualizar testes para `parse_index_csv`
- Cache: mudar chave de `idiv_portfolio_v2` para `portfolio_{index}`
