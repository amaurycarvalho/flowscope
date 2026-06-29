## Purpose

Define the Dominance Ranking panel — a cross-sectional visualization in the Análise Geral tab that ranks all tickers by their CLV (Close Location Value) for the most recent trading session.

## Requirements

### Requirement: Ranking de tickers por CLV (DR101)

O sistema DEVE exibir um gráfico de barras horizontais divergentes onde cada linha representa um ticker, ordenado pelo CLV do último pregão disponível.

#### Scenario: Ordenação decrescente por CLV

- **WHEN** o painel é carregado com dados de 5 tickers
- **THEN** os tickers DEVEM ser exibidos em ordem decrescente de CLV, do mais comprador (topo) ao mais vendedor (base)

#### Scenario: Ticker sem CLV

- **WHEN** um ticker não possui dados de CLV para o período
- **THEN** o ticker DEVE ser exibido na posição correspondente a CLV = 0, com barra de comprimento zero e cor cinza

### Requirement: Codificação visual das barras (DR102)

O sistema DEVE codificar visualmente dominância, intensidade e classificação qualitativa em cada barra.

#### Scenario: Direção da barra

- **WHEN** CLV > 0
- **THEN** a barra DEVE se estender para a direita (compradores)
- **WHEN** CLV < 0
- **THEN** a barra DEVE se estender para a esquerda (vendedores)

#### Scenario: Comprimento da barra

- **WHEN** |CLV| = 0.8
- **THEN** a barra DEVE ter o dobro do comprimento de uma barra com |CLV| = 0.4

#### Scenario: Cor da barra

- **WHEN** |CLV| ≥ 0.70
- **THEN** a barra DEVE usar a cor mais intensa da escala (verde escuro para compra, vermelho escuro para venda)
- **WHEN** |CLV| ≤ 0.15
- **THEN** a barra DEVE usar cinza
- **WHEN** 0.15 < |CLV| < 0.70
- **THEN** a barra DEVE usar uma cor intermediária proporcional à magnitude

#### Scenario: Espessura uniforme

- **WHEN** duas barras têm o mesmo CLV mas Money Flow Volume diferente
- **THEN** ambas DEVEM ter a mesma espessura

### Requirement: Indicador de Money Flow Volume (DR103)

O sistema DEVE exibir um marcador na extremidade de cada barra cujo tamanho representa o Money Flow Volume acumulado do período para aquele ticker.

#### Scenario: Marcador proporcional ao MFV

- **WHEN** um ticker tem MFV = R$ 10M e outro MFV = R$ 1M
- **THEN** o tamanho do marcador do primeiro DEVE ser maior que o do segundo

#### Scenario: MFV zero ou negativo

- **WHEN** MFV = 0 ou não disponível
- **THEN** o marcador NÃO DEVE ser exibido para aquele ticker

### Requirement: Tooltip informativo (DR104)

O sistema DEVE exibir um tooltip ao passar o mouse sobre cada barra ou marcador, com detalhes do ticker.

#### Scenario: Tooltip com dados completos

- **WHEN** o usuário passa o mouse sobre uma barra
- **THEN** o tooltip DEVE mostrar: ticker, CLV, classificação de dominância, Money Flow Volume acumulado, e data do último pregão

### Requirement: Eixos e rótulos (DR105)

O sistema DEVE exibir eixos e rótulos que tornem o gráfico auto-explicativo.

#### Scenario: Eixo de dominância

- **WHEN** o gráfico é renderizado
- **THEN** DEVE haver uma linha vertical central em CLV = 0 com rótulos "Compradores" à direita e "Vendedores" à esquerda
- **THEN** DEVE haver marcações em −1, 0, +1 no eixo horizontal

### Requirement: Período consistente (DR106)

O painel DEVE utilizar o mesmo conjunto de datas dos demais painéis temporais (Quadrantes, etc.), determinado pela função `fibonacci_dates`.

#### Scenario: Mesmas datas dos quadrantes

- **WHEN** o usuário carrega dados para uma data de referência
- **THEN** o painel DEVE usar as mesmas datas que o Quadrant Chart para determinar o último pregão de cada ticker
