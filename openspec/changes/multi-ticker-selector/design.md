## Context

Atualmente o TickerList é composto por:
- Label com contador
- `tk.Text` widget para edição livre de tickers
- Botões: Carregar, Salvar, Filtrar, índices (IBOV, IDIV, IFIX)
- Menu de contexto com copiar/remover/selecionar

O `get_tickers()` retorna todos os tickers do Text widget, que alimenta `self._tickers` no `FlowScopeGUI`. Este `self._tickers` é usado para popular os comboboxes da Análise Geral (`["Todos"] + self._tickers`) e da Análise do Ticker, e também como filtro nos gráficos.

Não há suporte a seleção visual de múltiplos tickers — para filtrar, o usuário precisa apagar linhas do Text widget, perdendo a lista original.

## Goals / Non-Goals

**Goals:**
- Adicionar modo visualização com Listbox(EXTENDED) no TickerList
- Botão toggle para alternar entre edição (Text) e visualização (Listbox)
- Botões Selecionar Todos / Desmarcar Todos no modo visualização
- Preservação de seleção ao transitar entre modos
- Disparar recarga de dados ao sair do modo edição se a lista mudou
- Implementar lazy refresh: gráficos só renderizam quando a aba é selecionada
- Nenhuma alteração nos comboboxes ou na sincronia entre eles

**Non-Goals:**
- Não alterar o pipeline de dados (`_current_data`, use cases, domain)
- Não remover funcionalidades existentes (carregar/salvar arquivo, índices, menu de contexto)
- Não adicionar dependências externas
- Não alterar os charts (VWAPHistChart, QuadrantChart, DominanceRankingChart, DominanceTimelineChart)

## Decisions

### D1: Dois widgets empilhados (Text e Listbox) com pack_forget/pack alternados

Em vez de criar/destruir widgets a cada transição, ambos os widgets (Text e Listbox) são criados no `__init__` e empilhados no mesmo frame, mas apenas um é visível por vez usando `pack_forget()`/`pack()`.

```python
self._text = tk.Text(...)    # sempre existe
self._listbox = tk.Listbox(..., selectmode=tk.EXTENDED)  # sempre existe
# Alterna visibilidade:
self._text.pack_forget()
self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
```

**Alternativa considerada**: Destruir e recriar widgets. Rejeitada porque perderia o estado (seleção, scroll position).

### D2: Botão toggle nativo via tk.Checkbutton(indicatoron=0)

```python
self._edit_toggle = tk.Checkbutton(
    btn_frame, image=icon,
    command=self._on_mode_toggle, cursor="hand2", padx=0,
    indicatoron=0,  # parece um botão que fica pressionado
)
```

### D3: Botões Select All / Deselect All visíveis apenas no view mode

Frame separado `_view_btn_frame` (com os botões Select All / Deselect All) posicionado entre o label e o content frame. Mostrado/escondido junto com o Listbox.

### D4: Preservação de seleção via snapshot

Ao entrar no modo edição, salvar:
- `_view_tickers_snapshot: list[str]` — todos os tickers do Listbox
- `_view_selection_snapshot: set[str]` — tickers selecionados no Listbox

Ao sair do modo edição:
- Comparar `set(text_tickers)` com `set(_view_tickers_snapshot)`
- Nova seleção: `(selection_snapshot ∩ text_tickers) ∪ (text_tickers - snapshot_tickers)`
- Se `set(text_tickers) != set(snapshot)`: marcar `_list_changed = True`

### D5: Sinal de recarga via callback `on_data_needed`

Adicionar callback `on_data_needed` no TickerList, chamado pelo `FlowScopeGUI` quando a transição edit→view detecta mudança na lista. Este callback executa `_on_load_data()`.

### D6: Lazy refresh via bandeira `_charts_dirty`

Atributo `_charts_dirty: bool` no `FlowScopeGUI`:
- `True` após: carga de dados, mudança de seleção no Listbox, transição edit→view
- Verificado em `_on_tab_changed()`: se dirty, chama `_update_charts()` + `_update_ticker_indicator_tabs()` + `_update_ticker_counter()`, depois limpa bandeira

`_on_ticker_edit()` NÃO chama `_update_charts()` diretamente — apenas marca dirty.

Os callbacks de combobox (`_on_vwap_combo_selected`, etc.) continuam chamando `_update_charts()` como antes (comportamento original preservado). A diferença é que agora `_update_charts()` usa o `get_tickers()` que no view mode retorna só os selecionados.

### D7: `set_tickers()` adaptado para view mode

```python
def set_tickers(self, tickers: list[str]) -> None:
    self._set_view_mode(True)  # força modo visualização
    self._listbox.delete(0, tk.END)
    for t in tickers:
        self._listbox.insert(tk.END, t)
    self._select_all_listbox()  # marca todos
    self._text.delete("1.0", tk.END)
    self._text.insert("1.0", "\n".join(tickers))
    self._view_tickers_snapshot = list(tickers)
    self._view_selection_snapshot = set(tickers)
```

## Risks / Trade-offs

- [**UX**] Dois widgets empilhados ocupam o mesmo espaço. O frame do content area precisa ter `expand=True` para ambos funcionarem corretamente.
- [**Sincronia**] A transição edit→view pode disparar recarga de dados, que é uma operação cara (requisição B3). O usuário sente um delay ao apertar o toggle. Mitigação: só recarrega se a lista realmente mudou, e o loading state já existe.
- [**Memória**] Manter Text e Listbox em memória simultaneamente é negligenciável (tickers são strings curtas).
- [**Ícones**] `document-properties.png`, `edit-select-all.png` e `list-remove-all.png` precisam existir em `src/flowscope/icons/`. Se não existirem, usar fallback textual.
