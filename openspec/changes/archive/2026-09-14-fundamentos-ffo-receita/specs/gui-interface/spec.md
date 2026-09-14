## MODIFIED Requirements

### Requirement: Colunas da tabela fundamentalista

A tabela fundamentalista DEVE exibir, nesta ordem, as colunas: Ticker, Nome, Tipo (`Papel`/`FII`), Sub-tipo, P (Cotação), Preço Típico, P / PT, VP (VP/Cota), P/VP, P/L, Dividend Yield, Última data-com, Último dividendo, Dividendo anterior, Tendência do dividendo, FFO/Receita (12m), FFO/Receita (3m), FFO Trend, Dividendos/Receita (12m), Dividendos/Receita (3m), Dividendos/FFO (12m), Dividendos/FFO (3m), Nº de cotistas, Classe de cotistas, Patrimônio, Classe de patrimônio, Data de referência, Informações adicionais e Dados fiscais. As colunas `FFO Yield`, `P/FFO` e `Dividend Payout (DY/FFOY)` NÃO DEVEM mais ser exibidas.

#### Scenario: Colunas de identidade preenchidas
- **WHEN** a tabela é renderizada para um ticker conhecido
- **THEN** as colunas Ticker, Nome, Tipo e Sub-tipo DEVEM estar preenchidas

#### Scenario: Coluna de dividendo anterior
- **WHEN** o ticker possui dividendo anterior consolidado
- **THEN** a coluna `Dividendo anterior` DEVE exibir o valor do dividendo imediatamente anterior ao último

#### Scenario: Dividend Payout (DY/FFOY)
- **WHEN** a tabela é renderizada
- **THEN** a coluna `Dividend Payout (DY/FFOY)` NÃO DEVE mais ser exibida, sendo substituída por `Dividendos/FFO (12m)` e `Dividendos/FFO (3m)`

#### Scenario: Preço e VP/Cota
- **WHEN** a fonte fornece a cotação e o VP/Cota do ticker
- **THEN** as colunas `P (Cotação)` e `VP (VP/Cota)` DEVEM exibir esses valores

#### Scenario: Coluna P/L
- **WHEN** a tabela é renderizada
- **THEN** a coluna `P/L` DEVE ser exibida imediatamente após a coluna `P/VP`

#### Scenario: FFO Trend posicionado após a margem de 3 meses
- **WHEN** a tabela é renderizada
- **THEN** a coluna `FFO Trend` DEVE ser exibida imediatamente após a coluna `FFO/Receita (3m)`

#### Scenario: Razões exibidas em percentual com uma casa decimal
- **WHEN** as razões de um FII estão disponíveis
- **THEN** `FFO/Receita`, `Dividendos/Receita` e `Dividendos/FFO` (12m e 3m) DEVEM ser exibidos em notação percentual com uma casa decimal

#### Scenario: Insumo negativo exibe texto
- **WHEN** a Receita ou o FFO de um período é negativo
- **THEN** a célula da razão correspondente DEVE exibir `Receita negativa`, `FFO negativo` ou `Receita e FFO negativos`

#### Scenario: Colunas FFO vazias para não elegível
- **WHEN** o ticker é do tipo `Papel` ou a fonte não fornece os insumos das razões
- **THEN** as colunas `FFO/Receita`, `Dividendos/Receita` e `Dividendos/FFO` DEVEM exibir `N/A`

#### Scenario: Métricas preenchidas quando disponíveis
- **WHEN** a fonte fornece Receita, FFO e Rend. Distribuído do ticker
- **THEN** as razões `FFO/Receita`, `Dividendos/Receita` e `Dividendos/FFO` e o `FFO Trend` DEVEM ser exibidos

#### Scenario: Novas colunas de cotistas e patrimônio
- **WHEN** a tabela é renderizada
- **THEN** as colunas de cotistas, classificação de cotistas, tamanho patrimonial, classificação patrimonial e data de referência DEVEM ser exibidas

### Requirement: Alinhamento das colunas numéricas

A tabela fundamentalista DEVE alinhar à direita o conteúdo das colunas Último dividendo, Dividendo anterior, Dividend Yield, FFO/Receita (12m), FFO/Receita (3m), Dividendos/Receita (12m), Dividendos/Receita (3m), Dividendos/FFO (12m), Dividendos/FFO (3m), P (Cotação), Preço Típico, P / PT, VP (VP/Cota), P/L, P/VP, Nº de cotistas e Patrimônio, mantendo as demais colunas alinhadas à esquerda.

#### Scenario: Colunas numéricas alinhadas à direita
- **WHEN** a tabela é renderizada
- **THEN** as colunas Último dividendo, Dividendo anterior, Dividend Yield, FFO/Receita (12m), FFO/Receita (3m), Dividendos/Receita (12m), Dividendos/Receita (3m), Dividendos/FFO (12m), Dividendos/FFO (3m), P (Cotação), Preço Típico, P / PT, VP (VP/Cota), P/L, P/VP, Nº de cotistas e Patrimônio DEVEM ter o conteúdo alinhado à direita

#### Scenario: Colunas textuais alinhadas à esquerda
- **WHEN** a tabela é renderizada
- **THEN** as colunas Ticker, Nome, Tipo, Sub-tipo, Última data-com, Tendência do dividendo, FFO Trend, Classe de cotistas, Classe de patrimônio, Data de referência, Informações adicionais e Dados fiscais DEVEM ter o conteúdo alinhado à esquerda

### Requirement: OrientationPanel para a sub-aba Fundamentos

O sistema DEVE exibir no OrientationPanel o conteúdo explicativo da sub-aba "Fundamentos", seguindo o padrão existente (objetivo, pergunta respondida, indicadores envolvidos e como interpretar). O campo **Indicadores envolvidos** DEVE descrever todas as colunas exibidas na tabela, incluindo Preço Típico, P / PT, as razões `FFO/Receita`, `Dividendos/Receita` e `Dividendos/FFO` (12m e 3m), Informações adicionais e Dados fiscais. O campo **Como interpretar** DEVE conter orientações sucintas de leitura para essas colunas: `FFO/Receita` como quanto da receita vira caixa operacional; `Dividendos/Receita` como quanto da receita é destinado a dividendos; e `Dividendos/FFO` como quanto do caixa operacional é consumido pelos dividendos, abaixo de 100% o FFO cobre os dividendos, acima de 100% os dividendos superam o FFO e negativo o FFO foi negativo no período.

#### Scenario: OrientationPanel da sub-aba Fundamentos
- **WHEN** o usuário seleciona a sub-aba "Fundamentos"
- **THEN** o OrientationPanel DEVE exibir texto explicativo sobre as métricas fundamentalistas e de dividendo exibidas na tabela

#### Scenario: Indicadores envolvidos descrevem as colunas exibidas
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Indicadores envolvidos" DEVE mencionar Preço Típico, P / PT, as razões `FFO/Receita`, `Dividendos/Receita` e `Dividendos/FFO`, Informações adicionais e Dados fiscais, além de identidade, cotação, VP/Cota, P/VP, P/L, Dividend Yield, dividendos, tendências, cotistas/acionistas e patrimônio

#### Scenario: Identidade descreve o Tipo e o Sub-tipo implementados
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Indicadores envolvidos" DEVE descrever o Tipo como `Papel` (ações, ETFs e BDRs) ou `FII`, e o Sub-tipo como o prefixo `Tijolo:`/`Papel:` seguido de segmento e gestão para FIIs, ou espécie, setor e subsetor para Papéis, em vez dos rótulos genéricos ação/FII/ETF/BDR e tijolo/papel/híbrido/fiagro/fiinfra

#### Scenario: Como interpretar orienta o Preço Típico e o P / PT
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar que o Preço Típico é a referência de preço médio de 52 semanas e que o P / PT expressa desconto (negativo) ou prêmio (positivo) da cotação frente a esse preço típico

#### Scenario: Como interpretar orienta o Dividend Payout
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar que `Dividendos/FFO` abaixo de 100% indica que o FFO cobre os dividendos, acima de 100% que os dividendos superam o FFO e negativo que o FFO foi negativo no período, em substituição ao antigo Dividend Payout

#### Scenario: Como interpretar orienta Informações adicionais e Dados fiscais
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar que Informações adicionais reúnem indicadores do ativo (LPA, ROE e ROIC para ações; imóveis, Cap Rate, Vacância Média e indexadores para FIIs) e que Dados fiscais reúnem o CNPJ e, para FIIs, o administrador e o gestor, omitindo itens sem dado

#### Scenario: Orientação de leitura das razões
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar `FFO/Receita` como quanto da receita vira caixa operacional e `Dividendos/Receita` como quanto da receita é destinado a dividendos
