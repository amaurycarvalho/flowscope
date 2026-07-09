## MODIFIED Requirements

### Requirement: Botões de índice IBOV, IDIV e IFIX

O sistema DEVE exibir três botões — "IBOV", "IDIV" e "IFIX" — na barra superior do TickerList, após um separador vertical do grupo de seleção (Editar, Selecionar Todos, Desmarcar Todos). Cada botão, quando pressionado, DEVE baixar a carteira teórica diária do respectivo índice via API B3 e **substituir** o conteúdo do Listbox pelos tickers obtidos. Durante todo o processo de download e análise, todos os botões da aplicação DEVEM ser desabilitados e restaurados ao estado anterior ao finalizar (conforme especificado em `loading-state-management`).

#### Scenario: Botão IBOV carrega carteira do IBOV com loading state

- **WHEN** o usuário clica no botão "IBOV"
- **THEN** o sistema DEVE desabilitar todos os botões, baixar a carteira do IBOV, preencher o campo de tickers com os tickers obtidos, processar os dados, e restaurar os botões ao estado anterior

#### Scenario: Botão IFIX carrega carteira do IFIX com loading state

- **WHEN** o usuário clica no botão "IFIX"
- **THEN** o sistema DEVE desabilitar todos os botões, baixar a carteira do IFIX, preencher o campo de tickers com os tickers obtidos, processar os dados, e restaurar os botões ao estado anterior

#### Scenario: Falha no download de um índice

- **WHEN** o usuário clica em um botão de índice, o download falha, e a lista de tickers NÃO é alterada
- **THEN** o sistema DEVE exibir uma mensagem de erro na barra de status e restaurar os botões ao estado anterior

### Requirement: Preenchimento automático com IDIV quando lista vazia

O sistema DEVE, quando a lista de tickers estiver vazia e o usuário pressionar "Carregar", buscar automaticamente a carteira do **IDIV** e preencher o Listbox com os tickers do índice. Durante esta operação, todos os botões DEVEM ser desabilitados.

#### Scenario: Carregar com lista vazia desabilita botões

- **WHEN** a lista de tickers está vazia e o usuário clica em "Carregar"
- **THEN** o sistema DEVE desabilitar todos os botões, buscar a carteira IDIV, preencher o Listbox com os tickers obtidos, selecionar todos, carregar os dados, e restaurar os botões

#### Scenario: Erro na busca IDIV com lista vazia restaura botões

- **WHEN** a lista de tickers está vazia, o sistema tenta buscar IDIV, a busca falha, e NÃO carrega dados
- **THEN** o sistema DEVE exibir uma mensagem de erro e restaurar os botões ao estado anterior

#### Scenario: Lista já preenchida mantém loading state

- **WHEN** a lista de tickers contém tickers e o usuário clica em "Carregar"
- **THEN** o sistema DEVE desabilitar todos os botões, carregar os dados para todos os tickers existentes no Listbox, e restaurar os botões ao finalizar
