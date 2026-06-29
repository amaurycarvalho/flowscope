## Purpose

Define the per-ticker analysis interface, including ticker selection via TickerList and sub-tabs for price dominance, financial flow, institutional participation, movement efficiency, and a general summary.

## Requirements

### Requirement: Seleção de ticker via TickerList

O sistema DEVE derivar o ticker analisado na aba "Análise do Ticker" a partir da seleção na TickerList (painel direito). O primeiro ticker selecionado no Listbox (por ordem de aparição) DEVE ser usado como ticker atual para todas as sub-abas de indicadores.

#### Scenario: Primeiro ticker selecionado é o analisado

- **WHEN** o usuário carrega dados para PETR4, VALE3, ITUB4 e seleciona VALE3 e ITUB4 no Listbox
- **THEN** a aba "Análise do Ticker" DEVE exibir indicadores para VALE3 (primeiro da ordem de seleção)

#### Scenario: Nenhum ticker selecionado usa o primeiro da lista

- **WHEN** o usuário carrega dados para PETR4, VALE3, ITUB4 e nenhum está selecionado no Listbox
- **THEN** a aba "Análise do Ticker" DEVE exibir indicadores para PETR4 (primeiro da lista completa)

#### Scenario: Lista vazia exibe mensagem

- **WHEN** a lista de tickers está vazia e o usuário navega para "Análise do Ticker"
- **THEN** as sub-abas DEVENDO exibir "Selecione um ticker"

### Requirement: Reordenação das sub-abas

A sub-aba "Evolução da Dominância" DEVE ser a primeira aba no notebook da "Análise do Ticker", antes de "Amplitude de Preço".

#### Scenario: Evolução da Dominância como primeira aba

- **WHEN** o usuário navega para "Análise do Ticker"
- **THEN** a primeira sub-aba DEVE ser "Evolução da Dominância" seguida por "Amplitude de Preço"

### Requirement: Atualização ao trocar seleção

O sistema DEVE atualizar as sub-abas da "Análise do Ticker" quando o usuário alterar a seleção na TickerList, utilizando o mecanismo de lazy refresh existente (via `_charts_dirty` e `_on_ticker_edit`).

#### Scenario: Troca de ticker atualiza abas

- **WHEN** o usuário está na aba "Análise do Ticker > Evolução da Dominância" visualizando PETR4 e clica em VALE3 no Listbox
- **THEN** o gráfico DEVE atualizar para mostrar dados de VALE3

### Requirement: Placeholder para Amplitude de Preço

A sub-aba "Amplitude de Preço" DEVE exibir os indicadores de preço: Range, Range%, Typical Price, Median Price, Weighted Close.

#### Scenario: Exibição dos indicadores de preço

- **WHEN** o usuário seleciona a sub-aba "Amplitude de Preço"
- **THEN** o sistema DEVE exibir Range, Range%, Typical Price, Median Price e Weighted Close para o ticker selecionado

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
