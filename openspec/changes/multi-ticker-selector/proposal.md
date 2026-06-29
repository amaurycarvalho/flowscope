## Why

O painel de tickers (TickerList) atualmente é apenas um editor de texto — o usuário digita tickers manualmente, carrega de arquivo ou usa índices predefinidos. Não há suporte a seleção visual de múltiplos tickers para análise comparativa. Para selecionar um subconjunto, o usuário precisa apagar linhas do editor de texto, perdendo a lista original. Adicionar um modo visualização com Listbox de seleção múltipla permite marcar/desmarcar tickers interativamente, enquanto o modo edição preserva a capacidade de editar a lista livremente.

## What Changes

- Adicionar botão toggle "Editar lista de tickers" (`document-properties.png`) entre "Salvar lista" e "Filtrar", alternando entre **modo edição** (Text widget, comportamento atual) e **modo visualização** (Listbox com `selectmode=EXTENDED`)
- **Modo visualização é o padrão** ao abrir o programa e após carga de dados
- No modo visualização: todos os tickers carregados aparecem no Listbox; exibir botões "Selecionar Todos" (`edit-select-all.png`) e "Desmarcar Todos" (`list-remove-all.png`) que atuam no Listbox
- **Default**: após carga de dados, modo visualização com todos os tickers marcados
- Ao sair do modo edição: atualizar Listbox com os tickers do Text widget; tickers existentes preservam seu estado de marcação anterior; tickers novos entram marcados; se a lista mudou, disparar recarga de dados
- O `get_tickers()` retorna **todos os tickers** no modo edição (comportamento atual) e **apenas os tickers selecionados** no modo visualização
- `self._tickers` (usado pelos comboboxes da Análise Geral e Análise do Ticker) reflete o retorno de `get_tickers()`, portanto os comboboxes **não precisam de alteração** — "Todos" mostra naturalmente os tickers selecionados no Listbox
- **Lazy refresh**: a renderização de gráficos ocorre apenas quando o usuário seleciona a respectiva aba manualmente, evitando trabalho desnecessário

## Capabilities

### New Capabilities
- `ticker-view-mode`: Modo visualização do TickerList com Listbox de seleção múltipla, toggle edição/visualização, e botões Selecionar Todos / Desmarcar Todos

### Modified Capabilities
- `gui-interface`: O TickerList passa a ter dois modos (edição/visualização). A atualização dos gráficos passa a ser lazy (apenas ao selecionar a aba).

## Impact

- `src/flowscope/presentation/gui/widgets/ticker_list.py`: Adicionar modo dual (Text/Listbox), toggle button, Select All/Deselect All, lógica de transição entre modos com preservação de seleção e detecção de mudanças na lista
- `src/flowscope/presentation/gui/app.py`: `_on_ticker_edit()` não chama mais `_update_charts()` (apenas marca dirty); `_on_tab_changed()` passa a chamar `_update_charts()` e `_update_ticker_indicator_tabs()` se dirty; `_on_load_data()` usa view mode + all selected via `set_tickers()`; `_update_ticker_counter()` se adapta ao novo fluxo
- Nenhuma alteração nos comboboxes ou na sincronia entre eles
- Nenhuma dependência externa nova
