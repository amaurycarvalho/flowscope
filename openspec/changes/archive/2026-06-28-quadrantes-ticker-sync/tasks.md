## 1. QuadrantChart — parâmetro show_arrows

- [x] 1.1 Adicionar parâmetro `show_arrows: bool = False` ao método `QuadrantChart.update()`
- [x] 1.2 Envolver o bloco de desenho das setas (linhas 79-88 em `quadrant_chart.py`) em um `if show_arrows:`

## 2. app.py — controle de show_arrows em _update_charts

- [x] 2.1 Em `_update_charts()`, determinar `show_arrows = (quadrant_sel != "Todos")`
- [x] 2.2 Passar `show_arrows` como argumento na chamada `self._quadrant_chart.update(filtered_quadrant, show_arrows=show_arrows)`

## 3. app.py — sincronização bidirecional dos comboboxes

- [x] 3.1 Criar flag `_syncing_in_progress: bool = False` no `__init__` do `FlowScopeGUI`
- [x] 3.2 No binding do `_quadrant_ticker_combo`, adicionar handler que: (a) verifica `_syncing_in_progress`, (b) seta `_syncing_in_progress = True`, (c) se ticker específico → seta `_ticker_combo` com o mesmo valor, (d) se "Todos" → limpa `_ticker_combo` (set vazio), (e) restaura `_syncing_in_progress = False`
- [x] 3.3 No binding do `_ticker_combo`, adicionar handler que: (a) verifica `_syncing_in_progress`, (b) seta `_syncing_in_progress = True`, (c) se ticker selecionado → seta `_quadrant_ticker_combo` com o mesmo valor e chama `_update_charts()`, (d) restaura `_syncing_in_progress = False`
- [x] 3.4 Garantir que o binding do `_quadrant_ticker_combo` continue chamando `_update_charts()` (comportamento existente)

## 4. Verificação

- [x] 4.1 Testar manualmente: carregar dados, selecionar "Todos" → setas ocultas, scatter visível
- [x] 4.2 Testar manualmente: selecionar ticker específico → setas visíveis apenas para ele
- [x] 4.3 Testar manualmente: selecionar ticker no Quadrantes → Análise do Ticker sincroniza
- [x] 4.4 Testar manualmente: selecionar ticker na Análise do Ticker → Quadrantes sincroniza e gráfico atualiza
- [x] 4.5 Testar manualmente: "Todos" no Quadrantes → Análise do Ticker fica vazio
- [x] 4.6 Verificar que não há loop infinito de sincronização
