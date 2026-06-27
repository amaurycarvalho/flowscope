## Why

O sistema atualmente carrega todos os tickers disponíveis quando o filtro está vazio, inundando a análise com centenas de ativos irrelevantes. Usuários do mercado brasileiro tipicamente analisam o fluxo de ordens de ativos do IDIV (Índice Dividendos). Ao pré-carregar a carteira do IDIV como filtro padrão e filtrar apenas o segmento CASH, o sistema reduz ruído, acelera o carregamento e entrega dados mais relevantes desde o primeiro uso.

## What Changes

- Novo método `fetch_idiv_portfolio()` no `B3Client` para baixar a carteira do IDIV da B3
- Cache local do portfólio IDIV com TTL (7 dias) — revalidate apenas se expirado
- Filtro `SgmtNm == "CASH"` aplicado no parser do CSV, descartando linhas de outros segmentos (BMF, FUTURE, etc.)
- Quando o campo de filtro de tickers estiver vazio e o usuário pressionar "Carregar" ou "Filtrar", o sistema busca automaticamente a carteira do IDIV e a usa como filtro
- Usuário pode limpar o filtro manualmente para recarregar a carteira IDIV, ou editar a lista para personalizar

## Capabilities

### New Capabilities
- _(nenhuma — as mudanças encaixam-se em capacidades existentes)_

### Modified Capabilities
- `data-ingestion`: Novo requisito para baixar portfólio IDIV via endpoint próprio; novo requisito para filtrar linhas por segmento CASH no parser
- `gui-interface`: Novo requisito para auto-preenchimento do filtro com IDIV quando vazio

## Impact

- `src/flowscope/infrastructure/b3/client.py` — novo método `fetch_idiv_portfolio()`
- `src/flowscope/infrastructure/b3/parser.py` — filtrar linhas por `SgmtNm == "CASH"`
- `src/flowscope/infrastructure/b3/repository.py` — orquestrar fetch IDIV + cache
- `src/flowscope/infrastructure/cache.py` — suporte a cache com TTL para portfólio
- `src/flowscope/presentation/gui/app.py` — `_on_load_data()` e `_on_ticker_edit()`: buscar IDIV se filtro vazio
- `src/flowscope/presentation/gui/widgets/ticker_list.py` — expor método para carregar tickers do IDIV
- Nenhuma nova dependência externa
