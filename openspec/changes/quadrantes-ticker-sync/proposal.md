## Why

O gráfico de quadrantes fica visualmente poluído quando exibe setas de trajetória para todos os tickers simultaneamente ("Todos" selecionado). As setas só são informativas quando isolamos um ticker. Além disso, não há sincronia entre o combobox de seleção de ticker nos Quadrantes e o combobox da Análise do Ticker — o usuário precisa selecionar manualmente o mesmo ticker em dois lugares.

## What Changes

- **Quadrantes — visibilidade das setas (quiver):** quando o combobox de ticker estiver como "Todos", as setas de trajetória NÃO serão plotadas. Quando um ticker específico for selecionado, as setas serão plotadas apenas para aquele ticker.
- **Sincronização bidirecional de comboboxes:** o combobox do Quadrantes e o combobox da Análise do Ticker sincronizam seus valores entre si. Ao selecionar um ticker em um, o outro é atualizado (apenas o valor, sem navegação forçada de aba). Quando "Todos" é selecionado no Quadrantes, o combobox da Análise do Ticker é limpo.
- **Abordagem explícita:** o `QuadrantChart.update()` receberá um parâmetro explícito `show_arrows` para controlar a exibição das setas.
- **Comportamento de scatter/labels inalterado:** bolhas, cores, tamanhos e labels continuam sendo plotados normalmente em ambos os modos.

## Capabilities

### New Capabilities

Nenhuma — todas as mudanças são modificações de capacidades existentes.

### Modified Capabilities

- `quadrant-chart`: Requisito "Setas de trajetória temporal (quiver)" — setas passam a ser condicionais: exibidas apenas quando um ticker específico é selecionado, ocultas no modo "Todos". O `update()` passa a aceitar flag `show_arrows`.
- `ticker-analysis`: Requisito "Seleção de ticker para análise individual" — combobox passa a sincronizar bidirecionalmente com o combobox de ticker do gráfico de quadrantes, incluindo limpeza quando "Todos" é selecionado.

## Impact

- `src/flowscope/presentation/gui/charts/quadrant_chart.py`: método `update()` ganha parâmetro `show_arrows: bool`, lógica condicional para desenho das setas.
- `src/flowscope/presentation/gui/app.py`: método `_update_charts()` determina `show_arrows` com base no valor do combobox. Sincronização entre `_quadrant_ticker_combo` e `_ticker_combo` via bindings `<<ComboboxSelected>>`.
- Nenhuma dependência nova. Nenhuma API externa afetada.
