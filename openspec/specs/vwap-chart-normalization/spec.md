## Purpose

Define the normalization of the VWAP chart Y-axis to display percentage deviation from VWAP, enabling visual comparison across tickers with different absolute price scales.

## Requirements

### Requirement: Normalização do eixo Y para desvio percentual do VWAP

O sistema DEVE normalizar o eixo Y do gráfico VWAP para exibir `(preço - VWAP_período) / VWAP_período × 100` em vez de preço absoluto. Todos os elementos visuais (violino, barra de MinPric/MaxPric, scatter de LastPric) DEVEM usar essa escala normalizada. O VWAP de cada ticker DEVE ser representado como 0% (linha de base horizontal tracejada).

#### Scenario: Exibição do violin plot com eixo Y normalizado

- **WHEN** dados de múltiplos tickers são carregados e a sub-aba VWAP está selecionada
- **THEN** o eixo Y DEVE exibir o desvio percentual em relação ao VWAP de cada ticker, com o VWAP em 0%, valores positivos acima (preço > VWAP) e valores negativos abaixo (preço < VWAP)

#### Scenario: Limites simétricos do eixo Y

- **WHEN** o gráfico é renderizado
- **THEN** os limites inferior e superior do eixo Y DEVEM ser simétricos em torno de 0%, com margem de 10% para o valor absoluto máximo

#### Scenario: Linha de base do VWAP

- **WHEN** o gráfico é renderizado
- **THEN** uma linha horizontal tracejada DEVE ser exibida em Y = 0% representando a referência do VWAP

### Requirement: Tooltip com diferença percentual e valor absoluto

O hover sobre o violino de um ticker DEVE exibir o ticker, o valor do VWAP absoluto (R$), a faixa de diferença percentual (mín e máx), a diferença percentual do LastPric, e o volume total.

#### Scenario: Hover sobre violino com dados normalizados

- **WHEN** o usuário passa o mouse sobre o violino de um ticker
- **THEN** o tooltip DEVE mostrar: ticker, "VWAP: R$ X.XX", "Δ Máx: +X.XX% / Mín: -X.XX%", "LastPric: +X.XX%" e "Volume: X"

### Requirement: Bucket size adaptado para escala percentual

O sistema DEVE estimar o bucket size para o histograma de preços usando a escala percentual em vez de preço absoluto.

#### Scenario: Bucket size para range estreito

- **WHEN** o range percentual dos dados ≤ 0.5%
- **THEN** o bucket size DEVE ser 0.01%

#### Scenario: Bucket size para range moderado

- **WHEN** o range percentual dos dados está entre 0.5% e 2%
- **THEN** o bucket size DEVE ser 0.05%

#### Scenario: Bucket size para range largo

- **WHEN** o range percentual dos dados > 10%
- **THEN** o bucket size DEVE ser 0.50%

### Requirement: Barra MinPric–MaxPric com vlines

O sistema DEVE usar `ax.vlines()` para desenhar a barra de alcance MinPric–MaxPric em vez de `ax.errorbar()`, para tratar corretamente casos onde MinPric e MaxPric estão ambos do mesmo lado do VWAP.

#### Scenario: Barra exibida com vlines

- **WHEN** o gráfico é renderizado
- **THEN** o sistema DEVE usar `ax.vlines()` para desenhar uma barra vertical de (MinPric - VWAP) / VWAP × 100 até (MaxPric - VWAP) / VWAP × 100 com um marcador em 0% representando o VWAP

#### Scenario: MinPric acima do VWAP (bullish extremo)

- **WHEN** o menor MinPric do período é maior que o VWAP
- **THEN** a barra DEVE ser exibida inteiramente na região positiva (acima de 0%) sem truncamento
