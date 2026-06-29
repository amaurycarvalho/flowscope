## 1. Verificar ícones

- [ ] 1.1 Verificar se `document-properties.png`, `edit-select-all.png` e `list-remove-all.png` existem em `src/flowscope/icons/`
- [ ] 1.2 Se não existirem, criar fallback textual nos botões

## 2. Adicionar modo dual no TickerList (ticker_list.py)

- [ ] 2.1 No `__init__`, criar `tk.Listbox` com `selectmode=EXTENDED` e scrollbar ao lado, empilhado no mesmo `text_frame` que o `tk.Text`, inicialmente escondido (`pack_forget`)
- [ ] 2.2 Adicionar frame `_view_btn_frame` entre o label e o `text_frame` com botões "Selecionar Todos" e "Desmarcar Todos" (inicialmente escondido)
- [ ] 2.3 Adicionar `tk.Checkbutton(indicatoron=0)` com ícone `document-properties.png` na `btn_frame` entre Salvar e Filtrar, com callback `_on_mode_toggle`
- [ ] 2.4 Implementar `_set_view_mode(enable: bool)` que alterna visibilidade entre Text e Listbox (+ view buttons), e atualiza estado do toggle button
- [ ] 2.5 Implementar `_on_mode_toggle()` que lê estado do Checkbutton, salva snapshot ao entrar em edição (D4), executa transição com preservação de seleção ao sair, e dispara `on_data_needed` se lista mudou

## 3. Implementar lógica de transição e estado

- [ ] 3.1 No `__init__`, inicializar `_view_tickers_snapshot: list[str] = []` e `_view_selection_snapshot: set[str] = set()`
- [ ] 3.2 Ao entrar em modo edição: salvar `_view_tickers_snapshot` e `_view_selection_snapshot` do Listbox; popular Text widget com snapshot
- [ ] 3.3 Ao sair do modo edição: ler Text widget; calcular nova seleção (preservando existentes + novos marcados); detectar se lista mudou (`set(text) != set(snapshot)`); popular Listbox com nova seleção
- [ ] 3.4 Se lista mudou ao sair do modo edição: chamar callback `on_data_needed`
- [ ] 3.5 Implementar `_select_all_listbox()` e `_deselect_all_listbox()` conectados aos botões de view mode

## 4. Adaptar get_tickers() e set_tickers() para o modo dual

- [ ] 4.1 `get_tickers()` no modo visualização: retornar `[self._listbox.get(i) for i in self._listbox.curselection()]`
- [ ] 4.2 `get_tickers()` no modo edição: comportamento atual (ler Text widget)
- [ ] 4.3 `set_tickers()`: forçar modo visualização, limpar e popular Listbox com todos os tickers, selecionar todos, atualizar Text widget (D7)

## 5. Adicionar lazy refresh no app.py

- [ ] 5.1 Adicionar `self._charts_dirty: bool = True` no `__init__` do `FlowScopeGUI`
- [ ] 5.2 Em `_on_load_data()`, após `self._ticker_list.set_tickers(...)`, setar `_charts_dirty = True` e remover chamada direta a `_update_charts()`
- [ ] 5.3 Em `_on_ticker_edit()`, setar `_charts_dirty = True` e NÃO chamar `_update_charts()`, `_update_ticker_indicator_tabs()`, `_update_ticker_counter()`
- [ ] 5.4 Em `_on_tab_changed()`, se `_charts_dirty`: chamar `_update_charts()` (Análise Geral) e/ou `_update_ticker_indicator_tabs()` + `_update_ticker_counter()` (Análise do Ticker); resetar `_charts_dirty = False`

## 6. Conectar TickerList ao FlowScopeGUI

- [ ] 6.1 Adicionar parâmetro `on_data_needed` na construção do `TickerList` em `FlowScopeGUI._build_main_area()`, apontando para `_on_load_data`
- [ ] 6.2 Remover `_update_charts()` da linha `self._on_tab_changed()` ao final de `_restore_tabs()` se existir (lazy refresh evita dupla renderização)

## 7. Atualizar contador (update_ticker_counter)

- [ ] 7.1 `_update_ticker_counter()` deve calcular `n_total` do Listbox (todos os itens, independente de seleção) e `n_filtered` do `get_tickers()` (selecionados), formatando "Exibindo M de N ativos" ou "Tickers (N)"

## 8. Verificação

- [ ] 8.1 Executar linter (`ruff` ou similar)
- [ ] 8.2 Executar testes existentes (`pytest`) e garantir que nada quebrou
- [ ] 8.3 Testar manualmente: abrir programa (view mode), carregar dados (view + all selected), selecionar/deselecionar, alternar modos, verificar lazy refresh ao trocar abas
