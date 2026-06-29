## MODIFIED Requirements

### Requirement: Contagem de tickers

O sistema DEVE exibir um label ao lado do campo de tickers indicando a quantidade total ou selecionada, dependendo do modo atual:
- Modo visualização: "Tickers (N)" com N = total de tickers no Listbox; "Exibindo M de N ativos" quando M < N selecionados
- Modo edição: "Tickers (N)" com N = total de tickers no Text widget

#### Scenario: Label no modo visualização com todos marcados

- **WHEN** dados de 37 tickers são carregados e todos estão marcados no Listbox
- **THEN** o label DEVE mostrar "Tickers (37)"

#### Scenario: Label no modo visualização com seleção parcial

- **WHEN** o usuário desmarca 10 dos 37 tickers no Listbox
- **THEN** o label DEVE mostrar "Exibindo 27 de 37 ativos"

#### Scenario: Label no modo edição

- **WHEN** o usuário alterna para modo edição com 37 tickers carregados
- **THEN** o label DEVE mostrar "Tickers (37)"

### Requirement: OrientationPanel com lazy refresh

O OrientationPanel DEVE ser atualizado sempre que o usuário navegar entre sub-abas, independentemente do estado de `charts_dirty`. O painel de orientação NÃO DEVE seguir a regra de lazy refresh — apenas os gráficos e indicadores seguem.

#### Scenario: OrientationPanel atualizado sem refresh de gráfico

- **WHEN** o usuário modifica a seleção de tickers e navega para uma sub-aba
- **THEN** o OrientationPanel DEVE exibir o conteúdo explicativo da sub-aba selecionada, mesmo que os gráficos não tenham sido re-renderizados
