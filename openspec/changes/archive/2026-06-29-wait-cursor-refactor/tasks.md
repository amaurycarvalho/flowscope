## 1. Core — refatorar loading state em 2 camadas

- [x] 1.1 Adicionar `_set_wait_cursor()`: `self.config(cursor="watch")` + `self.update_idletasks()`
- [x] 1.2 Adicionar `_clear_wait_cursor()`: `self.config(cursor="")`
- [x] 1.3 Refatorar `_enter_loading_state()`: substituir `self.config(cursor="watch")` + `self.update_idletasks()` por `self._set_wait_cursor()`
- [x] 1.4 Refatorar `_exit_loading_state()`: substituir `self.config(cursor="")` por `self._clear_wait_cursor()`
- [x] 1.5 Verificar que `_on_load_data` (L483-510) continua funcionando (cursor + animação + inputs)

## 2. Aplicar cursor em refresh de charts via troca de aba

- [x] 2.1 Em `_on_tab_changed()` (L597), envolver o bloco `if self._charts_dirty and self._current_data` (L607-614) com `self._set_wait_cursor()` / try / finally / `self._clear_wait_cursor()`
- [x] 2.2 Verificar que early returns (exceção L604-605, `_charts_dirty` falso L607) não acionam o cursor

## 3. Aplicar cursor em refresh via edição de tickers

- [x] 3.1 Em `_on_ticker_edit()` (L627), envolver `self._refresh_current_tab()` (L638) com `self._set_wait_cursor()` / try / finally / `self._clear_wait_cursor()`
- [x] 3.2 Verificar que early returns (L629-634) não acionam o cursor

## 4. Aplicar cursor em cópia de gráfico

- [x] 4.1 Em `_copy_chart()` (L729), envolver `copy_image_to_clipboard(figure)` (L733) com `self._set_wait_cursor()` / try / finally / `self._clear_wait_cursor()`
- [x] 4.2 Garantir que exceção `ClipboardError` (L735) também restaura o cursor (finally já garante)

## 5. Verificação final

- [x] 5.1 Executar a aplicação e testar: carregar dados (F5), trocar abas, editar tickers, selecionar ticker no combo, copiar gráfico
- [x] 5.2 Confirmar que cursor watch aparece durante cada operação e retorna ao normal ao final
- [x] 5.3 Confirmar que `_on_load_data` continua com inputs desabilitados + animação "Carregando..."
