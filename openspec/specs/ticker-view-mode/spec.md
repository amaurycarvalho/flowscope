## Purpose

Define the ticker list view mode with Listbox-based multi-selection, edit/view toggle, and selection controls.

## Requirements

### Requirement: Modo visualização com Listbox de seleção múltipla

O sistema DEVE prover um modo visualização no TickerList onde a lista de tickers é exibida em um `tk.Listbox` com `selectmode=EXTENDED`, permitindo que o usuário selecione múltiplos tickers usando Ctrl+Click (alternar) e Shift+Click (intervalo).

O modo visualização DEVE ser o padrão ao abrir o programa e após qualquer carga de dados.

Neste modo, o método `get_tickers()` DEVE retornar apenas os tickers atualmente selecionados no Listbox.

#### Scenario: Listbox exibido no modo visualização
- **WHEN** o usuário carrega dados para 30 tickers
- **THEN** o TickerList DEVE exibir um Listbox com todos os 30 tickers, todos selecionados

#### Scenario: get_tickers retorna seleção no modo visualização
- **WHEN** o usuário desmarca 3 tickers dos 30 no Listbox
- **THEN** `get_tickers()` DEVE retornar uma lista com 27 tickers (apenas os marcados)

### Requirement: Modo edição com Text widget

O sistema DEVE prover um modo edição onde a lista de tickers é exibida em um `tk.Text` editável, permitindo ao usuário digitar, colar, carregar de arquivo e editar livremente os tickers.

Neste modo, o método `get_tickers()` DEVE retornar todos os tickers presentes no Text widget.

#### Scenario: Text widget no modo edição
- **WHEN** o usuário ativa o modo edição
- **THEN** o TickerList DEVE exibir o Text widget com o conteúdo atual da lista de tickers

### Requirement: Botão toggle "Editar lista de tickers"

O sistema DEVE exibir um botão do tipo toggle (checkbutton com `indicatoron=0`) com o ícone `document-properties.png` na barra superior entre "Salvar" e "Selecionar Todos". Botão marcado = modo edição; desmarcado = modo visualização.

#### Scenario: Alternância visual entre modos
- **WHEN** o usuário clica no botão "Editar lista de tickers"
- **THEN** o TickerList DEVE alternar entre modo visualização e modo edição

### Requirement: Botões "Selecionar Todos" e "Desmarcar Todos"

O sistema DEVE exibir dois botões na barra superior, à direita do botão "Editar", visíveis apenas no modo visualização:
- "Selecionar Todos" com ícone `edit-select-all.png`: marca todos os tickers do Listbox
- "Desmarcar Todos" com ícone `edit-unselect-all.png`: desmarca todos os tickers do Listbox (apenas visual, sem disparar callback)

#### Scenario: Selecionar Todos
- **WHEN** o usuário desmarcou 10 de 30 tickers e clica em "Selecionar Todos"
- **THEN** todos os 30 tickers DEVEM ficar marcados no Listbox

#### Scenario: Desmarcar Todos
- **WHEN** o usuário clica em "Desmarcar Todos" com 30 tickers carregados
- **THEN** nenhum ticker DEVE ficar marcado no Listbox

### Requirement: Transição edit→view com preservação de seleção

Ao sair do modo edição, o sistema DEVE:
1. Ler os tickers do Text widget
2. Comparar com a lista anterior
3. Tickers existentes: preservar estado de marcação
4. Tickers novos: marcar como selecionados
5. Tickers removidos: desaparecem do Listbox
6. Se a lista mudou: disparar recarga de dados

#### Scenario: Preservação de seleção após edição
- **WHEN** usuário está com tickers A,B,C,D marcados e E,F desmarcados, entra em edição, adiciona G, remove F, volta à visualização
- **THEN** Listbox exibe A,B,C,D,E,G com A,B,C,D,G marcados e E desmarcado; recarga de dados disparada

### Requirement: Separadores entre grupos de botões

Dois separadores verticais DEVEM ser exibidos na barra superior:
1. Entre "Salvar" e "Editar"
2. Entre o grupo de seleção (Editar + Selecionar Todos + Desmarcar Todos) e os botões de índice (IBOV, IDIV, IFIX)

### Requirement: Lazy refresh híbrido de gráficos

O sistema DEVE atualizar os gráficos de forma híbrida:
- Aba ativa: renderizada imediatamente após carga/filtro
- Demais abas: renderizadas apenas quando selecionadas

#### Scenario: Renderização imediata da aba ativa após carga
- **WHEN** o usuário carrega dados estando na aba "VWAP"
- **THEN** o gráfico VWAP DEVE ser renderizado imediatamente
