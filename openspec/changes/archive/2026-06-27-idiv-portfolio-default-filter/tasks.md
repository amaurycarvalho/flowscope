## 1. Cache com TTL no CacheManager

- [x] 1.1 Adicionar suporte a TTL em `CacheManager`: novo método `get_or_fetch(key, ttl_days, fetch_fn)` que verifica idade do cache e busca novamente se expirado
- [x] 1.2 Garantir compatibilidade com cache existente de CSVs (sem TTL)

## 2. Parsing do CSV do IDIV

- [x] 2.1 Criar função `parse_idiv_csv(content: str) -> list[str]` que extrai a coluna `Código` do CSV da carteira IDIV, ignorando cabeçalho e rodapé
- [x] 2.2 Escrever testes unitários para `parse_idiv_csv` com CSV de exemplo real

## 3. Novo método B3Client.fetch_idiv_portfolio()

- [x] 3.1 Adicionar método `fetch_idiv_portfolio() -> list[str]` que faz GET no endpoint do IDIV com token base64 codificado
- [x] 3.2 Usar `CacheManager` com TTL de 7 dias no método
- [x] 3.3 Tratar erros de rede/parse retornando lista vazia

## 4. Filtro CASH no parser de CSV consolidado

- [x] 4.1 Adicionar parâmetro `segment_filter: str | None = "CASH"` em `parse_csv()`
- [x] 4.2 Pular linhas onde `SgmtNm != segment_filter` (se `segment_filter` não for `None`)
- [x] 4.3 Atualizar testes existentes para contemplar o filtro CASH

## 5. Integração no repositório

- [x] 5.1 Adicionar método `get_idiv_tickers() -> list[str]` em `B3DataRepository` que usa `B3Client.fetch_idiv_portfolio()`
- [x] 5.2 Garantir que `fetch_trades()` filtra por segmento CASH (via parser)

## 6. Auto-preenchimento na GUI

- [x] 6.1 Em `_on_load_data()`: se `self._tickers` estiver vazio, buscar IDIV via repositório e preencher campo de texto antes de carregar
- [x] 6.2 Em `_on_ticker_edit()`: se campo de texto estiver vazio, buscar IDIV via repositório e preencher antes de filtrar
- [x] 6.3 Exibir mensagem de erro na statusbar se busca do IDIV falhar
