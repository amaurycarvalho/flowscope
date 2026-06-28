## 1. Domain: Base Class e DAG Engine

- [x] 1.1 Criar classe abstrata `IndicatorStrategy` em `domain/strategies/base.py` com `id`, `dependencies`, e método `compute(trades, dep_results)`
- [x] 1.2 Criar `IndicatorEngine` em `domain/engine.py` com `register()`, `execute(trades)`, ordenação topológica (Kahn), validação de ciclos e cache de resultados
- [x] 1.3 Criar `domain/strategies/__init__.py` para exportar todas as strategies

## 2. Domain: Refatorar Indicadores Existentes

- [x] 2.1 Refatorar `VWAP` como `VWAPStrategy` (sem dependências, usando avg_price × fin_instr_qty)
- [x] 2.2 Refatorar `VolumeProfile` como `VolumeProfileStrategy` (sem dependências, usando min/max/fin_vol)
- [x] 2.3 Refatorar `TopTickers` como `TopTickersStrategy` (sem dependências, ranking por fin_vol)

## 3. Domain: Indicadores Escalares — Preço

- [x] 3.1 Implementar `RangeStrategy` — max_price − min_price por trade
- [x] 3.2 Implementar `TypicalPriceStrategy` — (max + min + last) / 3
- [x] 3.3 Implementar `MedianPriceStrategy` — (max + min) / 2
- [x] 3.4 Implementar `WeightedCloseStrategy` — (max + min + 2 × last) / 4

## 4. Domain: Indicadores Escalares — Fluxo e Tamanho

- [x] 4.1 Implementar `CLVStrategy` — ((close − low) − (high − close)) / (high − low)
- [x] 4.2 Implementar `MoneyFlowMultiplierStrategy` — delega ao CLV (alias)
- [x] 4.3 Implementar `BuyingPressureStrategy` — dependência: range
- [x] 4.4 Implementar `SellingPressureStrategy` — dependência: range
- [x] 4.5 Implementar `AverageTradeSizeStrategy` — fin_instr_qty / trades_qty
- [x] 4.6 Implementar `AverageFinancialTicketStrategy` — fin_vol / trades_qty

## 5. Domain: Indicadores Derivados

- [x] 5.1 Implementar `RangePercentualStrategy` — dependência: range; Preço Referência = avg_price
- [x] 5.2 Implementar `DailyEfficiencyStrategy` — dependência: range; |last − avg_price| / range
- [x] 5.3 Implementar `MoneyFlowVolumeStrategy` — dependência: money_flow_multiplier; MFM × fin_vol acumulado
- [x] 5.4 Implementar `FinancialDensityStrategy` — dependência: range; fin_vol / range
- [x] 5.5 Implementar `TradeDensityStrategy` — dependência: range; trades_qty / range
- [x] 5.6 Implementar `VolumeDensityStrategy` — dependência: range; fin_instr_qty / range

## 6. Application: Integração do Engine

- [x] 6.1 Refatorar `AnalyzeTickersUseCase` para receber `IndicatorEngine` via DI e usar `engine.execute()` em vez de chamadas diretas
- [x] 6.2 Remover `calculate_cvd` de `domain/indicators.py` e de todas as importações
- [x] 6.3 Registrar todas as strategies no engine dentro do use case (ou em config)
- [x] 6.4 Remover `AggregatedMetrics` não utilizado ou reativá-lo como schema de saída tipado

## 7. Testes Unitários

- [x] 7.1 Testar `IndicatorEngine`: registro, execução, ordenação topológica, detecção de ciclo, cache
- [x] 7.2 Testar `RangeStrategy` com valores positivos e zero
- [x] 7.3 Testar `CLVStrategy` com fechamento na máxima, mínima e centro
- [x] 7.4 Testar `TypicalPrice`, `MedianPrice`, `WeightedClose` com valores conhecidos
- [x] 7.5 Testar `BuyingPressure` e `SellingPressure` com relação complementar
- [x] 7.6 Testar `AverageTradeSize` e `AverageFinancialTicket` com denominator zero
- [x] 7.7 Testar `RangePercentual` e `DailyEfficiency` com avg_price como Preço Referência
- [x] 7.8 Testar `MoneyFlowVolume` acumulado em múltiplos dias
- [x] 7.9 Testar densidades (`Financial`, `Trade`, `Volume`)
- [x] 7.10 Testar strategies refatoradas (`VWAP`, `VolumeProfile`, `TopTickers`)
- [x] 7.11 Atualizar `AnalyzeTickersUseCase` tests para usar engine mockado
- [x] 7.12 Verificar que `test_indicators.py` existente continua passando (ou é atualizado)

## 8. GUI: População das Abas

- [x] 8.1 Sub-aba "Dominância do Pregão": exibir Range, Range%, Typical Price, Median Price, Weighted Close
- [x] 8.2 Sub-aba "Fluxo Financeiro": exibir CLV, MFM, MFV, Buying/Selling Pressure
- [x] 8.3 Sub-aba "Participação Institucional": exibir Average Trade Size, Average Financial Ticket
- [x] 8.4 Sub-aba "Eficiência do Movimento": exibir Daily Efficiency
- [x] 8.5 Sub-aba "Resumo Geral": consolidar todos os indicadores do ticker
- [x] 8.6 Atualizar OrientationPanel com textos explicativos para cada novo grupo de indicadores
