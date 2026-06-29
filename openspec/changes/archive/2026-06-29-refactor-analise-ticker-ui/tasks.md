## 1. Remover combobox e implementar seleção via TickerList

- [x] 1.1 Remover criação e packing do `self._ticker_combo` em `_build_main_area()`
- [x] 1.2 Remover binding `<<ComboboxSelected>>` da linha 348
- [x] 1.3 Remover handler `_on_ticker_combo_selected()` da linha 674
- [x] 1.4 Adicionar método `_get_selected_ticker()` em `FlowScopeGUI` que retorna o primeiro ticker selecionado na TickerList, ou o primeiro da lista, ou `None`
- [x] 1.5 Atualizar `_update_ticker_indicator_tabs()` para usar `_get_selected_ticker()` em vez de `self._ticker_combo.get()`
- [x] 1.6 Atualizar `_on_ticker_edit()` para remover `self._ticker_combo["values"] = tickers`
- [x] 1.7 Atualizar `_on_load_data()` para remover `self._ticker_combo["values"] = self._tickers` (linha 502)

## 2. Reordenar sub-abas da Análise do Ticker

- [x] 2.1 Mover "Evolução da Dominância" para primeiro item em `tab_configs` em `_build_main_area()`
- [x] 2.2 Atualizar `_tab_content` para ordenar as entradas na mesma ordem das abas

## 3. Redesenhar DominanceTimelineChart

- [x] 3.1 Remover `_summary_frame`, `_summary_text`, e todo código associado do `__init__()`
- [x] 3.2 Remover `_update_summary()` e sua chamada no final de `update()`
- [x] 3.3 Remover `twiny()` e `self._eff_line` (linhas 139-147), incluindo a importação desnecessária
- [x] 3.4 Atualizar `self._canvas.get_tk_widget().pack()` para remover `side=tk.LEFT`
- [x] 3.5 Atualizar `_show_tooltip()` para exibir: Data, Dominância (label + CLV), Convicção (label + Eficiência em % com 1 casa decimal), MFV do pregão
- [x] 3.6 Calcular percentual de pregões compradores (CLV > 0) e vendedores (CLV < 0) e atualizar os labels "Compradores X%" e "← Vendedores Y%" abaixo do eixo X
- [x] 3.7 Corrigir ordenação das datas (mais antiga acima, mais recente abaixo) — inverter ordem das linhas em `update()`
- [x] 3.8 Corrigir `_on_motion()` para detectar hover sobre qualquer parte da barra (entre 0 e CLV), não apenas próximo ao endpoint
- [x] 3.9 Elevar `zorder` da anotação do tooltip para 10 (acima dos stems MFV com zorder=5)

## 4. Corrigir DominanceRankingChart (mesmos bugs)

- [x] 4.1 Corrigir `_on_motion()` para detectar hover sobre qualquer parte da barra (entre 0 e CLV), não apenas próximo ao endpoint
- [x] 4.2 Elevar `zorder` da anotação do tooltip para 10
- [x] 4.3 Remover `import matplotlib` não utilizado

## 5. Adicionar labels "Compradores/Vendedores" ao QuadrantChart

- [x] 5.1 Inserir textos "Compradores →" e "← Vendedores" abaixo do eixo CLV no gráfico de quadrantes
- [x] 5.2 Remover variável `hover_index` não utilizada

## 6. Corrigir TickerList exportselection

- [x] 6.1 Adicionar `exportselection=False` ao `Listbox` para evitar que seleção externa (PRIMARY do X11) limpe a seleção interna da lista

## 7. Corrigir lazy refresh na troca de abas

- [x] 7.1 Remover gate `self._charts_dirty` em `_on_tab_changed()` para que a aba seja sempre atualizada ao navegar, não apenas quando dados são carregados

## 8. Verificação

- [x] 8.1 Executar o aplicativo e verificar que carrega sem erros
- [x] 8.2 Verificar que a seleção de ticker na TickerList atualiza as abas corretamente
- [x] 8.3 Verificar que o gráfico "Evolução da Dominância" exibe barras, tooltips expandidos, e percentuais nos labels
- [x] 8.4 Verificar que tooltips aparecem em qualquer parte da barra (não só no final)
- [x] 8.5 Verificar que tooltip fica acima dos stems MFV
- [x] 8.6 Executar linter e typecheck (ruff passa limpo)
- [x] 8.7 Executar testes: 131/131 passam
