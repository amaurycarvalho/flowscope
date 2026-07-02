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

### Requirement: Gauge horizontal divergente do Daily Money Flow

O sistema DEVE exibir um gauge horizontal divergente centrado em 0, onde o Daily Money Flow do último pregão é representado como uma barra colorida que se estende para a direita (fluxo comprador, verde) ou para a esquerda (fluxo vendedor, vermelho).

#### Scenario: Fluxo comprador exibido à direita

- **WHEN** o Daily Money Flow do último pregão é +R$ 8.100.000
- **THEN** o gauge DEVE exibir uma barra verde à direita do centro, proporcional à magnitude do valor

#### Scenario: Fluxo vendedor exibido à esquerda

- **WHEN** o Daily Money Flow do último pregão é -R$ 3.200.000
- **THEN** o gauge DEVE exibir uma barra vermelha à esquerda do centro, proporcional à magnitude do valor

#### Scenario: Fluxo neutro

- **WHEN** o Daily Money Flow do último pregão é R$ 0
- **THEN** o gauge DEVE exibir apenas o centro, sem barras coloridas

### Requirement: Classificação qualitativa do fluxo financeiro

O sistema DEVE classificar o fluxo financeiro usando score normalizado `score = daily_money_flow / fin_vol` do último pregão, com os seguintes thresholds simétricos:

- `score > +0,15`: "Fluxo Muito Forte" (comprador)
- `+0,08 < score <= +0,15`: "Fluxo Forte"
- `+0,03 < score <= +0,08`: "Fluxo Moderado"
- `+0,01 < score <= +0,03`: "Fluxo Fraco"
- `-0,01 <= score <= +0,01`: "Neutro"
- `-0,03 <= score < -0,01`: "Fluxo Fraco" (vendedor)
- `-0,08 <= score < -0,03`: "Fluxo Moderado"
- `-0,15 <= score < -0,08`: "Fluxo Forte"
- `score < -0,15`: "Fluxo Muito Forte" (vendedor)

#### Scenario: Score +0,12 classifica como Fluxo Forte

- **WHEN** daily_money_flow = +R$ 8.100.000 e fin_vol = R$ 67.500.000 (score = +0,12)
- **THEN** a classificação DEVE ser "Fluxo Forte" com score +0,12

#### Scenario: Score -0,05 classifica como Fluxo Moderado (vendedor)

- **WHEN** daily_money_flow = -R$ 2.500.000 e fin_vol = R$ 50.000.000 (score = -0,05)
- **THEN** a classificação DEVE ser "Fluxo Moderado" com score -0,05

#### Scenario: Score +0,005 classifica como Neutro

- **WHEN** daily_money_flow = +R$ 200.000 e fin_vol = R$ 40.000.000 (score = +0,005)
- **THEN** a classificação DEVE ser "Neutro" com score +0,005

### Requirement: Money Flow Volume acumulado como contexto

O sistema DEVE exibir o Money Flow Volume acumulado do período como texto de contexto no mesmo eixo do gauge principal, com o rótulo "Acum. {N}d: R$ {valor}".

#### Scenario: Acumulado de 7 dias exibido no gauge

- **WHEN** o período tem 7 pregões e money_flow_volume acumulado = +R$ 52.300.000
- **THEN** o texto "Acum. 7d: +R$ 52.300.000" DEVE ser exibido no canto inferior direito do gauge

#### Scenario: Período de 1 dia

- **WHEN** o período tem apenas 1 pregão
- **THEN** o texto DEVE ser "Acum. 1d: R$ {valor}" (não "7d")

### Requirement: Marcador de CLV no gauge principal

O sistema DEVE exibir um marcador visual (triângulo ou linha vertical) sobreposto ao gauge, indicando a posição do CLV do último pregão na escala de -1 a +1.

#### Scenario: CLV +0,81 mostra marcador à direita

- **WHEN** o CLV do último pregão é +0,81
- **THEN** o gauge DEVE exibir um marcador na posição +0,81, próximo ao extremo direito

#### Scenario: CLV -0,32 mostra marcador à esquerda

- **WHEN** o CLV do último pregão é -0,32
- **THEN** o gauge DEVE exibir um marcador na posição -0,32, no lado esquerdo

### Requirement: Barra empilhada de Buying Pressure vs Selling Pressure

O sistema DEVE exibir uma barra horizontal empilhada mostrando a proporção entre Buying Pressure e Selling Pressure do último pregão, com cores verde (compra) e vermelha (venda).

#### Scenario: Buying Pressure 72%, Selling Pressure 28%

- **WHEN** Buying Pressure = 0,72 e Selling Pressure = 0,28
- **THEN** a barra DEVE exibir 72% verde à esquerda e 28% vermelha à direita, com labels "Compra 72%" e "Venda 28%"

#### Scenario: Buying Pressure 100%

- **WHEN** Buying Pressure = 1,0 e Selling Pressure = 0,0
- **THEN** a barra DEVE ser inteiramente verde com label "Compra 100%"

### Requirement: Range Percentual como contexto auxiliar

O sistema DEVE exibir o Range Percentual do último pregão como texto de contexto, indicando a amplitude relativa do dia.

#### Scenario: Range Percentual de 2,5% exibido como contexto

- **WHEN** range_percentual do último pregão = 2,5%
- **THEN** o valor DEVE ser exibido como texto de contexto, ex.: "Range: 2,5%"

### Requirement: Hover tooltip com detalhes do pregão

O sistema DEVE exibir um tooltip ao passar o mouse sobre o gauge principal, mostrando valores numéricos do pregão.

#### Scenario: Mouse sobre o gauge exibe tooltip

- **WHEN** o usuário move o mouse sobre a área do gauge
- **THEN** o tooltip DEVE exibir: Daily Money Flow, Money Flow Volume acumulado, CLV, Score, Classificação, Volume Financeiro, Range Percentual

### Requirement: Summary callback para resumo textual

O sistema DEVE aceitar um `summary_callback` no construtor e invocá-lo durante `update()` com um texto-resumo em português descrevendo o fluxo financeiro do ticker.

#### Scenario: Summary gerado para fluxo comprador forte

- **WHEN** daily_money_flow = +R$ 8.100.000, score = +0,12 (Fluxo Forte), CLV = +0,81, Buying Pressure = 72%
- **THEN** o callback DEVE receber texto contendo "fluxo financeiro comprador forte" e "elevada convicção"

#### Scenario: Summary gerado para fluxo vendedor fraco

- **WHEN** daily_money_flow = -R$ 500.000, score = -0,01 (Neutro), CLV = -0,10, Buying Pressure = 48%
- **THEN** o callback DEVE receber texto contendo "fluxo equilibrado" e "baixa convicção"

### Requirement: Classificador MoneyFlow isolado em módulo próprio

O sistema DEVE implementar o classificador de fluxo financeiro em `src/flowscope/domain/strategies/classifiers/money_flow.py`, seguindo o mesmo padrão de `dominance.py` e `conviction.py`.

#### Scenario: Módulo exporta MoneyFlowClassification e classify_money_flow

- **WHEN** um painel importa `from flowscope.domain.strategies.classifiers.money_flow import classify_money_flow, MoneyFlowClassification`
- **THEN** a função `classify_money_flow(score: float)` DEVE retornar uma `MoneyFlowClassification` com `label`, `short_label`, `color` e `score`

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
