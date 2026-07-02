## ADDED Requirements

### Requirement: Sub-aba Fluxo Financeiro ativa com painel visual

O sistema DEVE ativar a sub-aba "Fluxo Financeiro" (removendo-a do conjunto de abas desabilitadas) e exibir o `FinancialFlowPanel` no lugar do placeholder `tk.Text`.

#### Scenario: Fluxo Financeiro selecionável

- **WHEN** o usuário navega para a aba "Análise do Ticker"
- **THEN** a sub-aba "Fluxo Financeiro" DEVE estar ativa e selecionável

#### Scenario: FinancialFlowPanel exibido na sub-aba

- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o sistema DEVE exibir o `FinancialFlowPanel` com gauge, barra empilhada e classificação

### Requirement: Summary callback atualiza OrientationPanel dinamicamente

O sistema DEVE conectar o `summary_callback` do `FinancialFlowPanel` para atualizar dinamicamente o OrientationPanel com um resumo textual do fluxo financeiro, seguindo o mesmo padrão do gráfico de Quadrantes.

#### Scenario: OrientationPanel atualizado com resumo do fluxo

- **WHEN** o `FinancialFlowPanel` invoca `summary_callback(summary_text)`
- **THEN** o texto do OrientationPanel DEVE ser atualizado para incluir "---" seguido do summary_text, sem perder o conteúdo explicativo base

### Requirement: Indicators tab config atualizada

O sistema DEVE atualizar a configuração de indicadores da tab "Fluxo Financeiro" em `tab_configs` para refletir corretamente os indicadores utilizados pelo painel visual.

#### Scenario: Indicadores corretos na tab_config

- **WHEN** a sub-aba "Fluxo Financeiro" é selecionada
- **THEN** o sistema DEVE usar apenas os indicadores relevantes para o painel (daily_money_flow, money_flow_volume, clv, buying_pressure, selling_pressure, range_percentual)

## MODIFIED Requirements

### Requirement: OrientationPanel para conteúdo explicativo

O sistema DEVE exibir um OrientationPanel na barra lateral direita contendo título e texto explicativo fixo associado à sub-aba ativa. Cada sub-aba DEVE ter seu próprio conteúdo explicativo composto por (objetivo, pergunta respondida, indicadores envolvidos, como interpretá-lo), nesta ordem. O texto explicativo DEVE suportar formatação rica nativa: cabeçalhos de seção (Objetivo, Responde a pergunta, Indicadores envolvidos, Como interpretar) em **negrito** e perguntas em itálico. O método `set_content(title, body)` DEVE aceitar `body` como uma lista de tuplas `(str, str)` onde o segundo elemento é o nome da tag de formatação.

#### Scenario: OrientationPanel da sub-aba Fluxo Financeiro contém a pergunta atualizada

- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _O movimento de hoje foi sustentado por fluxo financeiro?_"

#### Scenario: OrientationPanel da sub-aba Fluxo Financeiro contém indicadores atualizados

- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o texto do OrientationPanel DEVE conter "Daily Money Flow (DMF)" e "Money Flow Volume acumulado"
