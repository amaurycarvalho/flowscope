## MODIFIED Requirements

### Requirement: Colunas da tabela fundamentalista
A tabela fundamentalista DEVE exibir, nesta ordem, as colunas: Ticker, Nome, Tipo (`Papel`/`FII`), Sub-tipo, Última data-com, Último dividendo, Dividendo anterior, Tendência do dividendo, FFO Yield, Dividend Yield, Dividend Payout (DY/FFOY), FFO Trend, P (Cotação), VP (VP/Cota), P/FFO, P/VP, Nº de cotistas, Classe de cotistas, Patrimônio, Classe de patrimônio e Data de referência.

#### Scenario: Colunas de identidade preenchidas
- **WHEN** a tabela é renderizada para um ticker conhecido
- **THEN** as colunas Ticker, Nome, Tipo e Sub-tipo DEVEM estar preenchidas

#### Scenario: Coluna de dividendo anterior
- **WHEN** o ticker possui dividendo anterior consolidado
- **THEN** a coluna `Dividendo anterior` DEVE exibir o valor do dividendo imediatamente anterior ao último

#### Scenario: Dividend Payout (DY/FFOY)
- **WHEN** Dividend Yield e FFO Yield estão disponíveis para o ticker
- **THEN** a coluna `Dividend Payout (DY/FFOY)` DEVE exibir a razão entre Dividend Yield e FFO Yield

#### Scenario: Preço e VP/Cota
- **WHEN** a fonte fornece a cotação e o VP/Cota do ticker
- **THEN** as colunas `P (Cotação)` e `VP (VP/Cota)` DEVEM exibir esses valores

#### Scenario: Colunas FFO vazias para não elegível
- **WHEN** a fonte não fornece as métricas FFO para o ativo
- **THEN** as colunas FFO Yield, Dividend Yield, P/FFO, P/VP e FFO Trend DEVEM exibir `N/A`

#### Scenario: Métricas preenchidas quando disponíveis
- **WHEN** a fonte fornece as métricas para o ticker
- **THEN** FFO Yield, Dividend Yield, P/FFO, P/VP e FFO Trend DEVEM ser exibidos, inclusive para ativos antes considerados não elegíveis

#### Scenario: Novas colunas de cotistas e patrimônio
- **WHEN** a tabela é renderizada
- **THEN** as colunas de cotistas, classificação de cotistas, tamanho patrimonial, classificação patrimonial e data de referência DEVEM ser exibidas

## ADDED Requirements

### Requirement: Alinhamento das colunas numéricas
A tabela fundamentalista DEVE alinhar à direita o conteúdo das colunas Último dividendo, Dividendo anterior, FFO Yield, Dividend Yield, Dividend Payout (DY/FFOY), P (Cotação), VP (VP/Cota), P/FFO, P/VP, Nº de cotistas e Patrimônio, mantendo as demais colunas alinhadas à esquerda.

#### Scenario: Colunas numéricas alinhadas à direita
- **WHEN** a tabela é renderizada
- **THEN** as colunas Último dividendo, Dividendo anterior, FFO Yield, Dividend Yield, Dividend Payout (DY/FFOY), P (Cotação), VP (VP/Cota), P/FFO, P/VP, Nº de cotistas e Patrimônio DEVEM ter o conteúdo alinhado à direita

#### Scenario: Colunas textuais alinhadas à esquerda
- **WHEN** a tabela é renderizada
- **THEN** as colunas Ticker, Nome, Tipo, Sub-tipo, Última data-com, Tendência do dividendo, FFO Trend, Classe de cotistas, Classe de patrimônio e Data de referência DEVEM ter o conteúdo alinhado à esquerda
