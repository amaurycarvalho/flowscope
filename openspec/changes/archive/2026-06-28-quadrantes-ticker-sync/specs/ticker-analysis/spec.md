## ADDED Requirements

### Requirement: Sincronização bidirecional de comboboxes

O sistema DEVE sincronizar o combobox "Análise do Ticker" com o combobox de seleção de ticker do gráfico de quadrantes. As mudanças em um combobox DEVEM refletir no outro.

#### Scenario: Ticker selecionado nos Quadrantes reflete na Análise do Ticker
- **WHEN** o usuário seleciona "PETR4" no combobox do Quadrantes
- **THEN** o combobox "Análise do Ticker" DEVE exibir "PETR4" como valor selecionado

#### Scenario: Ticker selecionado na Análise do Ticker reflete nos Quadrantes
- **WHEN** o usuário seleciona "VALE3" no combobox "Análise do Ticker"
- **THEN** o combobox do Quadrantes DEVE exibir "VALE3" como valor selecionado

#### Scenario: "Todos" nos Quadrantes limpa a Análise do Ticker
- **WHEN** o usuário seleciona "Todos" no combobox do Quadrantes
- **THEN** o combobox "Análise do Ticker" DEVE ficar vazio (nenhum ticker selecionado)

### Requirement: Sincronização sem navegação automática de aba

A sincronização do valor entre comboboxes NÃO DEVE forçar a navegação para a aba correspondente. O conteúdo da aba "Análise do Ticker" DEVE ser atualizado apenas quando o usuário navegar para ela explicitamente.

#### Scenario: Sincronização preserva aba ativa
- **WHEN** o usuário está na aba "Análise Geral > Quadrantes" e seleciona um ticker
- **THEN** o combobox da Análise do Ticker é atualizado, MAS a aba ativa permanece "Análise Geral > Quadrantes"
