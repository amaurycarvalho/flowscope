## MODIFIED Requirements

### Requirement: Colunas da tabela fundamentalista
A tabela fundamentalista DEVE exibir, nesta ordem, as colunas: Ticker, Nome, Tipo (`Papel`/`FII`), Sub-tipo, Última data-com, Último dividendo, Tendência do dividendo, FFO Yield, Dividend Yield, P/FFO, P/VP, FFO Trend, número atual de cotistas, classificação por número de cotistas, tamanho patrimonial do fundo, classificação por tamanho patrimonial e data de referência dos dados.

#### Scenario: Colunas de identidade preenchidas
- **WHEN** a tabela é renderizada para um ticker conhecido
- **THEN** as colunas Ticker, Nome, Tipo e Sub-tipo DEVEM estar preenchidas

#### Scenario: Colunas FFO vazias para não elegível
- **WHEN** a fonte não fornece as métricas FFO para o ativo
- **THEN** as colunas FFO Yield, Dividend Yield, P/FFO, P/VP e FFO Trend DEVEM exibir `N/A`

#### Scenario: Métricas preenchidas quando disponíveis
- **WHEN** a fonte fornece as métricas para o ticker
- **THEN** FFO Yield, Dividend Yield, P/FFO, P/VP e FFO Trend DEVEM ser exibidos, inclusive para ativos antes considerados não elegíveis

#### Scenario: Novas colunas de cotistas e patrimônio
- **WHEN** a tabela é renderizada
- **THEN** as colunas de cotistas, classificação de cotistas, tamanho patrimonial, classificação patrimonial e data de referência DEVEM ser exibidas
