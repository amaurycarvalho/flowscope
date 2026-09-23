## MODIFIED Requirements

### Requirement: OrientationPanel da sub-aba Evolução dos Fundamentos

O OrientationPanel DEVE exibir conteúdo explicativo da sub-aba "Evolução dos Fundamentos", composto por objetivo, pergunta respondida, indicadores envolvidos e como interpretar, no mesmo padrão das demais sub-abas. O campo **Indicadores envolvidos** DEVE descrever os oito campos exibidos, incluindo `Shorts%`, e o campo **Como interpretar** DEVE mencionar que o painel mostra oito mini-gráficos (small multiples) e que o `Shorts%` representa a magnitude relativa da aposta baixista.

#### Scenario: Conteúdo explicativo ao selecionar a sub-aba

- **WHEN** o usuário seleciona a sub-aba "Evolução dos Fundamentos"
- **THEN** o OrientationPanel DEVE exibir o título e o texto explicativo da sub-aba, com as seções no padrão existente

#### Scenario: Indicadores envolvidos descrevem os oito campos

- **WHEN** o OrientationPanel da sub-aba "Evolução dos Fundamentos" é exibido
- **THEN** o campo "Indicadores envolvidos" DEVE mencionar Cotação, VP (VP/Cota), P/VP, Dividend Yield, Último dividendo, Nº de cotistas, Nº de cotas e `Shorts%`

#### Scenario: Como interpretar menciona os oito mini-gráficos

- **WHEN** o OrientationPanel da sub-aba "Evolução dos Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE mencionar que o painel exibe oito mini-gráficos e DEVE explicar o `Shorts%` como a magnitude relativa da aposta baixista
