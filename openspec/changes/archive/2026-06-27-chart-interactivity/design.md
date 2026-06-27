## Context

Os três charts do FlowScope (VWAP histogram, CVD histogram, scatter) são estáticos — usam `matplotlib.figure.Figure` com `FigureCanvasTkAgg` embedado em tkinter, sem qualquer toolbar ou interação. O DateEntry usa `maxdate=date.today()` mas não há botão para navegação rápida. Não há hover tooltip ou forma de inspecionar coordenadas dos pontos.

## Goals / Non-Goals

**Goals:**
- Adicionar NavigationToolbar2Tk em cada chart com zoom, pan, reset, save (labels em português)
- Adicionar botão "Hoje" na top bar para resetar DateEntry para `date.today()`
- Adicionar hover tooltips: scatter (ticker, VWAP, CVD, volume), CVD histogram (valor exato), VWAP histogram (faixa de preço e volume)
- Manter compatibilidade com matplotlib >= 3.5 (já instalado 3.6.3)

**Non-Goals:**
- Não adicionar novas dependências externas (toolbar é matplotlib nativo, tooltips via eventos)
- Não refatorar a arquitetura de charts para classe base compartilhada
- Não adicionar scroll-to-zoom (já coberto pelo NavigationToolbar2Tk)
- Não modificar comportamento existente de carregamento/filtro

## Decisions

### Decision 1: NavigationToolbar2Tk padrão vs custom toolbar
**Escolha**: NavigationToolbar2Tk com subclasse ToolbarBR para português
**Alternativa**: Custom toolbar com botões tkinter + eventos matplotlib — mais trabalho, sem ganho
**Rationale**: NavigationToolbar2Tk fornece home/back/forward/pan/zoom/save gratuitamente, com coordenadas em tempo real no canto da toolbar. A subclasse permite trocar `toolitems` para português sem reimplementar nada.

### Decision 2: Toolbar por chart vs toolbar compartilhada
**Escolha**: Uma toolbar por chart (cada chart cria a sua no `__init__`)
**Alternativa**: Toolbar única em app.py que re-targeta o canvas — requer desconectar/reconectar eventos do matplotlib
**Rationale**: Como apenas um chart fica visível por vez (pack_forget/pack gerenciado por `_show_current_chart`), a toolbar vem/esconde junto com o frame. Mais simples e sem estado compartilhado.

### Decision 3: Hover tooltip via matplotlib events vs mplcursors
**Escolha**: `mpl_connect("motion_notify_event")` com `annotate` customizado
**Alternativa**: `mplcursors` library — API mais concisa mas dependência externa
**Rationale**: matplotlib puro é suficiente para o caso de uso (pontos discretos, ~100 tickers no máximo). Evita adicionar dependência. O `annotate` é atualizado via `set_text()` e `xy` no evento de mouse.

### Decision 4: Botão "Hoje" — com ou sem auto-load
**Escolha**: Apenas seta a data no DateEntry, não dispara load automaticamente
**Rationale**: Consistente com o comportamento atual (usuário escolhe data, clica "Carregar"). Auto-load surpreenderia se o usuário quer só ver a data sem recarregar.

## Risks / Trade-offs

- [Layout] NavigationToolbar2Tk ocupa ~50px verticais. O checkbox "Exibir setas temporais" no scatter fica entre canvas e toolbar. Pode ser necessário reposicionar.
- [Performance] Hover em ~100 pontos no scatter é leve (`contains_point`), mas o VWAP histogram com múltiplos buckets por ticker pode ter mais elementos. Testar com IDIV completo.
- [Tooltip duração] Tooltips em matplotlib somem ao mover o mouse — comportamento esperado, mas diferente do ToolTip customizado do tkinter (delay + persistência). Aceitável.
- [Subplots] NavigationToolbar2Tk inclui botão "Config" (subplots) que não faz sentido com chart único. Removido na subclasse ToolbarBR.
- [Save] O diálogo "Save the figure" do matplotlib está em inglês. Para manter consistência com o app em português, seria necessário customizar — baixo priority, aceitar como está.
