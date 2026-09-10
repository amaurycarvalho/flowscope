## MODIFIED Requirements

### Requirement: Colunas da tabela fundamentalista
A tabela fundamentalista DEVE exibir, nesta ordem, as colunas: Ticker, Nome, Tipo (`Papel`/`FII`), Sub-tipo, P (Cotação), VP (VP/Cota), P/VP, P/L, Dividend Yield, Última data-com, Último dividendo, Dividendo anterior, Tendência do dividendo, FFO Yield, Dividend Payout (DY/FFOY), FFO Trend, P/FFO, Nº de cotistas, Classe de cotistas, Patrimônio, Classe de patrimônio e Data de referência.

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

#### Scenario: Coluna P/L
- **WHEN** a tabela é renderizada
- **THEN** a coluna `P/L` DEVE ser exibida imediatamente após a coluna `P/VP`

#### Scenario: Colunas FFO vazias para não elegível
- **WHEN** a fonte não fornece as métricas FFO para o ativo
- **THEN** as colunas FFO Yield, Dividend Yield, P/FFO, P/VP e FFO Trend DEVEM exibir `N/A`

#### Scenario: Métricas preenchidas quando disponíveis
- **WHEN** a fonte fornece as métricas para o ticker
- **THEN** FFO Yield, Dividend Yield, P/FFO, P/VP e FFO Trend DEVEM ser exibidos, inclusive para ativos antes considerados não elegíveis

#### Scenario: Novas colunas de cotistas e patrimônio
- **WHEN** a tabela é renderizada
- **THEN** as colunas de cotistas, classificação de cotistas, tamanho patrimonial, classificação patrimonial e data de referência DEVEM ser exibidas

### Requirement: Alinhamento das colunas numéricas
A tabela fundamentalista DEVE alinhar à direita o conteúdo das colunas Último dividendo, Dividendo anterior, FFO Yield, Dividend Yield, Dividend Payout (DY/FFOY), P (Cotação), VP (VP/Cota), P/L, P/FFO, P/VP, Nº de cotistas e Patrimônio, mantendo as demais colunas alinhadas à esquerda.

#### Scenario: Colunas numéricas alinhadas à direita
- **WHEN** a tabela é renderizada
- **THEN** as colunas Último dividendo, Dividendo anterior, FFO Yield, Dividend Yield, Dividend Payout (DY/FFOY), P (Cotação), VP (VP/Cota), P/L, P/FFO, P/VP, Nº de cotistas e Patrimônio DEVEM ter o conteúdo alinhado à direita

#### Scenario: Colunas textuais alinhadas à esquerda
- **WHEN** a tabela é renderizada
- **THEN** as colunas Ticker, Nome, Tipo, Sub-tipo, Última data-com, Tendência do dividendo, FFO Trend, Classe de cotistas, Classe de patrimônio e Data de referência DEVEM ter o conteúdo alinhado à esquerda

## ADDED Requirements

### Requirement: Rótulos descritivos das tendências

A tabela fundamentalista DEVE exibir rótulos descritivos em português para as colunas `FFO Trend` e `Tendência do dividendo`, em vez dos identificadores técnicos: `Forte Alta` para a faixa superior, `Leve Alta` para alta moderada, `Estável` para estabilidade, `Leve Queda` para queda moderada e `Forte Queda` para a faixa inferior, exibindo `N/A` quando a tendência não estiver disponível.

#### Scenario: Rótulos do FFO Trend
- **WHEN** a classificação do FFO Momentum é `FORTE_ALTA`, `ALTA`, `ESTAVEL`, `QUEDA` ou `FORTE_QUEDA`
- **THEN** a coluna `FFO Trend` DEVE exibir, respectivamente, `Forte Alta`, `Leve Alta`, `Estável`, `Leve Queda` ou `Forte Queda`

#### Scenario: Rótulos da Tendência do dividendo
- **WHEN** a classificação da tendência do dividendo é `FORTE_ALTA`, `ALTA`, `ESTAVEL`, `QUEDA` ou `FORTE_QUEDA`
- **THEN** a coluna `Tendência do dividendo` DEVE exibir, respectivamente, `Forte Alta`, `Leve Alta`, `Estável`, `Leve Queda` ou `Forte Queda`

#### Scenario: Tendência indisponível
- **WHEN** a tendência não está disponível
- **THEN** a coluna correspondente DEVE exibir `N/A`
