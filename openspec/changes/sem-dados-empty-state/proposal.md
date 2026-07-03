## Why

Ao iniciar o programa, todos os painéis de gráficos mostram eixos matplotlib em branco (com ticks, spines e grid visíveis) — aspecto visualmente polido e que não comunica estado ao usuário. Além disso, todos os charts de sub-tabs ocultas são renderizados durante o carregamento, desperdiçando processamento. Esta mudança introduz um estado vazio explícito ("Sem dados") e renderização lazy por sub-tab.

## What Changes

- Todos os 6 charts (VWAPHist, Quadrant, DominanceRanking, DominanceTimeline, PriceRangePanel, FinancialFlowPanel) passam a exibir "Sem dados" centralizado com `ax.axis("off")` na inicialização e quando não há dados disponíveis
- A renderização dos charts passa a ser lazy por sub-tab: apenas o chart da sub-tab visível é atualizado ao carregar/recarregar dados
- Ao recarregar dados, todos os charts não-visíveis voltam ao estado "Sem dados" (Opção A)
- Criação de uma utility function compartilhada para o estado vazio (`create_empty`, `show_empty`, `hide_empty`)
- Criação de um registry mapping em `app.py` para coordenar qual chart renderizar por sub-tab, eliminando o `if/elif` atual
- Os charts multi-eixos (PriceRangePanel, FinancialFlowPanel) usam `fig.text()` centralizado em vez de labels por subplot (Opção B)

## Capabilities

### New Capabilities
- `chart-empty-state`: Estado visual "Sem dados" para todos os charts, com lazy rendering por sub-tab, abrangendo a inicialização, carregamento, recarga e navegação entre abas.

### Modified Capabilities
<!-- Nenhuma capability existente tem seus REQUIREMENTS alterados — o comportamento das
     funcionalidades existentes (VWAP, quadrantes, dominância, etc.) não muda quando
     há dados e o painel está visível. Apenas adicionamos um estado visual intermediário. -->

## Impact

- **src/flowscope/presentation/gui/charts/** — Todos os 6 charts: adicionar empty state no `__init__` e nos guards de `update()`
- **src/flowscope/presentation/gui/app.py** — Refatorar `_update_charts()`, `_update_ticker_indicator_tabs()`, `_on_tab_changed()`, `_on_load_data()` para usar registry + lazy rendering
- **src/flowscope/presentation/gui/charts/__init__.py** — Adicionar utility function compartilhada (ou criar novo módulo `empty_state.py`)
