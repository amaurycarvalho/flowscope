## MODIFIED Requirements

### Requirement: Gráfico de distribuição de preços VWAP
O sistema DEVE exibir um violin plot horizontal com o ticker no eixo X e o valor do TradAvrgPric no eixo Y. A largura do violino em cada faixa de preço DEVE ser proporcional à soma de FinInstrmQty para aquele ticker em todo o período. Sobreposto ao violin plot, DEVE haver:
- Um errorbar exibindo o VWAP geral como ponto central, o menor MinPric do período como limite inferior e o maior MaxPric como limite superior
- Um scatter plot destacando o LastPric de cada ticker referente à data mais recente do período

#### Scenario: Exibição do violin plot com errorbar e scatter
- **WHEN** dados de múltiplos tickers são carregados e o gráfico VWAP está selecionado
- **THEN** o sistema DEVE exibir um violin plot horizontal com perfil de volume (largura ∝ Σ FinInstrMty por bucket de preço), errorbar (VWAP, MinPric, MaxPric) e scatter (LastPric da data mais recente)

#### Scenario: Ticker com dados de um único dia
- **WHEN** um ticker possui dados em apenas 1 dia
- **THEN** o violin plot DEVE exibir uma forma estreita centrada no TradAvrgPric, com errorbar mostrando VWAP = TradAvrgPric e MinPric = MaxPric

#### Scenario: Sem dados para exibir
- **WHEN** não há dados carregados ou o filtro resulta em lista vazia
- **THEN** o sistema DEVE exibir uma mensagem "Nenhum ticker corresponde ao filtro."

### Requirement: Campo multilinha de seleção de tickers
_(Sem alterações — requisito permanece o mesmo)_
