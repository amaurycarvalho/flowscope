## Purpose

Define the quadrant chart visualization panel that classifies assets based on CLV (X axis), VWAP Distance (Y axis), and trading volume (bubble size).

## Requirements

### Requirement: Exibição do gráfico de dispersão bidimensional

O sistema DEVE exibir um gráfico de dispersão (scatter plot) na sub-aba "Quadrantes" da "Análise Geral", onde cada ativo é representado por uma bolha posicionada segundo suas coordenadas CLV (eixo X) e VWAP Distance (eixo Y).

#### Scenario: Gráfico exibido com dados carregados

- **WHEN** o usuário carrega dados e seleciona a sub-aba "Quadrantes"
- **THEN** o gráfico DEVE exibir uma bolha para cada ticker, com tooltip ao passar o mouse

#### Scenario: Gráfico vazio sem dados

- **WHEN** não há dados carregados
- **THEN** o gráfico DEVE exibir uma mensagem "Nenhum dado disponível." centralizada

### Requirement: Coordenada X — CLV

O sistema DEVE posicionar cada bolha no eixo X usando o valor de CLV do último dia disponível para aquele ticker, no intervalo [-1, +1].

#### Scenario: CLV = 0 posicionado no centro

- **WHEN** um ticker tem CLV = 0 no último dia
- **THEN** a bolha DEVE ser posicionada em X = 0

#### Scenario: CLV = +1 posicionado à direita

- **WHEN** um ticker tem CLV = 1 no último dia
- **THEN** a bolha DEVE ser posicionada em X = 1

### Requirement: Coordenada Y — VWAP Distance

O sistema DEVE posicionar cada bolha no eixo Y usando o valor de `vwap_distance` do último dia disponível, em percentual.

#### Scenario: VWAP Distance = +2.5%

- **WHEN** um ticker tem vwap_distance = +0.025 no último dia
- **THEN** a bolha DEVE ser posicionada em Y = +2.5%

### Requirement: Tamanho da bolha proporcional a sqrt(fin_instr_qty)

O sistema DEVE dimensionar o raio de cada bolha como `sqrt(fin_instr_qty)` do último dia, normalizado para caber no gráfico sem sobreposição excessiva.

#### Scenario: Bolha maior para ativo com maior volume

- **WHEN** PETR4 tem fin_instr_qty = 20.000.000 e ticker A tem fin_instr_qty = 100.000
- **THEN** a bolha de PETR4 DEVE ser visivelmente maior que a de ticker A, com proporção `sqrt(200) : sqrt(1)` ≈ 14:1

### Requirement: Cor da bolha por CLV com colormap divergente

O sistema DEVE colorir cada bolha usando um colormap divergente contínuo (RdYlGn) mapeando CLV de -1 (vermelho) a +1 (verde), com CLV = 0 em amarelo.

#### Scenario: CLV positivo em verde

- **WHEN** um ticker tem CLV = 0.8
- **THEN** a bolha DEVE ser exibida em tom de verde

#### Scenario: CLV negativo em vermelho

- **WHEN** um ticker tem CLV = -0.6
- **THEN** a bolha DEVE ser exibida em tom de vermelho

#### Scenario: CLV próximo de zero em amarelo

- **WHEN** um ticker tem CLV = 0.05
- **THEN** a bolha DEVE ser exibida em tom de amarelo/esverdeado claro

### Requirement: Setas de trajetória temporal (quiver)

O sistema DEVE exibir setas (quiver) conectando os dias anteriores de cada ticker, convergindo para a bolha do dia mais recente. A cauda representa o dia anterior e a ponta o dia atual, permitindo visualizar a evolução temporal.

#### Scenario: Ativo com 3 dias de dados

- **WHEN** um ticker possui dados em 3 dias (D1, D2, D3)
- **THEN** o sistema DEVE exibir duas setas: D1→D2 e D2→D3, com a bolha em D3

#### Scenario: Ativo com apenas 1 dia

- **WHEN** um ticker possui dados em apenas 1 dia
- **THEN** o sistema DEVE exibir apenas a bolha, sem setas

### Requirement: Linhas centrais dos quadrantes

O sistema DEVE exibir linhas de referência em X = 0 e Y = 0 formando quatro quadrantes (Q1, Q2, Q3, Q4).

#### Scenario: Linhas centrais visíveis

- **WHEN** o gráfico é renderizado
- **THEN** DEVE haver uma linha vertical tracejada em X = 0 e uma linha horizontal tracejada em Y = 0

### Requirement: Tooltip ao passar o mouse

O sistema DEVE exibir um tooltip ao passar o mouse sobre uma bolha, contendo: ticker, data, CLV, VWAP Distance (%), e fin_instr_qty.

#### Scenario: Hover sobre bolha

- **WHEN** o usuário passa o mouse sobre uma bolha
- **THEN** um tooltip DEVE aparecer com as informações do ticker

### Requirement: Legendas do gráfico

O sistema DEVE exibir legenda indicando que o eixo X representa CLV (Close Location Value) e o eixo Y representa desvio do VWAP (%).

#### Scenario: Rótulos dos eixos

- **WHEN** o gráfico é renderizado
- **THEN** o eixo X DEVE ter o rótulo "CLV" e o eixo Y "Desvio do VWAP (%)"

### Requirement: Resumo textual automático no OrientationPanel

O sistema DEVE gerar um resumo textual da distribuição das bolhas entre os quadrantes e concatená-lo ao texto de orientação do painel, atualizando-o sempre que o gráfico for renderizado.

#### Scenario: Maioria em Q1

- **WHEN** mais de 50% das bolhas estão em Q1 (CLV > 0, VWAP Distance > 0)
- **THEN** o resumo DEVE incluir a frase "predominância de ativos com fechamento acima do VWAP e forte pressão compradora"

#### Scenario: Maioria em Q3

- **WHEN** mais de 50% das bolhas estão em Q3 (CLV < 0, VWAP Distance < 0)
- **THEN** o resumo DEVE incluir a frase "maioria dos ativos encerrou abaixo do VWAP com pressão vendedora dominante"

#### Scenario: Predomínio em Q2

- **WHEN** mais de 40% das bolhas estão em Q2 (CLV < 0, VWAP Distance > 0) e nenhum quadrante isolado tem maioria
- **THEN** o resumo DEVE mencionar "enfraquecimento no fechamento apesar de preço acima do VWAP, sugerindo realização de lucros"

#### Scenario: Predomínio em Q4

- **WHEN** mais de 40% das bolhas estão em Q4 (CLV > 0, VWAP Distance < 0) e nenhum quadrante isolado tem maioria
- **THEN** o resumo DEVE mencionar "possível início de recuperação, ainda sem confirmação"
