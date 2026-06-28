## Why

O frame Exportação ocupa espaço vertical no PanedWindow e, após a última refatoração (adição do splitter), os botões de ação ficam redundantes com funcionalidades que pertencem a locais mais naturais da interface. "Copiar Gráfico" é uma ação do chart — deve estar no toolbar do matplotlib. "Copiar Dados" é uma ação global — deve estar na barra superior ao lado de "Carregar", desabilitado até que haja dados carregados.

## What Changes

- **Remover** o frame `Exportação` (LabelFrame + btn_container + botões + separador) do `self._left_pw` em `_build_main_area()`
- **Mover** o botão "Copiar Gráfico" para o `ToolbarBR` como um toolitem custom, disponível em todos os charts que usarem o toolbar
- **Mover** o botão "Copiar Dados" para a barra superior (`_build_top_bar()`), ao lado do botão "Carregar"
- **Adicionar** estado disabled ao botão "Copiar Dados": inicia desabilitado, só é habilitado após `_on_load_data()` completar com sucesso
- **Atualizar** o `ToolbarBR` para aceitar um callback de cópia de gráfico via construtor
- **Ajustar** `_copy_chart` para usar `self._canvas.figure` (genérico) em vez de `self._vwap_chart.get_figure()` (acoplado ao VWAP)
- **Ajustar** `_enter_loading_state` / `_exit_loading_state` para incluir o novo botão
- Remover o separador visual entre "Copiar Dados" e "Copiar Gráfico" (não fará mais sentido)

## Capabilities

### New Capabilities
- *(none)*

### Modified Capabilities
- `ui-polish`: Requirement "LabelFrame para agrupamento visual" — remover referência ao frame Exportação e ao agrupamento dos botões de ação. Requirement "Separação visual entre botões de ação" — remover (os botões não estarão mais lado a lado). Requirement "Atalhos de teclado" — atalho Ctrl+Shift+C permanece, mas agora referenciando o botão na top bar.
- `clipboard-export`: Requirement "Cópia de gráfico como imagem PNG para clipboard" — o botão agora está no toolbar do chart, não mais no frame Exportação. O comportamento funcional não muda.

## Impact

- `src/flowscope/presentation/gui/app.py`: `_build_top_bar()`, `_build_main_area()`, `_build_action_buttons()`, `_enter_loading_state()`, `_exit_loading_state()`, `_on_load_data()` — remoção do export frame, adição do botão na top bar, controle de disabled state
- `src/flowscope/presentation/gui/charts/toolbar.py`: `ToolbarBR` — aceitar `copy_chart_callback` via parâmetro, adicionar toolitem "Copiar Gráfico"
- `src/flowscope/presentation/gui/charts/vwap_hist.py`: `VWAPHistChart` — passar callback ao `ToolbarBR`
- `openspec/specs/ui-polish/spec.md`: Delta spec — remover requisitos de agrupamento/separação dos botões
- `openspec/specs/clipboard-export/spec.md`: Delta spec — esclarecer que o botão "Copiar Gráfico" está no toolbar
