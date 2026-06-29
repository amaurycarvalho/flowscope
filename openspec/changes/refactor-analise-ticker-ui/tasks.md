## 1. Remover combobox e implementar seleção via TickerList

- [ ] 1.1 Remover criação e packing do `self._ticker_combo` em `_build_main_area()`
- [ ] 1.2 Remover binding `<<ComboboxSelected>>` da linha 348
- [ ] 1.3 Remover handler `_on_ticker_combo_selected()` da linha 674
- [ ] 1.4 Adicionar método `_get_selected_ticker()` em `FlowScopeGUI` que retorna o primeiro ticker selecionado na TickerList, ou o primeiro da lista, ou `None`
- [ ] 1.5 Atualizar `_update_ticker_indicator_tabs()` para usar `_get_selected_ticker()` em vez de `self._ticker_combo.get()`
- [ ] 1.6 Atualizar `_on_ticker_edit()` para remover `self._ticker_combo["values"] = tickers`
- [ ] 1.7 Atualizar `_on_load_data()` para remover `self._ticker_combo["values"] = self._tickers` (linha 502)

## 2. Reordenar sub-abas da Análise do Ticker

- [ ] 2.1 Mover "Evolução da Dominância" para primeiro item em `tab_configs` em `_build_main_area()`
- [ ] 2.2 Atualizar `_tab_content` para ordenar as entradas na mesma ordem das abas

## 3. Redesenhar DominanceTimelineChart

- [ ] 3.1 Remover `_summary_frame`, `_summary_text`, e todo código associado do `__init__()`
- [ ] 3.2 Remover `_update_summary()` e sua chamada no final de `update()`
- [ ] 3.3 Remover `twiny()` e `self._eff_line` (linhas 139-147), incluindo a importação desnecessária
- [ ] 3.4 Atualizar `self._canvas.get_tk_widget().pack()` para remover `side=tk.LEFT`
- [ ] 3.5 Atualizar `_show_tooltip()` para exibir: Data, Dominância (label + CLV), Convicção (label + Eficiência em % com 1 casa decimal), MFV do pregão
- [ ] 3.6 Calcular percentual de pregões compradores (CLV > 0) e vendedores (CLV < 0) e atualizar os labels "Compradores X%" e "← Vendedores Y%" abaixo do eixo X
- [ ] 3.7 Atualizar `_on_motion()` e `_on_pick()` se necessário para compatibilidade com o novo tooltip

## 4. Verificação

- [ ] 4.1 Executar o aplicativo e verificar que carrega sem erros
- [ ] 4.2 Verificar que a seleção de ticker na TickerList atualiza as abas corretamente
- [ ] 4.3 Verificar que o gráfico "Evolução da Dominância" exibe barras, tooltips expandidos, e percentuais nos labels
- [ ] 4.4 Executar linter e typecheck
