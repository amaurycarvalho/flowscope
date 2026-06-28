## Purpose

Define the per-ticker analysis interface, including a combobox for ticker selection and sub-tabs for price dominance, financial flow, institutional participation, movement efficiency, and a general summary.

## Requirements

### Requirement: Seleção de ticker para análise individual

O sistema DEVE fornecer um combobox na aba "Análise do Ticker" para selecionar um ticker específico dentre os carregados no momento. O combobox DEVE ser populado com os tickers da lista principal (TickerList) e atualizado automaticamente quando a lista for modificada.

#### Scenario: Combobox populado após carregamento

- **WHEN** o usuário carrega dados para 37 tickers
- **THEN** o combobox DEVE conter 37 itens listando os tickers carregados

#### Scenario: Combobox atualizado após filtro

- **WHEN** o usuário filtra a lista para 15 tickers
- **THEN** o combobox DEVE conter apenas os 15 tickers do filtro ativo

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
