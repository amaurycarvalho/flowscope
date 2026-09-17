## Why

A aba "Análise do Ticker" hoje deriva o ticker analisado de duas fontes desconexas: a seleção na TickerList (que governa os gráficos de Dominância, Amplitude e Fluxo) e um ticker "fixado" por duplo-clique na tabela de Fundamentos (que governa apenas Evolução dos Fundamentos e Documentos). Isso torna o comportamento imprevisível e acopla a análise por ticker a um painel de filtragem que deveria servir a outro propósito. Além disso, a ordem das sub-abas não reflete a jornada do usuário e três sub-abas placeholder sem painel implementado permanecem visíveis como abas desabilitadas.

## What Changes

- Mover a sub-aba "Fundamentos" para a **primeira** posição na aba "Análise Geral".
- Reordenar as sub-abas da "Análise do Ticker": "Evolução dos Fundamentos" em primeiro e "Documentos" em último.
- Deixar **invisíveis** as três sub-abas sem painel implementado — "Participação Institucional", "Eficiência do Movimento" e "Resumo Geral" — que têm changes dedicadas (`participation-negociacoes`, `eficiencia-do-movimento`, `diagnosis-panel`).
- Tornar a linha selecionada na tabela da sub-aba "Fundamentos" a **fonte única** do ticker analisado em todas as sub-abas da "Análise do Ticker" (Dominância, Amplitude, Fluxo, Evolução dos Fundamentos e Documentos) e na cópia CSV dessa aba.
- Desvincular o ticker analisado da seleção na TickerList: a lista continua definindo **quais linhas** aparecem na tabela de Fundamentos e governa a "Análise Geral", mas não define mais o ticker das sub-abas por ticker.
- Ao carregar os fundamentos, **auto-selecionar a primeira linha** da tabela quando houver dados; sem dados, permanecer sem seleção e sem ticker analisado.
- Manter o duplo-clique na linha de Fundamentos como atalho: seleciona o ticker e navega para "Análise do Ticker" → "Evolução dos Fundamentos".
- **BREAKING** (comportamento observável): a seleção na TickerList deixa de atualizar as sub-abas da "Análise do Ticker"; o requisito correspondente é removido e substituído.

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `ticker-analysis`: a fonte do ticker analisado passa a ser a tabela de Fundamentos; a ordem das sub-abas muda; a visibilidade passa a mostrar somente sub-abas implementadas; o gatilho de atualização deixa de ser a TickerList.
- `gui-interface`: a sub-aba "Fundamentos" passa a ser a primeira sub-aba da "Análise Geral".

## Impact

- **Apresentação (GUI)**: `presentation/gui/app_tabs.py` (ordem de `TAB_CONFIGS`), `app_tab_layout.py` (ordem de `_build_general_tabs`, montagem de `_build_ticker_tabs` pulando sub-abas não habilitadas, religação do callback de seleção), `app_actions.py` (`_ticker_apresentado`, `_do_update`), `app_tab_actions.py` (`_on_fundamental_row_activated`, `_on_ticker_edit`), `app.py` (estado do ticker selecionado), `app_csv.py` (CSV da Análise do Ticker).
- **Widget de tabela**: `presentation/gui/charts/fundamental_table.py` — emitir callback de seleção de linha (clique simples) e expor o ticker selecionado.
- **Testes**: `tests/test_presentation/test_fundamental_evolution_integration.py`, `test_document_tree_panel.py`, `test_app_csv.py`, `test_fundamental_table.py` e testes de ordem/visibilidade de abas.
- **Specs**: `openspec/specs/ticker-analysis/spec.md` e `openspec/specs/gui-interface/spec.md`.
- **Sem novas dependências**, sem mudanças em infraestrutura, domínio ou casos de uso.
