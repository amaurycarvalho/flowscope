## Why

Quando múltiplos tickers com preços absolutos muito diferentes (ex: R$ 5 vs R$ 500) são exibidos lado a lado no gráfico VWAP, o eixo Y precisa acomodar todas as escalas, comprimindo visualmente os tickers de menor preço e dificultando a identificação de quais ativos estão com LastPric acima ou abaixo do VWAP. A normalização do eixo Y para diferença percentual em relação ao VWAP resolve esse problema colocando todos os tickers na mesma escala.

## What Changes

- Eixo Y do gráfico VWAP passa a exibir `(preço - VWAP) / VWAP × 100` (desvio percentual) em vez do preço absoluto
- VWAP torna-se a linha de base em 0% (representada por `axhline` tracejada)
- Violin plot (distribuição de TradAvrgPric), errorbar (MinPric/MaxPric) e scatter (LastPric) usam a escala normalizada
- Errorbar é substituído por `vlines` para maior robustez em casos extremos
- `_estimate_bucket_size` adaptado para ranges percentuais
- Tooltip do hover atualizado para exibir diferença percentual + valor absoluto
- Rótulo do eixo Y alterado para "Diferença do VWAP (%)"
- Eixo Y configurado com limites simétricos em torno de 0%

## Capabilities

### New Capabilities

- `vwap-chart-normalization`: Normalização do eixo Y do gráfico VWAP para exibir desvio percentual em relação ao VWAP, permitindo comparação visual entre tickers de diferentes escalas de preço

### Modified Capabilities

- `gui-interface`: O requisito "Gráfico de distribuição de preços VWAP" é modificado para especificar que o eixo Y exibe diferença percentual do VWAP em vez de preço absoluto

## Impact

- `src/flowscope/presentation/gui/charts/vwap_hist.py`: Modificação completa do método `update()` e funções auxiliares
- Nenhuma mudança no domínio, aplicação ou infraestrutura — apenas apresentação visual
- Nenhuma mudança na API pública ou CLI
- **Target**: Release 0.1.0
