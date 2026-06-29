## 1. Verificar ícones

- [x] 1.1 Verificar se `document-properties.png`, `edit-select-all.png` e `edit-unselect-all.png` existem em `src/flowscope/icons/`
- [x] 1.2 Se não existirem, criar fallback textual nos botões

## 2. Adicionar modo dual no TickerList (ticker_list.py)

- [x] 2.1 No `__init__`, criar `tk.Listbox` com `selectmode=EXTENDED` e scrollbar ao lado, empilhado no mesmo `text_frame` que o `tk.Text`, inicialmente escondido (`pack_forget`)
- [x] 2.2 Adicionar botões "Selecionar Todos" e "Desmarcar Todos" no `btn_frame` (barra superior), imediatamente à direita do toggle de edição, com `pack(before=sep)` para posicionamento correto ao re-exibir. Visíveis apenas no modo visualização via `_set_view_mode()`.
- [x] 2.3 Adicionar `tk.Checkbutton(indicatoron=0)` com ícone `document-properties.png` na `btn_frame` após separador de "Salvar", com callback `_on_mode_toggle`
- [x] 2.4 Implementar `_set_view_mode(enable: bool)` que alterna visibilidade entre Text e Listbox (+ botões de seleção), e atualiza estado do toggle button
- [x] 2.5 Implementar `_on_mode_toggle()` que lê estado do Checkbutton, salva snapshot ao entrar em edição (D4), executa transição com preservação de seleção ao sair, e dispara `on_data_needed` se lista mudou

## 3. Implementar lógica de transição e estado

- [x] 3.1 No `__init__`, inicializar `_view_tickers_snapshot: list[str] = []` e `_view_selection_snapshot: set[str] = set()`
- [x] 3.2 Ao entrar em modo edição: salvar `_view_tickers_snapshot` e `_view_selection_snapshot` do Listbox; popular Text widget com snapshot
- [x] 3.3 Ao sair do modo edição: ler Text widget; calcular nova seleção (preservando existentes + novos marcados); detectar se lista mudou (`set(text) != set(snapshot)`); popular Listbox com nova seleção
- [x] 3.4 Se lista mudou ao sair do modo edição: chamar callback `on_data_needed`
- [x] 3.5 Implementar `_select_all_listbox()` e `_deselect_all_listbox()` conectados aos botões de view mode

## 4. Adaptar get_tickers(), set_tickers() e carga de dados

- [x] 4.1 `get_tickers()` no modo visualização: retornar `[self._listbox.get(i) for i in self._listbox.curselection()]`
- [x] 4.2 `get_tickers()` no modo edição: comportamento atual (ler Text widget)
- [x] 4.3 `set_tickers()`: forçar modo visualização, limpar e popular Listbox com todos os tickers, selecionar todos, atualizar Text widget (D7)
- [x] 4.4 `_on_load_data()` NÃO chama `set_tickers()` — preserva a lista original do usuário
- [x] 4.5 `_ensure_tickers()` usa `get_all_listbox_tickers()` — carrega todos os tickers, não apenas os selecionados

## 5. Implementar lazy refresh híbrido

- [x] 5.1 Adicionar `self._charts_dirty: bool = True` no `__init__` do `FlowScopeGUI`
- [x] 5.2 Criar `_refresh_current_tab()` que renderiza a aba ativa imediatamente (se dirty) e limpa a bandeira
- [x] 5.3 Chamar `_refresh_current_tab()` após `_on_load_data()` e `_on_ticker_edit()`
- [x] 5.4 Em `_on_tab_changed()`, se `_charts_dirty`: renderizar aba selecionada; resetar `_charts_dirty = False`
- [x] 5.5 `_on_ticker_edit()` marca dirty + `_refresh_current_tab()` (não chama `_update_charts()` diretamente)

## 6. Remover comboboxes da Análise Geral

- [x] 6.1 Remover criação de `_vwap_ticker_combo`, `_quadrant_ticker_combo`, `_dominance_combo` no `_build_main_area()`
- [x] 6.2 Remover `_build_ticker_selector()`, `_update_ticker_selectors()`, `_sync_ticker_selectors()`, `_on_vwap_combo_selected()`, `_on_quadrant_combo_selected()`, `_on_dominance_combo_selected()`
- [x] 6.3 Remover `_syncing_in_progress` attribute
- [x] 6.4 Simplificar `_update_charts()`: sem filtro por combo; `show_arrows = len(filtered) == 1`
- [x] 6.5 Atualizar `_on_ticker_combo_selected()` (não chama `_sync_ticker_selectors`)

## 7. Remover botão Filtrar e reorganizar barra de botões

- [x] 7.1 Remover botão "Filtrar" (`edit-find.png`) de `btn_frame`
- [x] 7.2 Mover `btn_frame` para antes do label "Tickers (um por linha):"
- [x] 7.3 Adicionar separador vertical entre "Salvar" e "Editar"
- [x] 7.4 Adicionar separador vertical entre "Desmarcar Todos" e botões de índice
- [x] 7.5 Botões Selecionar/Desmarcar Todos no grupo do botão Editar, à direita dele
- [x] 7.6 `_deselect_all_listbox()` não dispara `_on_change` (evita substituir lista pelo IDIV)

## 8. Ajustar carga de dados

- [x] 8.1 `_on_load_data()` não sobrescreve `self._tickers` com `_current_data.keys()`
- [x] 8.2 `_on_load_data()` não chama `set_tickers()` — preserva lista original
- [x] 8.3 `_on_date_change()` não substitui tickers — apenas marca dirty + refresh
- [x] 8.4 `_load()` (arquivo) popula listbox diretamente e seleciona todos

## 9. Verificação

- [x] 9.1 Executar linter (`ruff` ou similar)
- [x] 9.2 Executar testes existentes (`pytest`) e garantir que nada quebrou
- [x] 9.3 Testar manualmente: abrir programa (view mode), carregar dados (todos os tickers preservados), selecionar/deselecionar, alternar modos, lazy refresh ao trocar abas
