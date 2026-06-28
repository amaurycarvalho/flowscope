## MODIFIED Requirements

### Requirement: Placeholder para Dominância do Pregão

A sub-aba "Dominância do Pregão" DEVE exibir os indicadores de preço: Range, Range%, Typical Price, Median Price, Weighted Close.

#### Scenario: Exibição dos indicadores de preço

- **WHEN** o usuário seleciona a sub-aba "Dominância do Pregão"
- **THEN** o sistema DEVE exibir uma tabela ou painel com Range, Range%, Typical Price, Median Price e Weighted Close para o ticker selecionado

### Requirement: Placeholder para Fluxo Financeiro

A sub-aba "Fluxo Financeiro" DEVE exibir os indicadores de fluxo: CLV, Money Flow Multiplier, Money Flow Volume, Buying Pressure Index, Selling Pressure Index.

#### Scenario: Exibição dos indicadores de fluxo

- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o sistema DEVE exibir CLV, MFM, MFV acumulado, Buying Pressure e Selling Pressure para o ticker selecionado, em formato textual ou visual

### Requirement: Placeholder para Participação Institucional

A sub-aba "Participação Institucional" DEVE exibir os indicadores de tamanho de negócio: Average Trade Size e Average Financial Ticket.

#### Scenario: Exibição dos indicadores de tamanho de negócio

- **WHEN** o usuário seleciona a sub-aba "Participação Institucional"
- **THEN** o sistema DEVE exibir Average Trade Size e Average Financial Ticket para o ticker selecionado

### Requirement: Placeholder para Eficiência do Movimento

A sub-aba "Eficiência do Movimento" DEVE exibir o indicador Daily Efficiency.

#### Scenario: Exibição do Daily Efficiency

- **WHEN** o usuário seleciona a sub-aba "Eficiência do Movimento"
- **THEN** o sistema DEVE exibir o Daily Efficiency para o ticker selecionado

### Requirement: Placeholder para Resumo Geral

A sub-aba "Resumo Geral" DEVE consolidar todos os indicadores do ticker em uma única visualização.

#### Scenario: Exibição do resumo consolidado

- **WHEN** o usuário seleciona a sub-aba "Resumo Geral"
- **THEN** o sistema DEVE exibir todos os indicadores disponíveis para o ticker selecionado em formato consolidado (tabela ou painel)
