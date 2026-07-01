## 1. Price Range Panel — Módulo de Chart

- [ ] 1.1 Criar `src/flowscope/presentation/gui/charts/price_range_panel.py` com classe `PriceRangePanel` seguindo o padrão das classes existentes (Figure + canvas + toolbar)
- [ ] 1.2 Implementar o método `_build_timeline()`: Price Range Timeline Chart com GridSpec, eixo Y temporal (datas), eixo X normalizado [0%, 100%], banda horizontal representando o range
- [ ] 1.3 Implementar marcadores do dia atual (Median, Typical, VWAP, Weighted Close, Close) com `scatter()` e `annotate()`, apenas para a última data
- [ ] 1.4 Implementar marcadores de close (●) para dias anteriores com opacidade reduzida
- [ ] 1.5 Implementar quiver temporal com `arrow()` conectando closes consecutivos
- [ ] 1.6 Implementar o método `_build_range_history()`: subplot de Range % como linha do tempo com destaque no ponto atual
- [ ] 1.7 Implementar o método `_build_efficiency_gauge()`: gauge horizontal de Daily Efficiency (escala 0-1) com `barh` e cores por faixa
- [ ] 1.8 Implementar o método `_build_clv_gauge()`: gauge horizontal de CLV (escala -1 a +1) com `barh` e cor verde/vermelho
- [ ] 1.9 Implementar classificação qualitativa como `fig.text()` no timeline chart, com thresholds baseados na mediana histórica do Range%
- [ ] 1.10 Implementar método `update(data, ticker)` que extrai dados do ticker selecionado e repopula todos os subplots
- [ ] 1.11 Adicionar suporte a hover/tooltip para mostrar valores dos marcadores

## 2. Integração com a GUI

- [ ] 2.1 Importar `PriceRangePanel` em `src/flowscope/presentation/gui/app.py`
- [ ] 2.2 Adicionar `"Amplitude de Preço"` ao conjunto `enabled_tabs` para habilitar a aba
- [ ] 2.3 Substituir o widget `Text` da aba "Amplitude de Preço" por uma instância de `PriceRangePanel`
- [ ] 2.4 Atualizar `_update_ticker_indicator_tabs()` para chamar `price_range_panel.update()` quando a aba estiver ativa
- [ ] 2.5 Atualizar `_tab_content` com o novo texto de orientação (objetivo, pergunta respondida, indicadores, interpretação)

## 3. Documentação

- [ ] 3.1 Atualizar `panels.md` seção "Sub-aba: Amplitude de Preço" para refletir o novo layout visual e texto de orientação
