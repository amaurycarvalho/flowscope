## Why

A especificação técnica FS001–FS403 define ~20 indicadores diários calculáveis exclusivamente com dados consolidados da B3. Atualmente apenas 4 estão implementados (VWAP, CVD, Volume Profile, Top Tickers). Implementar o conjunto completo desbloqueia análise multidimensional de pregão sem depender de dados intraday.

## What Changes

- **BREAKING**: Remove indicador CVD (substituído por Money Flow Volume, que usa CLV contínuo em vez de sinal binário)
- **BREAKING**: Define Preço Referência = avg_price (desambigua FS003 e FS301)
- Implementa 15 novos indicadores da especificação FS001–FS403
- Cria motor de cálculo baseado em DAG: cada indicador é uma estratégia independente que declara suas dependências; o motor resolve ordem de execução automaticamente, elimina recomputações e facilita testes
- Refatora indicadores existentes (VWAP, Volume Profile, Top Tickers) para o novo padrão de estratégia
- Atualiza a GUI para exibir os novos indicadores nas abas existentes

## Capabilities

### New Capabilities

- `price-range-indicators`: Range, Range%, Typical Price, Median Price, Weighted Close
- `flow-indicators`: CLV (Close Location Value), Money Flow Multiplier, Money Flow Volume, Buying/Selling Pressure
- `efficiency-indicators`: Daily Efficiency
- `density-indicators`: Financial Density, Trade Density, Volume Density
- `trade-size-indicators`: Average Trade Size, Average Financial Ticket
- `dag-engine`: Motor de cálculo que resolve dependências entre indicadores via grafo acíclico (DAG), executa na ordem correta e evita recomputações

### Modified Capabilities

- `volume-indicators`: Remove requisito de CVD, adiciona requisito de Money Flow Volume
- `ticker-analysis`: Substitui abas placeholder por visualizações reais dos novos indicadores
- `gui-interface`: Adiciona exibição dos novos indicadores no OrientationPanel e nas abas

## Impact

- `src/flowscope/domain/indicators.py`: Refatorado — cada indicador vira uma classe Strategy
- `src/flowscope/domain/`: Novo módulo `engine.py` com o resolvedor DAG
- `src/flowscope/domain/`: Novo módulo `strategies/` com implementações individuais
- `src/flowscope/domain/entities.py`: `AggregatedMetrics` passa a ser usado de fato
- `src/flowscope/application/use_cases.py`: `AnalyzeTickersUseCase` usa o engine DAG
- `src/flowscope/presentation/gui/`: Abas da GUI são populadas com novos indicadores
- `tests/`: Testes unitários para cada Strategy + testes do engine DAG
- Nenhuma nova dependência externa (tudo usa stdlib + Decimal)
