## Why

A sub-aba "Fluxo Financeiro" existe como placeholder desabilitado que exibe apenas texto cru de indicadores. Isso contrasta com o objetivo do FlowScope de "explicar o mercado, não apenas exibir indicadores". Um painel visual dedicado ao fluxo financeiro responde se o movimento do preço foi sustentado por capital, preenchendo uma lacuna importante na análise de convicção do mercado.

## What Changes

- Criar um painel visual matplotlib para a sub-aba "Fluxo Financeiro" em "Análise do Ticker"
- O painel substitui o atual `tk.Text` placeholder (desabilitado) por um gráfico rico com:
  - Gauge horizontal divergente do Daily Money Flow (indicador operacional)
  - Barra empilhada de Buying Pressure vs Selling Pressure
  - Marcador de CLV integrado ao gauge principal
  - Caixa de contexto com o Money Flow Volume acumulado do período
  - Classificação qualitativa baseada em score normalizado (|DMF|/fin_vol)
- Ativar a sub-aba (remover do conjunto `enabled_tabs`)
- Atualizar o OrientationPanel com novo conteúdo explicativo
- Adicionar `summary_callback` para resumo textual dinâmico
- Criar classificador `MoneyFlowClassifier` para classificação qualitativa do fluxo

## Capabilities

### New Capabilities
- `fluxo-financeiro-panel`: Painel visual que mostra o fluxo financeiro diário (Daily Money Flow) como gauge horizontal divergente, complementado por barra empilhada de Buying vs Selling Pressure, marcador de CLV, e classificação qualitativa baseada em score normalizado pelo volume financeiro.

### Modified Capabilities
- `gui-interface`: Ativar a sub-aba "Fluxo Financeiro" (remover do conjunto de abas desabilitadas). Atualizar OrientationPanel com novo conteúdo explicativo alinhado ao redesign. Adicionar cenário para o summary dinâmico via callback.

## Impact

- `src/flowscope/presentation/gui/app.py`: Ativar tab, adicionar instância do novo painel, conectar `summary_callback`, atualizar `_tab_content`
- `src/flowscope/presentation/gui/charts/`: Novo arquivo `financial_flow_panel.py` (~350-400 linhas)
- `src/flowscope/domain/strategies/classifiers/`: Novo arquivo `money_flow.py` com classificador de fluxo financeiro
- `openspec/specs/gui-interface/spec.md`: Atualizar cenários do OrientationPanel para Fluxo Financeiro
- Nenhuma mudança em indicadores existentes — `daily_money_flow`, `money_flow_volume`, `clv`, `buying_pressure`, `selling_pressure` já estão disponíveis
