## MODIFIED Requirements

### Requirement: Gráfico de distribuição de preços VWAP

O sistema DEVE exibir um violin plot horizontal com o ticker no eixo X e o valor do desvio percentual do TradAvrgPric em relação ao VWAP no eixo Y, calculado como `(TradAvrgPric - VWAP) / VWAP × 100`. A largura do violino em cada faixa DEVE ser proporcional à soma de FinInstrmQty para aquele ticker em todo o período. Sobreposto ao violin plot, DEVE haver:
- Uma barra vertical (`vlines`) do menor MinPric ao maior MaxPric, normalizados pelo VWAP, com um marcador em 0% indicando o VWAP
- Um scatter plot destacando o LastPric de cada ticker normalizado pelo VWAP, referente à data mais recente do período
- Uma linha horizontal tracejada em Y = 0% representando o VWAP

O eixo Y DEVE exibir o rótulo "Diferença do VWAP (%)" e os limites DEVEM ser simétricos em torno de 0%.

#### Scenario: Exibição do violin plot com eixo normalizado

- **WHEN** dados de múltiplos tickers são carregados e a sub-aba VWAP está selecionada
- **THEN** o sistema DEVE exibir um violin plot horizontal com perfil de volume (largura ∝ Σ FinInstrMty por bucket), barra vertical vlines (MinPric–MaxPric normalizados, marcador VWAP em 0%), scatter (LastPric normalizado), e linha tracejada em Y = 0%

#### Scenario: Ticker com dados de um único dia

- **WHEN** um ticker possui dados em apenas 1 dia
- **THEN** o violin plot DEVE exibir uma forma estreita centrada em 0% (TradAvrgPric = VWAP), com barra vertical mostrando MinPric = MaxPric normalizados e VWAP = TradAvrgPric em 0%

#### Scenario: Sem dados para exibir

- **WHEN** não há dados carregados ou o filtro resulta em lista vazia
- **THEN** o sistema DEVE exibir uma mensagem "Nenhum ticker corresponde ao filtro."
