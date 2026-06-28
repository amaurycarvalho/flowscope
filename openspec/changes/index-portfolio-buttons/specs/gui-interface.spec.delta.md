## Purpose

Delta spec for `gui-interface`: adicionar botões de índice IBOV/IDIV/IFIX e generalizar autopreenchimento.

## Modified Requirements

### Requirement: Botões de índice IBOV, IDIV e IFIX

O sistema DEVE exibir três botões — "IBOV", "IDIV" e "IFIX" — em uma fileira abaixo dos botões "Salvar Tickers", "Carregar Tickers" e "Filtrar". Cada botão, quando pressionado, DEVE baixar a carteira teórica diária do respectivo índice via API B3 e **substituir** o conteúdo do campo de tickers pelos tickers obtidos.

#### Scenario: Botão IBOV carrega carteira do IBOV
- **WHEN** o usuário clica no botão "IBOV"
- **THEN** o sistema DEVE baixar a carteira do IBOV e preencher o campo de tickers com os tickers obtidos

#### Scenario: Botão IFIX carrega carteira do IFIX
- **WHEN** o usuário clica no botão "IFIX"
- **THEN** o sistema DEVE baixar a carteira do IFIX e preencher o campo de tickers com os tickers obtidos

#### Scenario: Falha no download de um índice
- **WHEN** o usuário clica em um botão de índice e o download falha
- **THEN** o sistema DEVE exibir uma mensagem de erro na barra de status e NÃO DEVE alterar o campo de tickers

### Requirement: Preenchimento automático com IDIV quando filtro vazio (modificado)

O sistema DEVE, quando o campo de filtro de tickers estiver vazio e o usuário pressionar "Carregar" (ou editar o filtro de forma que ele fique vazio), buscar automaticamente a carteira do **IDIV** e preencher o campo com os tickers do índice. Esta lógica DEVE usar o mesmo mecanismo interno do botão "IDIV".

#### Scenario: Carregar com filtro vazio (comportamento preservado)
- **WHEN** o campo de tickers está vazio e o usuário clica em "Carregar"
- **THEN** o sistema DEVE buscar a carteira IDIV (via `_fill_with_index("IDIV")`), preencher o campo de tickers com os tickers obtidos, e carregar os dados filtrando apenas por esses tickers

#### Scenario: Edição do filtro deixando-o vazio dispara autopreenchimento
- **WHEN** o campo de tickers contém tickers, o usuário apaga todos, e o sistema detecta o campo vazio
- **THEN** o sistema DEVE buscar a carteira IDIV e preencher o campo automaticamente (mesmo comportamento do botão "Carregar" com filtro vazio)

#### Scenario: Erro na busca IDIV com filtro vazio (comportamento preservado)
- **WHEN** o campo de tickers está vazio, o sistema tenta buscar IDIV, e a busca falha
- **THEN** o sistema DEVE exibir uma mensagem de erro e NÃO DEVE carregar dados
