## Why

A "Análise do Ticker" possui um combobox para selecionar o ticker analisado, mas a lista de tickers no painel direito (TickerList) já oferece seleção múltipla — o combobox é redundante e adiciona complexidade desnecessária. Além disso, o painel "Evolução da Dominância" exibe um resumo lateral e uma linha de eficiência que podem ser integrados diretamente nos tooltips das barras, simplificando o layout e eliminando duplicação visual.

## What Changes

- **Remover combobox de seleção de ticker** na aba "Análise do Ticker". O ticker analisado passa a ser o primeiro item selecionado na TickerList (painel direito). Se nenhum estiver selecionado, usa o primeiro da lista. Se a lista estiver vazia, exibe "Selecione um ticker".
- **Reordenar as sub-abas** da "Análise do Ticker": "Evolução da Dominância" passa a ser a primeira aba, antes de "Amplitude de Preço".
- **Redesenhar o gráfico "Evolução da Dominância"** (DominanceTimelineChart):
  - Remover o painel lateral de resumo (summary frame + text widget)
  - Remover a linha de eficiência (eixo secundário twiny + plot)
  - Mover as informações do resumo lateral para o tooltip de cada barra: Data, Dominância (label + CLV), Convicção (label + Eficiência em %), MFV do pregão
  - Incluir percentual de pregões nos labels "Compradores" e "Vendedores" abaixo do gráfico
  - Manter o estilo visual similar ao "Dominância do Pregão" (label nas extremidades das barras, marcador MFV via hlines)
- **Corrigir hover nos charts de barra** (DominanceTimelineChart e DominanceRankingChart): tooltip agora detecta mouse sobre qualquer ponto da barra (entre 0 e CLV), não apenas próximo ao endpoint
- **Corrigir zorder do tooltip** em ambos os charts de barra: tooltip agora renderiza acima dos stems MFV
- **Corrigir ordenação das datas** no DominanceTimelineChart: mais antiga no topo, mais recente embaixo
- **Adicionar labels "Compradores/Vendedores"** no QuadrantChart, abaixo do eixo CLV
- **Corrigir TickerList**: adicionar `exportselection=False` para evitar que seleção externa (X11 PRIMARY) limpe a seleção interna
- **Corrigir lazy refresh**: `_on_tab_changed()` agora sempre atualiza a aba atual ao navegar, não apenas quando `_charts_dirty` está True
- **Atualizar spec `ticker-analysis`** para refletir a nova mecânica de seleção (sem combobox)
- **Atualizar spec `dominance-timeline-panel`** para refletir o novo design (sem painel lateral, sem linha de eficiência, tooltip expandido)

## Capabilities

### New Capabilities

- *(none — todas as alterações são modificações em capacidades existentes)*

### Modified Capabilities

- `ticker-analysis`: Mecanismo de seleção de ticker muda de combobox para primeiro item selecionado na TickerList. Aba "Evolução da Dominância" reposicionada como primeira sub-aba.
- `dominance-timeline-panel`: Gráfico redesenhado — remove painel lateral de resumo, remove overlay de eficiência, expande tooltips, adiciona percentuais nos labels de buyer/seller.

## Impact

- **`src/flowscope/presentation/gui/app.py`**: Remover criação/bind/handlers do combobox; adicionar método `_get_selected_ticker()`; reordenar `tab_configs`; atualizar `_update_ticker_indicator_tabs()`, `_on_ticker_edit()`, `_on_load_data()`; atualizar textos de ajuda no `_tab_content`.
- **`src/flowscope/presentation/gui/charts/dominance_timeline.py`**: Remover `_summary_frame`, `_summary_text`, `_update_summary()`, `twiny()`, `_eff_line`; refatorar `update()`, `_show_tooltip()`, `_on_motion()`, `_on_pick()`; adicionar cálculo de percentuais e labels "Vendedores/Compradores" com percentual.
- **`src/flowscope/presentation/gui/widgets/ticker_list.py`**: Nenhuma alteração necessária — o callback `_on_listbox_select` já dispara `_on_change()` em view mode.
