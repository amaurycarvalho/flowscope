## MODIFIED Requirements

### Requirement: OrientationPanel para a sub-aba Fundamentos
O sistema DEVE exibir no OrientationPanel o conteúdo explicativo da sub-aba "Fundamentos", seguindo o padrão existente (objetivo, pergunta respondida, indicadores envolvidos e como interpretar). O campo **Indicadores envolvidos** DEVE descrever todas as colunas exibidas na tabela, incluindo Preço Típico, P / PT, Dividend Payout (DY/FFOY), Informações adicionais e Dados fiscais. O campo **Como interpretar** DEVE conter orientações sucintas de leitura para essas colunas.

#### Scenario: OrientationPanel da sub-aba Fundamentos
- **WHEN** o usuário seleciona a sub-aba "Fundamentos"
- **THEN** o OrientationPanel DEVE exibir texto explicativo sobre as métricas fundamentalistas e de dividendo exibidas na tabela

#### Scenario: Indicadores envolvidos descrevem as colunas exibidas
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Indicadores envolvidos" DEVE mencionar Preço Típico, P / PT, Dividend Payout (DY/FFOY), Informações adicionais e Dados fiscais, além de identidade, cotação, VP/Cota, P/VP, P/L, Dividend Yield, dividendos, tendências, métricas FFO, cotistas/acionistas e patrimônio

#### Scenario: Como interpretar orienta o Preço Típico e o P / PT
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar que o Preço Típico é a referência de preço médio de 52 semanas e que o P / PT expressa desconto (negativo) ou prêmio (positivo) da cotação frente a esse preço típico

#### Scenario: Como interpretar orienta o Dividend Payout
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar que o Dividend Payout compara o Dividend Yield com o FFO Yield, indicando quanto do retorno do FFO é distribuído como dividendo

#### Scenario: Como interpretar orienta Informações adicionais e Dados fiscais
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar que Informações adicionais reúnem indicadores do ativo (LPA, ROE e ROIC para ações; imóveis, Cap Rate, Vacância Média e indexadores para FIIs) e que Dados fiscais reúnem o CNPJ e, para FIIs, o administrador e o gestor, omitindo itens sem dado
