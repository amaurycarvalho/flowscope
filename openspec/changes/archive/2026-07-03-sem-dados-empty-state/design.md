## Context

O aplicativo FlowScope possui 6 charts matplotlib distribuídos em dois níveis de abas (main tabs + sub-tabs). Atualmente:

- Na inicialização, cada chart exibe eixos matplotlib padrão (ticks, spines, grid visíveis) sem nenhum label ou estado informativo
- Quando `update()` é chamado sem dados, cada chart popula `ax.set_title()` com título e retorna — os eixos continuam visíveis
- Todos os charts de um main tab são renderizados ao mesmo tempo, independente de qual sub-tab está visível
- Não há classe base compartilhada — cada chart gerencia sua própria Figure, Canvas e Toolbar
- Charts multi-eixos (PriceRangePanel: 2 subplots, FinancialFlowPanel: 3 subplots) tratam o estado vazio individualmente por subplot com `set_xlim()` e `set_title()`

## Goals / Non-Goals

**Goals:**
- Estado vazio visualmente limpo para todos os charts (axis off + "Sem dados" centralizado)
- Renderização lazy por sub-tab: apenas o chart visível é atualizado no carregamento
- Recarga de dados (Opção A): charts não-visíveis resetam para "Sem dados"
- Utility function compartilhada para o padrão `create_empty` / `show_empty` / `hide_empty`
- Registry mapping em `app.py` para coordenar qual chart renderizar
- Mínima intrusão nos charts existentes — cada chart ganha ~5 linhas

**Non-Goals:**
- Não criar uma classe base abstrata para charts (assinaturas de `update()` divergem)
- Não implementar Observer/EventBus (Tkinter não oferece detecção nativa de visibilidade de sub-tab)
- Não alterar a lógica de negócio dos charts quando há dados e estão visíveis
- Não modificar a toolbar, hover/tooltip, ou clipboard copy

## Decisions

### D1: Utility functions em módulo separado vs método em base class

**Decisão**: Módulo separado `src/flowscope/presentation/gui/charts/empty_state.py`

**Rationale**: As assinaturas de `update()` divergem entre charts (parâmetros diferentes para ticker vs. show_arrows), o que torna uma base class frágil — qualquer mudança na assinatura quebraria o contrato. Utility functions são chamadas explicitamente em cada chart, sem acoplamento de herança. O custo é 3 chamadas de função por chart (init, empty guard, data path) vs. herança silenciosa.

**Alternativa considerada**: Mixin `EmptyStateMixin` — rejeitado porque mixins em Python com `__init__` que precisa configurar a Figure são frágeis (precisam de `super().__init__` disciplinado, que os charts atuais não têm).

### D2: fig.text() para multi-eixos vs label por subplot (Opção B)

**Decisão**: `fig.text()` centralizado para todos os charts, independente do número de eixos.

**Rationale**: Visualmente mais limpo — um único "Sem dados" no centro do figure. Para charts single-axis, `fig.text()` cobre o axes (que está com `axis("off")`), então não há diferença visual. A utility function `create_empty` sempre usa `fig.text()` e recebe a lista de axes para desligá-los.

### D3: Registry mapping vs if/elif

**Decisão**: Registry mapping com dois dicts (GENERAL, TICKER) + método `_resolve_chart()` + `_do_update()` com `isinstance` para o caso especial do Quadrant.

**Rationale**: Elimina a repetição de if/elif. A única exceção é `show_arrows` do QuadrantChart, que requer `isinstance` — contido em _do_update. O mapping é declarativo e fácil de estender.

```
GENERAL = {
    "VWAP":                self._vwap_chart,
    "Quadrantes":          self._quadrant_chart,
    "Dominância do Pregão": self._dominance_ranking,
}
TICKER = {
    "Evolução da Dominância": self._dominance_timeline,
    "Amplitude de Preço":     self._price_range_panel,
    "Fluxo Financeiro":       self._financial_flow_panel,
}
```

**Alternativa considerada**: Single dict com tuplas `(main_tab, sub_tab)` como chave — rejeitado porque a lógica de filtragem de dados difere entre main tabs (general vs ticker), então dois dicts + notebook check é mais claro.

### D4: Opção A (pure) para recarga de dados

**Decisão**: Em `_on_load_data()`, após carregar os dados, reseta todos os charts com reset() e depois renderiza apenas o chart da sub-tab atual.

**Rationale**: Consistência total — nenhum chart exibe dado obsoleto. O "flash" visual ao trocar de sub-tab após recarga é mitigado porque o `reset()` é instantâneo (só texto + axis off) e o `update()` subsequente é rápido.

**Risco**: Se o usuário recarrega dados e rapidamente navega por várias sub-tabs, cada troca dispara um `update()` com renderização real. Isso é o mesmo comportamento de hoje (quando o usuário navega, os charts renderizam), então não há regressão.

### D5: Previnir flash do chart visível no reload

**Decisão**: O chart atualmente visível NÃO é resetado antes de ser atualizado. Na implementação, primeiro identifica-se o chart atual com `_resolve_chart()`, então reseta-se todos os charts QUE NÃO SÃO o atual, e então chama-se `update()` no atual.

```python
current = self._resolve_current_chart()
for c in self._all_charts:
    if c is not current:
        c.reset()     # volta pra "Sem dados"
self._do_update(current, ...)  # renderiza com dados novos
```

## Architecture

```
app.py :: _on_load_data()
    │
    ├── busca dados
    ├── current = _resolve_chart(main_tab, sub_tab)
    ├── for c in _all_charts: if c is not current: c.reset()
    └── _do_update(current, filtered)
            │
            └── isinstance(QuadrantChart)? 
                    ├── Sim: chart.update(data, show_arrows=...)
                    └── Não (general): chart.update(data)
                    └── Não (ticker): chart.update(data, ticker=t)

app.py :: _on_tab_changed()
    │
    ├── current = _resolve_chart(main_tab, sub_tab)
    └── if current and _current_data: _do_update(current, filtered)

empty_state.py (utility)
    │
    ├── create_empty(fig, axes) → Text
    ├── show_empty(fig, axes, label)
    └── hide_empty(label)

Cada chart:
    __init__():
        ...existing init...
        self._all_axes = [...]       # lista de axes
        self._empty_label = create_empty(self._figure, self._all_axes)
    
    update():
        hide_empty(self._empty_label)
        self._axes.clear()
        ...existing plotting logic...
    
    update() empty guard:
        if not data:
            show_empty(self._figure, self._all_axes, self._empty_label)
            self._canvas.draw()
            return
```

## Component states

```
┌──────────┐         data load          ┌──────────┐
│  EMPTY   │  + sub-tab visible ──────▶ │  LOADED  │
│         │◀───── reset()               │         │
│ axis off │         data reload         │ plot     │
│ fig.text │                             │ visible  │
└──────────┘                             └──────────┘
     ▲                                        │
     │                                        │
     │    data reload                          │ tab switch away
     │    (current chart)                      │
     │                                        ▼
     │                              ┌──────────┐
     │                              │ LOADED   │
     │                              │ (hidden) │
     │                              │          │
     │                              │    ...até
     │                              │ tab switch
     │                              │ de volta
     │                              └──────────┘
     │
     └────────────────────────────────┘
            reset() on reload
            (non-current charts)
```

## Risks / Trade-offs

- **[isinstance]** O `isinstance(chart, QuadrantChart)` em `_do_update()` é frágil se a hierarquia de classes mudar. Mitigação: documentado com comentário e protegido por type check explícito. Alternativa seria adicionar um atributo `self._needs_show_arrows = True` no QuadrantChart.
- **[Reset cost]** Chamar `c.reset()` em todos os charts não-visíveis no reload é O(1) visual (só texto + axis off) e não envolve busca de dados. Custo desprezível.
- **[Tab switch latency]** Ao trocar para uma sub-tab cujo chart está em EMPTY, o `update()` renderiza o chart completo. Isso é idêntico ao comportamento de hoje (quando o chart nunca foi atualizado), sem regressão.
- **[Toolbar visibility]** O toolbar permanece visível durante o estado EMPTY. O usuário pode interagir com ele (zoom, pan, copy), mas sobre um gráfico vazio. Isso é comportamento existente e não muda.
