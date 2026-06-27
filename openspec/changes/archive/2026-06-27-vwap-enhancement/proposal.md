## Why

O VWAP atual usa NtlFinVol (volume financeiro em R$) como peso, mas o cálculo conceitualmente correto deve usar FinInstrmQty (quantidade de instrumentos negociados), que reflete o número de ações/contratos. Além disso, o gráfico atual (bar chart do VWAP periódico) não mostra a distribuição de preços ao longo do período — informação valiosa para análise de fluxo de ordens.

## What Changes

- **BREAKING**: VWAP geral passa a ser calculado como `Σ(TradAvrgPric × FinInstrmQty) / Σ(FinInstrmQty)` em todo o app (peso por quantidade, não por volume financeiro)
- VWAP Histogram (bar chart) substituído por um violin plot com perfil de volume horizontal, errorbar (VWAP, MinPric, MaxPric) e scatter (LastPric da data mais recente)
- `AnalyzeTickersUseCase` modificado para retornar dados diários adicionais (FinInstrmQty, MinPric, MaxPric, LastPric) necessários ao novo gráfico
- Tooltip do Radiobutton VWAP atualizada com descrição completa

## Capabilities

### New Capabilities

_(Nenhuma — as alterações modificam capacidades existentes)_

### Modified Capabilities

- `volume-indicators`: Requisito de cálculo do VWAP alterado — peso muda de NtlFinVol para FinInstrmQty
- `gui-interface`: Gráfico VWAP substituído por violin plot com errorbar + scatter; dados adicionais retornados pelo use case

## Impact

- **Target**: Release 0.1.0
- `src/flowscope/domain/indicators.py`: `calculate_vwap()` — alterar peso de `fin_vol` para `fin_instr_qty`
- `src/flowscope/domain/entities.py`: Sem alterações (os campos já existem)
- `src/flowscope/application/use_cases.py`: `AnalyzeTickersUseCase.execute()` — incluir `daily_data` (avg_price, fin_instr_qty, min_price, max_price, last_price por data) no resultado
- `src/flowscope/presentation/gui/charts/vwap_hist.py`: Reescrever `VWAPHistChart` como violin plot com errorbar e scatter
- `src/flowscope/presentation/gui/app.py`: Tooltip do Radiobutton VWAP, título do gráfico
- Testes: `test_domain/test_indicators.py` — atualizar valores esperados do VWAP
