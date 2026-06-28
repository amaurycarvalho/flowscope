## Purpose

Define the per-ticker analysis interface, including a combobox for ticker selection and placeholder sub-tabs for future development of price dominance, financial flow, institutional participation, movement efficiency, and a general summary.

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

O sistema DEVE exibir uma sub-aba "Dominância do Pregão" vazia na aba "Análise do Ticker", reservada para desenvolvimento futuro de indicadores de dominância de preço por ticker.

#### Scenario: Exibição da sub-aba placeholder

- **WHEN** o usuário seleciona a sub-aba "Dominância do Pregão"
- **THEN** o sistema DEVE exibir uma mensagem "Em desenvolvimento" no espaço do gráfico

### Requirement: Placeholder para Fluxo Financeiro

O sistema DEVE exibir uma sub-aba "Fluxo Financeiro" vazia na aba "Análise do Ticker", reservada para desenvolvimento futuro de indicadores de fluxo de capital.

#### Scenario: Exibição da sub-aba placeholder

- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o sistema DEVE exibir uma mensagem "Em desenvolvimento" no espaço do gráfico

### Requirement: Placeholder para Participação Institucional

O sistema DEVE exibir uma sub-aba "Participação Institucional" vazia na aba "Análise do Ticker", reservada para desenvolvimento futuro de indicadores de atividade institucional.

#### Scenario: Exibição da sub-aba placeholder

- **WHEN** o usuário seleciona a sub-aba "Participação Institucional"
- **THEN** o sistema DEVE exibir uma mensagem "Em desenvolvimento" no espaço do gráfico

### Requirement: Placeholder para Eficiência do Movimento

O sistema DEVE exibir uma sub-aba "Eficiência do Movimento" vazia na aba "Análise do Ticker", reservada para desenvolvimento futuro de indicadores de eficiência de preço.

#### Scenario: Exibição da sub-aba placeholder

- **WHEN** o usuário seleciona a sub-aba "Eficiência do Movimento"
- **THEN** o sistema DEVE exibir uma mensagem "Em desenvolvimento" no espaço do gráfico

### Requirement: Placeholder para Resumo Geral

O sistema DEVE exibir uma sub-aba "Resumo Geral" vazia na aba "Análise do Ticker", reservada para desenvolvimento futuro de um sumário consolidado por ticker.

#### Scenario: Exibição da sub-aba placeholder

- **WHEN** o usuário seleciona a sub-aba "Resumo Geral"
- **THEN** o sistema DEVE exibir uma mensagem "Em desenvolvimento" no espaço do gráfico
