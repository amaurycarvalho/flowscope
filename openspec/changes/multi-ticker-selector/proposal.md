## Why

O painel de tickers (TickerList) atualmente é apenas um editor de texto — o usuário digita tickers manualmente, carrega de arquivo ou usa índices predefinidos. Não há suporte a seleção visual de múltiplos tickers para análise comparativa. Para selecionar um subconjunto, o usuário precisa apagar linhas do editor de texto, perdendo a lista original. Adicionar um modo visualização com Listbox de seleção múltipla permite marcar/desmarcar tickers interativamente, enquanto o modo edição preserva a capacidade de editar a lista livremente.

A seleção via Listbox torna redundantes os comboboxes de ticker da Análise Geral (VWAP, Quadrantes, Dominância), que foram removidos. A seleção do Listbox passa a controlar diretamente todos os gráficos.

## What Changes

- Adicionar botão toggle "Editar lista de tickers" (`document-properties.png`) entre "Salvar lista" e os botões de seleção. Alterna entre **modo edição** (Text widget, comportamento atual) e **modo visualização** (Listbox com `selectmode=EXTENDED`)
- **Modo visualização é o padrão** ao abrir o programa e após carga de dados
- No modo visualização: todos os tickers carregados aparecem no Listbox; exibir botões "Selecionar Todos" (`edit-select-all.png`) e "Desmarcar Todos" (`edit-unselect-all.png`) na barra superior, ao lado direito do toggle de edição, visíveis apenas no modo visualização
- Separadores verticais entre Salvar/Editar e entre seleção/índices
- Botão "Filtrar" removido (a seleção do Listbox já filtra)
- **Default**: após carga de dados, modo visualização com todos os tickers marcados
- Ao sair do modo edição: atualizar Listbox com os tickers do Text widget; tickers existentes preservam seu estado de marcação anterior; tickers novos entram marcados; se a lista mudou, disparar recarga de dados
- O `get_tickers()` retorna **todos os tickers** no modo edição (comportamento atual) e **apenas os tickers selecionados** no modo visualização
- `_ensure_tickers()` (carga de dados) usa `get_all_listbox_tickers()` — carrega **todos** os tickers, independente da seleção. O filtro de seleção só afeta a exibição nos painéis
- Comboboxes de ticker da Análise Geral (VWAP, Quadrantes, Dominância) **removidos**. A seleção via Listbox é suficiente
- A regra de quiver no painel Quadrantes é mantida: quando apenas 1 ticker está selecionado, exibe setas
- **Lazy refresh híbrido**: gráficos renderizam ao selecionar aba manualmente, mas a aba ativa é renderizada imediatamente após carga/filtro

## Capabilities

### New Capabilities
- `ticker-view-mode`: Modo visualização do TickerList com Listbox de seleção múltipla, toggle edição/visualização, e botões Selecionar Todos / Desmarcar Todos na barra superior

### Modified Capabilities
- `gui-interface`: O TickerList passa a ter dois modos (edição/visualização). Comboboxes de ticker da Análise Geral removidos. A atualização dos gráficos passa a ser lazy (híbrida: aba ativa imediata, demais ao selecionar).

## Impact

- `src/flowscope/presentation/gui/widgets/ticker_list.py`: Adicionar modo dual (Text/Listbox), toggle button, Select All/Deselect All na barra superior (visíveis só no view mode), lógica de transição entre modos com preservação de seleção e detecção de mudanças na lista, separadores visuais, botão Filtrar removido
- `src/flowscope/presentation/gui/app.py`: `_on_ticker_edit()` marca dirty + `_refresh_current_tab()`; `_on_tab_changed()` e `_refresh_current_tab()` chamam `_update_charts()`/`_update_ticker_indicator_tabs()` se dirty; `_on_load_data()` não substitui `self._tickers` nem chama `set_tickers()`; `_ensure_tickers()` usa `get_all_listbox_tickers()`; comboboxes da Análise Geral removidos junto com `_sync_ticker_selectors`, `_build_ticker_selector`, `_update_ticker_selectors` e handlers associados; `_update_charts()` simplificado (sem filtro por combo)
- Nenhuma alteração nos charts (VWAPHistChart, QuadrantChart, DominanceRankingChart, DominanceTimelineChart)
- Nenhuma dependência externa nova
