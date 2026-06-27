## Purpose

Define the graphical user interface for FlowScope, including the Tkinter main window, chart widgets (VWAP histogram, CVD histogram, scatter plot with temporal arrows), ticker list management, and clipboard export.

## Requirements

### Requirement: Gráfico de dispersão VWAP × CVD
O sistema DEVE exibir um scatter plot com VWAP no eixo X e CVD no eixo Y, onde cada ponto representa um ticker. O tamanho dos marcadores DEVE variar conforme o volume financeiro (NtlFinVol) e a cor por quadrante. O checkbox "Exibir setas temporais" DEVE desenhar setas conectando a posição de cada ticker no dia anterior (d-1) à sua posição no dia atual (d), indicando a trajetória temporal.

#### Scenario: Checkbox quiver temporal marcado
- **WHEN** o usuário marca o checkbox "Exibir setas temporais"
- **THEN** setas DEVEM ser desenhadas no scatter plot conectando a posição (VWAP, CVD) de cada ticker em d-1 à sua posição em d, com setas indicando a direção

### Requirement: Campo multilinha de seleção de tickers
O sistema DEVE fornecer um campo de texto multilinha onde o usuário pode editar a lista de tickers (um por linha). O sistema DEVE fornecer um botão "Filtrar" ao lado de "Salvar Tickers" e "Carregar Tickers". As alterações no campo de texto NÃO DEVEM atualizar os gráficos automaticamente. O filtro DEVE ser aplicado apenas quando o botão "Filtrar" for pressionado manualmente. O botão "Carregar Tickers" DEVE preencher o campo sem aplicar o filtro automaticamente.

#### Scenario: Filtro manual via botão "Filtrar"
- **WHEN** o usuário edita a lista de tickers e clica no botão "Filtrar"
- **THEN** os gráficos DEVEM ser atualizados para refletir apenas os tickers presentes no campo

#### Scenario: Edição manual não atualiza gráficos
- **WHEN** o usuário digita ou apaga tickers no campo texto
- **THEN** os gráficos NÃO DEVEM ser atualizados

#### Scenario: Carregar tickers de arquivo não atualiza gráficos
- **WHEN** o usuário clica em "Carregar Tickers" e seleciona um arquivo
- **THEN** o campo DEVE ser preenchido com os tickers do arquivo, e os gráficos NÃO DEVEM ser atualizados

### Requirement: Duplo clique filtra ticker
O sistema DEVE aplicar filtro para mostrar apenas o ticker onde o usuário der duplo clique no campo de texto de tickers.

#### Scenario: Duplo clique em ticker existente
- **WHEN** o usuário dá duplo clique na palavra "PETR4" no campo de tickers
- **THEN** o campo DEVE ser atualizado para conter apenas "PETR4" e o filtro DEVE ser aplicado

### Requirement: Menu de contexto no campo de tickers
O campo de texto de tickers DEVE exibir um menu de contexto ao clicar com o botão direito, com opções: Copiar ticker, Remover do filtro, Selecionar todos, Limpar seleção.

#### Scenario: Menu de contexto com ticker selecionado
- **WHEN** o usuário seleciona "PETR4" no campo e clica com botão direito em "Copiar ticker"
- **THEN** o texto "PETR4" DEVE ser copiado para o clipboard

#### Scenario: Menu de contexto "Selecionar todos"
- **WHEN** o usuário clica com botão direito e escolhe "Selecionar todos"
- **THEN** todo o texto no campo DEVE ser selecionado

### Requirement: Contagem de tickers
O sistema DEVE exibir um label ao lado do campo de tickers indicando a quantidade total carregada "Tickers (N)" e, quando filtrado, "Exibindo M de N ativos".

#### Scenario: Label atualizado após carregamento
- **WHEN** dados de 37 tickers são carregados
- **THEN** o label DEVE mostrar "Tickers (37)"

#### Scenario: Label atualizado após filtro
- **WHEN** o usuário filtra para 15 de 37 tickers
- **THEN** o label DEVE mostrar "Exibindo 15 de 37 ativos"

### Requirement: Ícone da aplicação na janela
O sistema DEVE carregar e exibir o ícone da aplicação na barra de título e barra de tarefas.

#### Scenario: Ícone carregado no Linux
- **WHEN** o aplicativo inicia no Linux e `flowscope.png` existe em `src/flowscope/icons/`
- **THEN** a janela DEVE usar `self.wm_iconphoto(True, tk.PhotoImage(file=path))`

#### Scenario: Ícone carregado no Windows
- **WHEN** o aplicativo inicia no Windows e `flowscope.ico` existe em `src/flowscope/icons/`
- **THEN** a janela DEVE usar `self.iconbitmap(path)`

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
