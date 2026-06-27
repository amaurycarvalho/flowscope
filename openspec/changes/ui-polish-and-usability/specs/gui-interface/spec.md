## ADDED Requirements

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
