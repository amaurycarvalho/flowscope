## 1. ToolbarBR — Subclasse em português da NavigationToolbar2Tk

- [x] 1.1 Criar subclasse `ToolbarBR(NavigationToolbar2Tk)` com `toolitems` traduzidos para português (Início, Voltar, Avançar, Mover, Ampliar, Salvar) — sem botão "Config"
- [x] 1.2 Colocar a classe em módulo compartilhado (ex: `presentation/gui/charts/toolbar.py`)

## 2. Botão "Hoje" na barra superior

- [x] 2.1 Adicionar botão "Hoje" ao lado do DateEntry em `_build_top_bar()` no `app.py`
- [x] 2.2 Implementar callback que chama `self._date_entry.set_date(date.today())` — sem auto-load

## 3. Toolbar nos charts

- [x] 3.1 Adicionar `ToolbarBR` no `VWAPHistChart.__init__` — toolbar abaixo do canvas
- [x] 3.2 Adicionar `ToolbarBR` no `CVDHistChart.__init__` — toolbar abaixo do canvas
- [x] 3.3 Adicionar `ToolbarBR` no `ScatterChart.__init__` — toolbar abaixo do canvas, verificar posição do checkbox "Exibir setas temporais"

## 4. Hover tooltip no scatter plot (VWAP × CVD)

- [x] 4.1 Implementar `_on_hover(event)` com `mpl_connect("motion_notify_event")` no `ScatterChart`
- [x] 4.2 Usar `annotate` para exibir tooltip com ticker, VWAP, CVD e volume ao passar sobre ponto
- [x] 4.3 Esconder tooltip ao sair do ponto (set_visible(False))

## 5. Hover tooltip no CVD histogram

- [x] 5.1 Implementar `_on_hover(event)` no `CVDHistChart` para detectar barra sob o mouse via `ax.patches`
- [x] 5.2 Usar `annotate` para exibir tooltip com ticker e valor do CVD

## 6. Hover tooltip no VWAP histogram

- [x] 6.1 Implementar `_on_hover(event)` no `VWAPHistChart` para detectar bucket sob o mouse via `ax.patches` (fill shapes)
- [x] 6.2 Usar `annotate` para exibir tooltip com ticker, faixa de preço e volume

## 7. Smoke test

- [x] 7.1 Executar aplicação e verificar que os 3 charts exibem toolbar com botões em português
- [x] 7.2 Testar zoom/pan/reset em cada chart
- [x] 7.3 Testar hover tooltips no scatter, CVD histogram e VWAP histogram
- [x] 7.4 Testar botão "Hoje" — data atual restaurada sem recarregar
