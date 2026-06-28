## 1. Indicador VWAP Distance

- [x] 1.1 Criar `src/flowscope/domain/strategies/vwap_distance.py` com `VWAPDistanceStrategy` (depende de `vwap`, computa `(last_price - daily_vwap) / daily_vwap` por ticker-por-data)
- [x] 1.2 Exportar `VWAPDistanceStrategy` em `src/flowscope/domain/strategies/__init__.py`
- [x] 1.3 Registrar `VWAPDistanceStrategy()` em `src/flowscope/domain/indicators.py::default_engine()`
- [x] 1.4 Adicionar `vwap_distance` na lista de indicadores em `_format_all_indicators()` em `app.py`
- [x] 1.5 Adicionar `vwap_distance` no texto de orientação da aba "Fluxo Financeiro" em `app.py`
- [x] 1.6 Criar `tests/test_domain/test_vwap_distance.py` com testes para o novo indicador

## 2. Gráfico de Quadrantes (QuadrantChart)

- [x] 2.1 Criar `src/flowscope/presentation/gui/charts/quadrant_chart.py` com classe `QuadrantChart` seguindo o padrão `VWAPHistChart` (matplotlib + FigureCanvasTkAgg + ToolbarBR)
- [x] 2.2 Implementar `update(data)`: extrair CLV, VWAP Distance, fin_instr_qty, e trajetórias por ticker-por-data
- [x] 2.3 Renderizar setas quiver para dias anteriores e scatter para o dia mais recente
- [x] 2.4 Aplicar colormap divergente RdYlGn às bolhas com base no CLV
- [x] 2.5 Dimensionar bolhas como `sqrt(fin_instr_qty)` normalizado
- [x] 2.6 Exibir linhas centrais tracejadas em X=0 e Y=0
- [x] 2.7 Implementar tooltip ao passar o mouse (ticker, data, CLV, VWAP Distance, fin_instr_qty)
- [x] 2.8 Implementar `get_figure()` para cópia do gráfico

## 3. Integração na Interface

- [x] 3.1 Importar `QuadrantChart` em `app.py`
- [x] 3.2 Substituir placeholder "Em desenvolvimento." pela instância do `QuadrantChart` no `general_quadrantes_frame`
- [x] 3.3 Chamar `quadrant_chart.update(filtered)` em `_update_charts()`
- [x] 3.4 Adicionar entry de `(\"Análise Geral\", \"Quadrantes\")` em `self._tab_content` com texto de orientação

## 4. Resumo Automático

- [x] 4.1 Implementar lógica de contagem por quadrante e geração de frases template no `QuadrantChart.update()` ou em função separada
- [x] 4.2 Integrar o resumo ao `OrientationPanel` via callback ou atualização direta

## 5. Documentação

- [x] 5.1 Atualizar `panels.md`: substituir seção "Quadrantes" com descrição completa (objetivo, indicadores, interpretação dos quadrantes)
- [x] 5.2 Atualizar `indicators.md`: adicionar entrada "VWAP Distance" na categoria "Volume"
