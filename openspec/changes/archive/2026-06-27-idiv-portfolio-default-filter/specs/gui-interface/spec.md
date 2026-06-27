## ADDED Requirements

### Requirement: Preenchimento automático com IDIV quando filtro vazio

O sistema DEVE, quando o campo de filtro de tickers estiver vazio e o usuário pressionar "Carregar" ou "Filtrar", buscar automaticamente a carteira do IDIV e preencher o campo com os tickers do índice. O carregamento de dados DEVE então prosseguir usando essa lista como filtro.

#### Scenario: Carregar com filtro vazio
- **WHEN** o campo de tickers está vazio e o usuário clica em "Carregar"
- **THEN** o sistema DEVE buscar a carteira IDIV, preencher o campo de tickers com os tickers obtidos, e carregar os dados filtrando apenas por esses tickers

#### Scenario: Filtrar com filtro vazio
- **WHEN** o campo de tickers está vazio e o usuário clica em "Filtrar"
- **THEN** o sistema DEVE buscar a carteira IDIV, preencher o campo de tickers com os tickers obtidos, e aplicar o filtro

#### Scenario: Erro na busca IDIV com filtro vazio
- **WHEN** o campo de tickers está vazio, o usuário clica em "Carregar", e a busca do IDIV falha
- **THEN** o sistema DEVE exibir uma mensagem de erro e NÃO DEVE carregar dados

#### Scenario: Filtro já preenchido mantém comportamento atual
- **WHEN** o campo de tickers contém tickers e o usuário clica em "Carregar" ou "Filtrar"
- **THEN** o sistema DEVE usar os tickers existentes no campo, sem buscar o IDIV
