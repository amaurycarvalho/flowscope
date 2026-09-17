## 1. Reordenar a "Análise Geral"

- [x] 1.1 Em `presentation/gui/app_tab_layout.py`, mover o bloco que constrói a sub-aba "Fundamentos" (`FundamentalTablePanel`) para o início de `_build_general_tabs`, antes de "VWAP"; verificar que a primeira sub-aba de `_general_notebook` é "Fundamentos" com um teste de widget (`test_fundamental_table.py`).
- [x] 1.2 (Opcional) Avaliar alterar o default `last_subtab` de `"VWAP"` para `"Fundamentos"` em `app_layout.py`/`app.py`; registrar a decisão e verificar que a restauração de aba continua funcionando.

## 2. Reordenar e ocultar sub-abas da "Análise do Ticker"

- [x] 2.1 Em `presentation/gui/app_tabs.py`, reordenar `TAB_CONFIGS` para: "Evolução dos Fundamentos", "Evolução da Dominância", "Amplitude de Preço", "Fluxo Financeiro", seguidos das três abas ainda não implementadas e, por último, "Documentos"; verificar que `ENABLED_TABS` não muda.
- [x] 2.2 Em `presentation/gui/app_tab_layout.py`, alterar `_build_ticker_tabs` para **não adicionar** frames cujo nome não está em `ENABLED_TABS` (em vez de `state="disabled"`); verificar que as sub-abas ocultas não aparecem no notebook.
- [x] 2.3 Remover o ramo `else` do placeholder `tk.Text` e o dicionário `_ticker_indicator_frames` (write-only) se não houver mais leitores; verificar com `ruff check src/` e pela suíte de testes.
- [x] 2.4 Adicionar/ajustar teste que verifica a ordem exata das sub-abas visíveis e a ausência de "Participação Institucional", "Eficiência do Movimento" e "Resumo Geral".

## 3. Seleção do ticker na tabela de Fundamentos

- [x] 3.1 Em `presentation/gui/charts/fundamental_table.py`, adicionar o parâmetro `on_ticker_selected` e disparar o callback no `<<TreeviewSelect>>` apenas da árvore de origem, sob o guard `_syncing_selection`; verificar com teste de widget que um clique simples notifica o ticker uma única vez.
- [x] 3.2 Expor um método para ler o ticker selecionado (ex.: `get_selected_ticker()`) e um para (re)selecionar uma linha por ticker; verificar com teste de unidade.
- [x] 3.3 Em `presentation/gui/app_tab_layout.py`, ligar `on_ticker_selected` à GUI e, após cada `update()` da tabela, reaplicar a seleção guardada ou auto-selecionar a primeira linha; sem linhas, limpar a seleção; verificar com teste de integração (auto-seleção, preservação e estado vazio).

## 4. Fonte única do ticker na GUI

- [x] 4.1 Em `app.py`, substituir `_evolution_ticker` por `_ticker_selecionado` (inicialmente `None`) e ajustar referências; verificar que a aplicação inicializa sem erro (`ruff check` + testes).
- [x] 4.2 Em `app_actions.py`, fazer `_ticker_apresentado()` retornar apenas `_ticker_selecionado` e usar `_ticker_apresentado()` em `_do_update` também para os gráficos de Dominância, Amplitude e Fluxo; remover o fallback para `_get_selected_ticker()`; verificar com testes de `_do_update`/`_ticker_apresentado`.
- [x] 4.3 Em `app_tab_actions.py`, ajustar `_on_fundamental_row_activated` para apenas navegar (a seleção já define o ticker) e `_on_ticker_edit` para não alterar o ticker analisado; verificar com testes atualizados.
- [x] 4.4 Em `app_csv.py`, usar `_ticker_apresentado()` no CSV da "Análise do Ticker"; verificar com `test_app_csv.py`.

## 5. Verificação final

- [x] 5.1 Atualizar os testes que referenciam `_evolution_ticker`/fonte pela TickerList (`test_fundamental_evolution_integration.py`, `test_document_tree_panel.py`, `test_app_csv.py`) e garantir que a suíte passa.
- [x] 5.2 Executar `make test` (ou `pytest`) e `make lint`; verificar que passam sem regressões.
- [x] 5.3 Validação manual da jornada: carregar dados, confirmar "Fundamentos" como primeira sub-aba da "Análise Geral", selecionar uma linha e conferir que todas as sub-abas da "Análise do Ticker" exibem o mesmo ticker, com as abas ocultas ausentes.
