## ADDED Requirements

### Requirement: Sub-aba Fundamentos na Análise Geral
O sistema DEVE adicionar uma sub-aba "Fundamentos" ao sub-notebook da aba "Análise Geral", exibindo uma tabela fundamentalista para os tickers selecionados no Listbox.

#### Scenario: Sub-aba Fundamentos exibe tabela
- **WHEN** o usuário navega para a aba "Análise Geral" e seleciona a sub-aba "Fundamentos"
- **THEN** o sistema DEVE exibir uma tabela com uma linha por ticker selecionado no Listbox

#### Scenario: Tabela usa os tickers do Listbox
- **WHEN** o usuário seleciona 5 tickers no Listbox e navega para a sub-aba "Fundamentos"
- **THEN** a tabela DEVE exibir os dados fundamentalistas para os 5 tickers selecionados

### Requirement: Colunas da tabela fundamentalista
A tabela fundamentalista DEVE exibir, nesta ordem, as colunas: Ticker, Nome, Tipo, Sub-tipo, Última data-com, Último dividendo, Tendência do dividendo, e — para FIIs elegíveis — FFO Yield, Dividend Yield, P/FFO, P/VP e FFO Trend.

#### Scenario: Colunas de identidade preenchidas
- **WHEN** a tabela é renderizada para um ticker conhecido
- **THEN** as colunas Ticker, Nome, Tipo e Sub-tipo DEVEM estar preenchidas

#### Scenario: Colunas FFO vazias para não elegível
- **WHEN** a tabela é renderizada para um ativo que não é FII elegível (ex.: ação)
- **THEN** as colunas FFO Yield, Dividend Yield, P/FFO, P/VP e FFO Trend DEVEM exibir `N/A`

### Requirement: OrientationPanel para a sub-aba Fundamentos
O sistema DEVE exibir no OrientationPanel o conteúdo explicativo da sub-aba "Fundamentos", seguindo o padrão existente (objetivo, pergunta respondida, indicadores envolvidos e como interpretar).

#### Scenario: OrientationPanel da sub-aba Fundamentos
- **WHEN** o usuário seleciona a sub-aba "Fundamentos"
- **THEN** o OrientationPanel DEVE exibir texto explicativo sobre as métricas fundamentalistas e de dividendo exibidas na tabela
