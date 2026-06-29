## Purpose

Define the Dominance Timeline panel — a time-series visualization in the Análise do Ticker tab that shows the evolution of buyer/seller dominance for a single ticker across multiple trading sessions.

## Requirements

### Requirement: Gráfico temporal de CLV (DT201)

O sistema DEVE exibir um gráfico de barras horizontais divergentes onde cada linha representa uma data de pregão para o ticker selecionado.

#### Scenario: Uma barra por data

- **WHEN** o painel é carregado com dados de 5 pregões para PETR4
- **THEN** DEVEM ser exibidas 5 barras, uma por data, ordenadas cronologicamente da mais antiga (topo) à mais recente (base)

#### Scenario: Ordenação cronológica

- **WHEN** as datas disponíveis são 20/06, 23/06, 24/06, 25/06, 26/06
- **THEN** a barra de 20/06 DEVE estar no topo e a de 26/06 na base

### Requirement: Codificação visual (DT202)

O sistema DEVE aplicar a mesma codificação visual do ranking (direção, comprimento, cor, espessura uniforme), com círculo representando o Money Flow diário.

#### Scenario: Direção da barra

- **WHEN** CLV > 0 para uma data
- **THEN** a barra DEVE se estender para a direita
- **WHEN** CLV < 0 para uma data
- **THEN** a barra DEVE se estender para a esquerda

#### Scenario: Cor por classificação

- **WHEN** |CLV| ≥ 0.70
- **THEN** a barra DEVE usar a cor mais intensa (verde escuro / vermelho escuro)
- **WHEN** CLV entre −0.15 e +0.15
- **THEN** a barra DEVE ser cinza
- **WHEN** valores intermediários
- **THEN** a barra DEVE usar cor proporcional à magnitude

### Requirement: Círculo de Money Flow diário (DT203)

O sistema DEVE exibir um círculo na extremidade da barra cujo diâmetro representa o Money Flow diário (CLV × FinVol daquele pregão), não o MFV acumulado.

#### Scenario: MFV diário proporcional

- **WHEN** um pregão tem CLV = 0.5 e FinVol = R$ 2M
- **THEN** o círculo DEVE corresponder a MFV_diário = R$ 1M
- **WHEN** outro pregão tem CLV = 0.5 e FinVol = R$ 200K
- **THEN** o círculo DO primeiro DEVE ser maior que o do segundo

### Requirement: Overlay de Daily Efficiency (DT204)

O sistema DEVE exibir a Daily Efficiency como uma linha ou marcador sobreposto ao gráfico, em escala independente.

#### Scenario: Linha de eficiência

- **WHEN** o gráfico é renderizado
- **THEN** DEVE haver uma linha conectando os valores de Daily Efficiency de cada pregão, plotada em um eixo secundário (0 a 1) ou como marcador visual distinto

#### Scenario: Tooltip da eficiência

- **WHEN** o usuário passa o mouse sobre um ponto da linha de eficiência
- **THEN** o tooltip DEVE mostrar: data, Daily Efficiency, e classificação de convicção

### Requirement: Resumo lateral (DT205)

O sistema DEVE exibir um resumo textual ao lado do gráfico com a classificação do último pregão e um KPI agregado do período.

#### Scenario: Classificação do último pregão

- **WHEN** o gráfico é renderizado para um ticker com dados
- **THEN** DEVE ser exibido: "Dominância: <classificação> (<CLV>)", "Convicção: <classificação> (<Efficiency>)", "Fluxo: <valor>"

#### Scenario: KPI de pregões compradores

- **WHEN** o período contém 10 pregões, dos quais 6 têm CLV positivo
- **THEN** DEVE ser exibido "Pregões Compradores: 60%"

### Requirement: Tooltip por barra (DT206)

O sistema DEVE exibir tooltip ao passar o mouse sobre cada barra ou círculo.

#### Scenario: Tooltip completo

- **WHEN** o usuário passa o mouse sobre uma barra de uma data específica
- **THEN** o tooltip DEVE mostrar: data, CLV, classificação de dominância, Daily Efficiency, classificação de convicção, Money Flow diário
