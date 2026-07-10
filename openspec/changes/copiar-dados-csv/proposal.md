## Why

O botão "Copiar Dados" atual copia apenas `Ticker;VWAP;MoneyFlowVolume` — indicadores agregados que não permitem ao usuário verificar manualmente a análise exportando os dados brutos para uma planilha. O usuário precisa conferir se os cálculos dos indicadores estão corretos comparando com os dados originais da B3.

## What Changes

- Substituir a lógica do botão "Copiar Dados" existente para copiar dados brutos CSV (SgmtNm=CASH) dos tickers selecionados
- O CSV copiado conterá os campos: `RptDt;TckrSymb;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;FinInstrmQty;NtlFinVol`
- Na aba "Análise do Ticker": copia dados apenas do ticker selecionado
- Na aba "Análise Geral": copia dados de todos os tickers selecionados no TickerList
- O período copiado reflete o selecionado nos comboboxes de período e amostragem
- O OperationGuard continua desabilitando/habilitando o botão durante cargas
- Adicionar `segment` e `trades_qty` ao `daily_data` no use case para viabilizar o CSV completo
- Formato brasileiro: campo separado por `;`, decimal com `,` (vírgula)
- Atalho `Ctrl+Shift+C` mantido com a nova lógica

## Capabilities

### New Capabilities
_(Nenhuma — é uma modificação de capability existente)_

### Modified Capabilities
- `clipboard-export`: O conteúdo copiado pelo botão "Copiar Dados" muda de indicadores agregados (Ticker;VWAP;MoneyFlowVolume) para dados brutos do CSV original (RptDt;TckrSymb;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;FinInstrmQty;NtlFinVol), com comportamento sensível à aba ativa

## Impact

- `src/flowscope/application/use_cases.py`: +2 campos no `daily_data` (`segment`, `trades_qty`)
- `src/flowscope/presentation/gui/app.py`: Substituir métodos `_copy_data` e `_fallback_clipboard_text` 
- `src/flowscope/presentation/gui/presenter.py`: Nenhuma mudança (interface `GUIView.config_copy_button_state` já existe)
- Nenhuma dependência nova
- Nenhuma API ou interface pública quebrada
