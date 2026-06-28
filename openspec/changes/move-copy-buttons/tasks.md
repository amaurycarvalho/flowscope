## 1. Toolbar — Adicionar "Copiar Gráfico" ao ToolbarBR

- [x] 1.1 Modificar `ToolbarBR.__init__` para aceitar `copy_chart_callback=None`
- [x] 1.2 Adicionar toolitem "Copiar Gráfico" ao `toolitems` da classe
- [x] 1.3 Adicionar método `copy_chart()` que invoca o callback com `self.canvas.figure`

## 2. VWAPHistChart — Passar callback ao toolbar

- [x] 2.1 Em `VWAPHistChart.__init__`, aceitar `copy_chart_callback` e passar ao ToolbarBR
- [x] 2.2 Passar o callback ao `ToolbarBR(self._canvas, self.frame, copy_chart_callback=...)`

## 3. Top Bar — Adicionar botão "Copiar Dados"

- [x] 3.1 Em `_build_top_bar()`, criar `self._copy_data_btn` ao lado de `self._load_button`, com `state=tk.DISABLED`
- [x] 3.2 Adicionar tooltip ao botão ("Copiar dados CSV para a área de transferência")
- [x] 3.3 Conectar `command=self._copy_data` ao botão

## 4. Gerenciar estado disabled do "Copiar Dados"

- [x] 4.1 Em `_on_load_data()`, habilitar `self._copy_data_btn` após carregamento bem-sucedido (antes do `finally`)

## 5. Remover frame Exportação

- [x] 5.1 Remover bloco `export_frame` + `btn_container` + botões + separador de `_build_main_area()`
- [x] 5.2 Remover conteúdo de `_build_action_buttons()` (já é no-op, confirmar)

## 6. Verificar integração

- [x] 6.1 `Ctrl+Shift+C` permanece bindado a `self._copy_data()` (linha 612)
- [x] 6.2 "Copiar Gráfico" no toolbar chama `_copy_chart(self.canvas.figure)` via callback
- [x] 6.3 "Copiar Dados" inicia DISABLED (linha 151), habilitado após load (linha 418)
- [x] 6.4 Statusbar feedback mantido em `_copy_data` e `_copy_chart`
- [x] 6.5 Nenhuma referência a `_copy_chart_btn`, `export_frame`, `btn_container` removidos (confirmado via grep)
