## 1. Domain: Base Class e DAG Engine

- [ ] 1.1 Criar classe abstrata `IndicatorStrategy` em `domain/strategies/base.py` com `id`, `dependencies`, e método `compute(trades, dep_results)`
- [ ] 1.2 Criar `IndicatorEngine` em `domain/engine.py` com `register()`, `execute(trades)`, ordenação topológica (Kahn), validação de ciclos e cache de resultados
- [ ] 1.3 Criar `domain/strategies/__init__.py` para exportar todas as strategies

## 2. Domain: Refatorar Indicadores Existentes

- [ ] 2.1 Refatorar `VWAP` como `VWAPStrategy` (sem dependências, usando avg_price × fin_instr_qty)
- [ ] 2.2 Refatorar `VolumeProfile` como `VolumeProfileStrategy` (sem dependências, usando min/max/fin_vol)
- [ ] 2.3 Refatorar `TopTickers` como `TopTickersStrategy` (sem dependências, ranking por fin_vol)

## 3. Domain: Indicadores Escalares — Preço

- [ ] 3.1 Implementar `RangeStrategy` — max_price − min_price por trade
- [ ] 3.2 Implementar `TypicalPriceStrategy` — (max + min + last) / 3
- [ ] 3.3 Implementar `MedianPriceStrategy` — (max + min) / 2
- [ ] 3.4 Implementar `WeightedCloseStrategy` — (max + min + 2 × last) / 4

## 4. Domain: Indicadores Escalares — Fluxo e Tamanho

- [ ] 4.1 Implementar `CLVStrategy` — ((close − low) − (high − close)) / (high − low)
- [ ] 4.2 Implementar `MoneyFlowMultiplierStrategy` — delega ao CLV (alias)
- [ ] 4.3 Implementar `BuyingPressureStrategy` — dependência: range
- [ ] 4.4 Implementar `SellingPressureStrategy` — dependência: range
- [ ] 4.5 Implementar `AverageTradeSizeStrategy` — fin_instr_qty / trades_qty
- [ ] 4.6 Implementar `AverageFinancialTicketStrategy` — fin_vol / trades_qty

## 5. Domain: Indicadores Derivados

- [ ] 5.1 Implementar `RangePercentualStrategy` — dependência: range; Preço Referência = avg_price
- [ ] 5.2 Implementar `DailyEfficiencyStrategy` — dependência: range; |last − avg_price| / range
- [ ] 5.3 Implementar `MoneyFlowVolumeStrategy` — dependência: money_flow_multiplier; MFM × fin_vol acumulado
- [ ] 5.4 Implementar `FinancialDensityStrategy` — dependência: range; fin_vol / range
- [ ] 5.5 Implementar `TradeDensityStrategy` — dependência: range; trades_qty / range
- [ ] 5.6 Implementar `VolumeDensityStrategy` — dependência: range; fin_instr_qty / range

## 6. Application: Integração do Engine

- [ ] 6.1 Refatorar `AnalyzeTickersUseCase` para receber `IndicatorEngine` via DI e usar `engine.execute()` em vez de chamadas diretas
- [ ] 6.2 Remover `calculate_cvd` de `domain/indicators.py` e de todas as importações
- [ ] 6.3 Registrar todas as strategies no engine dentro do use case (ou em config)
- [ ] 6.4 Remover `AggregatedMetrics` não utilizado ou reativá-lo como schema de saída tipado

## 7. Testes Unitários

- [ ] 7.1 Testar `IndicatorEngine`: registro, execução, ordenação topológica, detecção de ciclo, cache
- [ ] 7.2 Testar `RangeStrategy` com valores positivos e zero
- [ ] 7.3 Testar `CLVStrategy` com fechamento na máxima, mínima e centro
- [ ] 7.4 Testar `TypicalPrice`, `MedianPrice`, `WeightedClose` com valores conhecidos
- [ ] 7.5 Testar `BuyingPressure` e `SellingPressure` com relação complementar
- [ ] 7.6 Testar `AverageTradeSize` e `AverageFinancialTicket` com denominator zero
- [ ] 7.7 Testar `RangePercentual` e `DailyEfficiency` com avg_price como Preço Referência
- [ ] 7.8 Testar `MoneyFlowVolume` acumulado em múltiplos dias
- [ ] 7.9 Testar densidades (`Financial`, `Trade`, `Volume`)
- [ ] 7.10 Testar strategies refatoradas (`VWAP`, `VolumeProfile`, `TopTickers`)
- [ ] 7.11 Atualizar `AnalyzeTickersUseCase` tests para usar engine mockado
- [ ] 7.12 Verificar que `test_indicators.py` existente continua passando (ou é atualizado)

## 8. GUI: População das Abas

- [ ] 8.1 Sub-aba "Dominância do Pregão": exibir Range, Range%, Typical Price, Median Price, Weighted Close
- [ ] 8.2 Sub-aba "Fluxo Financeiro": exibir CLV, MFM, MFV, Buying/Selling Pressure
- [ ] 8.3 Sub-aba "Participação Institucional": exibir Average Trade Size, Average Financial Ticket
- [ ] 8.4 Sub-aba "Eficiência do Movimento": exibir Daily Efficiency
- [ ] 8.5 Sub-aba "Resumo Geral": consolidar todos os indicadores do ticker
- [ ] 8.6 Atualizar OrientationPanel com textos explicativos para cada novo grupo de indicadores
