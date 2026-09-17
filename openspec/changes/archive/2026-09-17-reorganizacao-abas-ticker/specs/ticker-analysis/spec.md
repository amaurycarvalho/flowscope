## REMOVED Requirements

### Requirement: Seleção de ticker via TickerList

**Reason**: A seleção na TickerList passa a definir apenas quais tickers compõem a tabela de Fundamentos e os gráficos da "Análise Geral"; ela não define mais o ticker analisado na aba "Análise do Ticker".

**Migration**: O ticker analisado passa a ser a linha selecionada na tabela da sub-aba "Fundamentos" (ver requisito "Seleção de ticker via tabela de Fundamentos").

### Requirement: Placeholder para Participação Institucional

**Reason**: A sub-aba "Participação Institucional" não possui painel implementado e passa a não ser renderizada até que sua change dedicada (`participation-negociacoes`) a implemente e habilite.

**Migration**: A sub-aba será reintroduzida (renomeada para "Participação nas Negociações") pela change `participation-negociacoes`.

### Requirement: Placeholder para Eficiência do Movimento

**Reason**: A sub-aba "Eficiência do Movimento" não possui painel implementado e passa a não ser renderizada até que sua change dedicada (`eficiencia-do-movimento`) a implemente e habilite.

**Migration**: A sub-aba será reintroduzida pela change `eficiencia-do-movimento`.

### Requirement: Placeholder para Resumo Geral

**Reason**: A sub-aba "Resumo Geral" não possui painel implementado e passa a não ser renderizada até que sua change dedicada (`diagnosis-panel`) a substitua pelo painel "Diagnóstico".

**Migration**: A sub-aba será substituída pelo painel "Diagnóstico" pela change `diagnosis-panel`.

### Requirement: Reordenação das sub-abas

**Reason**: A ordem anterior ("Evolução da Dominância" em primeiro) não reflete a jornada do usuário nem a nova fonte de seleção do ticker; a ordem passa a ser definida pelo requisito "Ordem das sub-abas da Análise do Ticker".

**Migration**: Usar a nova ordem definida em "Ordem das sub-abas da Análise do Ticker".

## ADDED Requirements

### Requirement: Seleção de ticker via tabela de Fundamentos

O sistema DEVE derivar o ticker analisado na aba "Análise do Ticker" da linha selecionada na tabela da sub-aba "Fundamentos" (aba "Análise Geral"). A seleção da tabela DEVE ser a única fonte do ticker para todas as sub-abas de indicadores e para a cópia CSV da "Análise do Ticker". Quando houver dados de fundamentos, o sistema DEVE selecionar automaticamente a primeira linha da tabela; quando não houver dados, NÃO DEVE haver seleção nem ticker analisado.

#### Scenario: Linha selecionada define o ticker analisado

- **WHEN** o usuário seleciona a linha do ticker VALE3 na tabela de Fundamentos e navega para "Análise do Ticker"
- **THEN** todas as sub-abas de indicadores DEVEM exibir dados de VALE3

#### Scenario: Seleção inicial automática

- **WHEN** a análise fundamentalista conclui com dados para PETR4, VALE3 e ITUB4 e nenhuma linha está selecionada
- **THEN** o sistema DEVE selecionar automaticamente a primeira linha (PETR4) e usá-la como ticker analisado

#### Scenario: Sem dados não há ticker analisado

- **WHEN** não há dados de fundamentos carregados
- **THEN** a tabela NÃO DEVE ter linha selecionada e as sub-abas da "Análise do Ticker" NÃO DEVEM exibir indicadores de nenhum ticker

#### Scenario: Seleção desvinculada da TickerList

- **WHEN** o usuário altera a seleção na TickerList sem alterar a linha selecionada na tabela de Fundamentos
- **THEN** o ticker analisado nas sub-abas da "Análise do Ticker" DEVE permanecer o da tabela de Fundamentos

#### Scenario: Duplo-clique seleciona e navega

- **WHEN** o usuário dá duplo-clique em uma linha da tabela de Fundamentos
- **THEN** o sistema DEVE selecionar o ticker da linha e navegar para "Análise do Ticker" na sub-aba "Evolução dos Fundamentos"

#### Scenario: Seleção preservada após recarga

- **WHEN** os dados de fundamentos são recarregados e o ticker antes selecionado continua presente
- **THEN** a linha desse ticker DEVE permanecer selecionada e continuar sendo o ticker analisado

### Requirement: Ordem das sub-abas da Análise do Ticker

As sub-abas da "Análise do Ticker" DEVEM ser exibidas na ordem: "Evolução dos Fundamentos", "Evolução da Dominância", "Amplitude de Preço", "Fluxo Financeiro" e "Documentos". Somente sub-abas com painel implementado DEVEM ser renderizadas; sub-abas sem painel implementado NÃO DEVEM aparecer, nem mesmo como abas desabilitadas.

#### Scenario: Ordem das sub-abas

- **WHEN** o usuário navega para "Análise do Ticker"
- **THEN** a primeira sub-aba DEVE ser "Evolução dos Fundamentos" e a última "Documentos", seguidas por "Evolução da Dominância", "Amplitude de Preço" e "Fluxo Financeiro" nesta ordem

#### Scenario: Sub-abas sem painel não são exibidas

- **WHEN** o usuário navega para "Análise do Ticker"
- **THEN** as sub-abas "Participação Institucional", "Eficiência do Movimento" e "Resumo Geral" NÃO DEVEM estar presentes no notebook

## MODIFIED Requirements

### Requirement: Atualização ao trocar seleção

O sistema DEVE atualizar as sub-abas da "Análise do Ticker" quando o ticker selecionado na tabela de Fundamentos mudar. A atualização DEVE ocorrer ao exibir a aba ou quando a seleção mudar enquanto a aba estiver visível.

#### Scenario: Troca de ticker atualiza abas

- **WHEN** o usuário está na sub-aba "Evolução da Dominância" visualizando PETR4, volta para a tabela de Fundamentos, seleciona VALE3 e retorna para "Análise do Ticker"
- **THEN** o gráfico DEVE atualizar para mostrar dados de VALE3

#### Scenario: Mesmo ticker mantém os painéis

- **WHEN** o usuário retorna para "Análise do Ticker" sem alterar a linha selecionada na tabela de Fundamentos
- **THEN** os painéis DEVEM continuar exibindo o mesmo ticker
