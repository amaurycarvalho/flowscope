## ADDED Requirements

### Requirement: Registro da sub-aba Rede de Correlação

O sistema DEVE registrar a sub-aba "Rede de Correlação" no sub-notebook da aba "Análise Geral", após a sub-aba "Dominância do Pregão", e DEVE incluí-la no despacho de atualização e no controle do botão "Copiar Gráfico". A preferência de última sub-aba selecionada DEVE passar a considerar a nova sub-aba.

#### Scenario: Sub-aba aparece após Dominância do Pregão

- **WHEN** o usuário navega para a aba "Análise Geral"
- **THEN** a sub-aba "Rede de Correlação" DEVE aparecer após "Dominância do Pregão"

#### Scenario: Atualização ao trocar para a sub-aba

- **WHEN** o usuário seleciona a sub-aba "Rede de Correlação"
- **THEN** o sistema DEVE atualizar o painel correspondente e o botão "Copiar Gráfico"

#### Scenario: Restauração da última sub-aba

- **WHEN** o usuário reabre a aplicação tendo selecionado "Rede de Correlação" por último
- **THEN** o sistema DEVE restaurar a sub-aba "Rede de Correlação"

### Requirement: OrientationPanel da sub-aba Rede de Correlação

O sistema DEVE exibir, no OrientationPanel, o conteúdo explicativo da sub-aba "Rede de Correlação" composto por objetivo, pergunta respondida, indicadores envolvidos e como interpretar, incluindo a explicação da codificação visual (cor da aresta para correlação, estilo/espessura para cointegração, cor do nó para cluster) e do gate de densidade da cointegração.

#### Scenario: Conteúdo explicativo ao selecionar a sub-aba

- **WHEN** o usuário seleciona a sub-aba "Rede de Correlação"
- **THEN** o OrientationPanel DEVE exibir o título e o texto explicativo da sub-aba, contendo Objetivo, Responde a pergunta, Indicadores envolvidos e Como interpretar

#### Scenario: Explicação da codificação visual

- **WHEN** o conteúdo da sub-aba "Rede de Correlação" é exibido
- **THEN** ele DEVE explicar que a cor da aresta representa a correlação de curto prazo e o estilo/espessura representa a cointegração de longo prazo

#### Scenario: Explicação do gate de densidade

- **WHEN** o conteúdo da sub-aba "Rede de Correlação" é exibido
- **THEN** ele DEVE explicar que a cointegração só é exibida quando há observações alinhadas suficientes
