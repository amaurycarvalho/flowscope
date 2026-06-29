## MODIFIED Requirements

### Requirement: Contagem de tickers

O sistema DEVE exibir um label ao lado do campo de tickers indicando a quantidade total ou selecionada, dependendo do modo atual:
- Modo visualização: "Tickers (N)" com N = total de tickers no Listbox; "Exibindo M de N ativos" quando M < N selecionados
- Modo edição: "Tickers (N)" com N = total de tickers no Text widget

#### Scenario: Label no modo visualização com todos marcados

- **WHEN** dados de 37 tickers são carregados e todos estão marcados no Listbox
- **THEN** o label DEVE mostrar "Tickers (37)"

#### Scenario: Label no modo visualização com seleção parcial

- **WHEN** o usuário desmarca 10 dos 37 tickers no Listbox
- **THEN** o label DEVE mostrar "Exibindo 27 de 37 ativos"

#### Scenario: Label no modo edição

- **WHEN** o usuário alterna para modo edição com 37 tickers carregados
- **THEN** o label DEVE mostrar "Tickers (37)"

### Requirement: Comboboxes de ticker da Análise Geral removidos

Os comboboxes de seleção de ticker nas abas VWAP, Quadrantes e Dominância do Pregão foram removidos. A seleção de tickers é feita exclusivamente pelo Listbox no TickerList. Todos os gráficos da Análise Geral usam os tickers selecionados no Listbox.

A regra de exibição de setas (quiver) no gráfico de Quadrantes é mantida: setas são exibidas quando apenas 1 ticker está selecionado no Listbox.

#### Scenario: VWAP exibe todos os tickers selecionados

- **WHEN** o usuário seleciona 5 tickers no Listbox e navega para a aba VWAP
- **THEN** o histograma VWAP DEVE exibir dados para todos os 5 tickers

#### Scenario: Quadrantes com setas quando 1 ticker selecionado

- **WHEN** o usuário seleciona exatamente 1 ticker no Listbox e navega para a aba Quadrantes
- **THEN** o gráfico de quadrantes DEVE exibir setas (quiver) para o ticker selecionado

#### Scenario: Quadrantes sem setas quando múltiplos tickers

- **WHEN** o usuário seleciona 3 tickers no Listbox e navega para a aba Quadrantes
- **THEN** o gráfico de quadrantes DEVE exibir pontos sem setas

### Requirement: Carga de dados usa todos os tickers da lista

O método `_ensure_tickers()` DEVE usar `get_all_listbox_tickers()` para obter a lista completa de tickers, independentemente de quais estão marcados. A marcação no Listbox só afeta a exibição nos painéis, não a carga de dados.

#### Scenario: Carga com tickers desmarcados

- **WHEN** o usuário tem 30 tickers no Listbox, desmarca 10, e clica em "Carregar"
- **THEN** os dados DEVEM ser carregados para todos os 30 tickers (não apenas os 20 marcados)

### Requirement: Order of buttons

A barra de botões do TickerList DEVE exibir os botões na seguinte ordem, da esquerda para a direita:

`[Carregar] [Salvar] |sep| [Editar] [Selecionar Todos] [Desmarcar Todos] |sep| [IBOV] [IDIV] [IFIX]`

Onde `|sep|` são separadores verticais. Os botões "Selecionar Todos" e "Desmarcar Todos" DEVEM estar visíveis apenas no modo visualização.
