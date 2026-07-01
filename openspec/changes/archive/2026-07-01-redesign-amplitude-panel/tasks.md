## 1. Price Range Panel — Módulo de Chart

- [x] 1.1 Criar `src/flowscope/presentation/gui/charts/price_range_panel.py` com classe `PriceRangePanel` seguindo o padrão das classes existentes (Figure + canvas + toolbar)
- [x] 1.2 Implementar o método `_build_timeline()`: Price Range Timeline Chart com GridSpec, eixo Y temporal (datas), eixo X normalizado [0%, 100%], banda horizontal representando o range
- [x] 1.3 Implementar marcadores do dia atual (Median, Typical, VWAP, Weighted Close, Close) com `scatter()` e `annotate()`, apenas para a última data
- [x] 1.4 Implementar marcadores de close (●) para dias anteriores com opacidade reduzida
- [x] 1.5 Implementar quiver temporal com `arrow()` conectando closes consecutivos
- [x] 1.6 Implementar o método `_build_range_history()`: subplot de Range % como linha do tempo com destaque no ponto atual
- [x] 1.7 Implementar o método `_build_efficiency_gauge()`: gauge horizontal de Daily Efficiency (escala 0-1) com `barh` e cores por faixa
- [x] 1.8 Implementar o método `_build_clv_gauge()`: gauge horizontal de CLV (escala -1 a +1) com `barh` e cor verde/vermelho
- [x] 1.9 Implementar classificação qualitativa como `fig.text()` no timeline chart, com thresholds baseados na mediana histórica do Range%
- [x] 1.10 Implementar método `update(data, ticker)` que extrai dados do ticker selecionado e repopula todos os subplots
- [x] 1.11 Adicionar suporte a hover/tooltip para mostrar valores dos marcadores

## 2. Integração com a GUI

- [x] 2.1 Importar `PriceRangePanel` em `src/flowscope/presentation/gui/app.py`
- [x] 2.2 Adicionar `"Amplitude de Preço"` ao conjunto `enabled_tabs` para habilitar a aba
- [x] 2.3 Substituir o widget `Text` da aba "Amplitude de Preço" por uma instância de `PriceRangePanel`
- [x] 2.4 Atualizar `_update_ticker_indicator_tabs()` para chamar `price_range_panel.update()` quando a aba estiver ativa
- [x] 2.5 Atualizar `_tab_content` com o novo texto de orientação (objetivo, pergunta respondida, indicadores, interpretação)

## 3. Documentação

- [x] 3.1 Atualizar `panels.md` seção "Sub-aba: Amplitude de Preço" para refletir o novo layout visual e texto de orientação
