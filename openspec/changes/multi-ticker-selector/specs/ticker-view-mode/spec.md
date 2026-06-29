## ADDED Requirements

### Requirement: Modo visualização com Listbox de seleção múltipla

O sistema DEVE prover um modo visualização no TickerList onde a lista de tickers é exibida em um `tk.Listbox` com `selectmode=EXTENDED`, permitindo que o usuário selecione múltiplos tickers usando Ctrl+Click (alternar) e Shift+Click (intervalo).

O modo visualização DEVE ser o padrão ao abrir o programa e após qualquer carga de dados.

Neste modo, o método `get_tickers()` DEVE retornar apenas os tickers atualmente selecionados no Listbox.

#### Scenario: Listbox exibido no modo visualização

- **WHEN** o usuário carrega dados para 30 tickers
- **THEN** o TickerList DEVE exibir um Listbox com todos os 30 tickers, todos selecionados, e o label DEVE mostrar "Tickers (30)"

#### Scenario: get_tickers retorna seleção no modo visualização

- **WHEN** o usuário desmarca 3 tickers dos 30 no Listbox
- **THEN** `get_tickers()` DEVE retornar uma lista com 27 tickers (apenas os marcados)

#### Scenario: Todos marcados após carga de dados

- **WHEN** o usuário clica em "Carregar" e novos dados são carregados
- **THEN** o TickerList DEVE entrar em modo visualização com todos os tickers carregados marcados

### Requirement: Modo edição com Text widget

O sistema DEVE prover um modo edição onde a lista de tickers é exibida em um `tk.Text` editável (comportamento atual), permitindo ao usuário digitar, colar, carregar de arquivo e editar livremente os tickers.

Neste modo, o método `get_tickers()` DEVE retornar todos os tickers presentes no Text widget (comportamento atual).

#### Scenario: Text widget no modo edição

- **WHEN** o usuário ativa o modo edição
- **THEN** o TickerList DEVE exibir o Text widget com o conteúdo atual da lista de tickers

#### Scenario: get_tickers retorna todos no modo edição

- **WHEN** o usuário está no modo edição com 30 tickers no Text widget
- **THEN** `get_tickers()` DEVE retornar todos os 30 tickers (não apenas uma seleção)

### Requirement: Botão toggle "Editar lista de tickers"

O sistema DEVE exibir um botão do tipo toggle (checkbutton com `indicatoron=0`) com o ícone `document-properties.png` entre os botões "Salvar lista de tickers" e "Filtrar" na barra de botões do TickerList.

- Botão marcado (pressed) = modo edição
- Botão desmarcado (released) = modo visualização

#### Scenario: Alternância visual entre modos

- **WHEN** o usuário clica no botão "Editar lista de tickers"
- **THEN** o TickerList DEVE alternar entre modo visualização e modo edição, mostrando o widget correspondente e atualizando o estado do botão

#### Scenario: Botão visível em ambos os modos

- **WHEN** o TickerList está em modo visualização ou edição
- **THEN** o botão "Editar lista de tickers" DEVE estar sempre visível na barra de botões

### Requirement: Botões "Selecionar Todos" e "Desmarcar Todos" no modo visualização

O sistema DEVE exibir dois botões nativos visíveis apenas no modo visualização:
- "Selecionar Todos" com ícone `edit-select-all.png`: marca todos os tickers do Listbox
- "Desmarcar Todos" com ícone `list-remove-all.png`: desmarca todos os tickers do Listbox

Os botões DEVEM estar posicionados entre o label do TickerList e o Listbox.

#### Scenario: Selecionar Todos

- **WHEN** o usuário desmarcou 10 de 30 tickers e clica em "Selecionar Todos"
- **THEN** todos os 30 tickers DEVEM ficar marcados no Listbox

#### Scenario: Desmarcar Todos

- **WHEN** o usuário clica em "Desmarcar Todos" com 30 tickers carregados
- **THEN** nenhum ticker DEVE ficar marcado no Listbox

### Requirement: Transição do modo edição para visualização com preservação de seleção

Ao sair do modo edição (botão toggle desmarcado), o sistema DEVE:
1. Ler os tickers do Text widget
2. Comparar com a lista anterior (antes de entrar em edição)
3. Tickers que já existiam na lista anterior: preservar seu estado de marcação (marcado/desmarcado)
4. Tickers novos (que não estavam na lista anterior): marcar como selecionados
5. Tickers removidos (que estavam na lista anterior mas não estão no Text): desaparecem do Listbox
6. Se a lista de tickers mudou (adições/remoções): disparar uma recarga de dados

#### Scenario: Preservação de seleção após edição

- **WHEN** o usuário está em modo visualização com tickers A, B, C, D marcados e E, F desmarcados, entra em modo edição, adiciona o ticker G, remove o ticker F, e volta ao modo visualização
- **THEN** o Listbox DEVE exibir A, B, C, D, E, G com A, B, C, D, G marcados e E desmarcado; e uma recarga de dados DEVE ser disparada

#### Scenario: Nenhuma mudança dispensa recarga

- **WHEN** o usuário entra em modo edição, não altera a lista, e volta ao modo visualização
- **THEN** a lista de tickers no Listbox DEVE permanecer inalterada e NENHUMA recarga de dados DEVE ser disparada

### Requirement: Lazy refresh de gráficos

O sistema DEVE atualizar os gráficos (VWAP, Quadrantes, Dominância do Pregão na Análise Geral; Dominance Timeline e indicadores textuais na Análise do Ticker) apenas quando o usuário selecionar a respectiva aba manualmente. Alterações na seleção de tickers NÃO DEVEM disparar renderização de gráficos.

#### Scenario: Seleção modificada sem refresh imediato

- **WHEN** o usuário marca/desmarca tickers no Listbox (modo visualização)
- **THEN** os gráficos NÃO DEVEM ser atualizados (apenas o estado interno muda)

#### Scenario: Gráfico atualizado ao selecionar aba da Análise Geral

- **WHEN** o usuário modifica a seleção de tickers e então clica na sub-aba "VWAP" da Análise Geral
- **THEN** o gráfico VWAP DEVE ser renderizado com a seleção atual de tickers

#### Scenario: Indicadores atualizados ao selecionar Análise do Ticker

- **WHEN** o usuário modifica a seleção de tickers e então clica na aba "Análise do Ticker"
- **THEN** o combobox e os indicadores textuais DEVM ser atualizados com a seleção atual
