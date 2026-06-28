## 1. Normalizar eixo Y para desvio percentual

- [x] 1.1 Calcular `vwap` por ticker a partir de `info["vwap"]["period_vwap"]` e converter para float
- [x] 1.2 Transformar `avg_price` para `(avg_price - vwap) / vwap * 100` em cada daily_data antes de construir o violino
- [x] 1.3 Transformar `min_price`/`max_price` globais para escala percentual
- [x] 1.4 Transformar `last_price` (último dia) para escala percentual
- [x] 1.5 Adicionar `axhline(y=0, color='gray', linestyle='--')` como baseline VWAP
- [x] 1.6 Alterar rótulo do eixo Y para "Diferença do VWAP (%)"
- [x] 1.7 Forçar limites simétricos do eixo Y usando dados normalizados

## 2. Substituir errorbar por vlines

- [x] 2.1 Remover chamada a `ax.errorbar()` e cálculo de `yerr_lower`/`yerr_upper`
- [x] 2.2 Adicionar `ax.vlines(x_positions, min_prices_pct, max_prices_pct, colors='black', linewidth=1.5)` para barra MinPric–MaxPric
- [x] 2.3 Adicionar `ax.scatter(x_positions, [0]*len(tickers), color='black', marker='o', s=40, zorder=5)` para marcador VWAP em 0%
- [x] 2.4 Remover label "VWAP" da legenda (agora é a baseline em 0%)

## 3. Adaptar bucket size para escala percentual

- [x] 3.1 Modificar `_estimate_bucket_size` para receber e processar dados já normalizados
- [x] 3.2 Implementar heurística: range ≤ 0.5% → 0.01%, ≤ 2% → 0.05%, ≤ 10% → 0.25%, > 10% → 0.50%

## 4. Atualizar tooltip de hover

- [x] 4.1 Armazenar valores absolutos de VWAP para exibição no tooltip
- [x] 4.2 Modificar `_on_hover` para exibir ticker, "VWAP: R$ X.XX", "Δ Máx: +X.XX% / Mín: -X.XX%", "LastPric: +X.XX%", "Volume: X"
- [x] 4.3 Calcular e armazenar `last_price_pct` no hover data

## 5. Tratar edge cases

- [x] 5.1 Adicionar proteção contra `vwap == 0` (pular ticker com fallback)
- [x] 5.2 Verificar comportamento com ticker de único dia (avg_price = vwap → violino centrado em 0%)
- [x] 5.3 Verificar comportamento com dados vazios (título de fallback "VWAP — Distribuição de Preços")

## 6. Verificar e ajustar testes

- [x] 6.1 Identificar testes existentes que dependem do comportamento do chart (nenhum encontrado)
- [x] 6.2 Atualizar snapshots/assertions se houver testes visuais ou de valor (não há)
- [x] 6.3 Executar suite de testes e corrigir falhas (78/78 passed)
