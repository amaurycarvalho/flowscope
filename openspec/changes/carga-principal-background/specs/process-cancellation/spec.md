## REMOVED Requirements

### Requirement: Botão de interromper processamento

**Reason**: A carga principal deixa de ser síncrona e passa a ser um processamento cancelável em background, invalidando a exclusão da carga principal do botão de interromper. O requisito é reescrito para abranger a carga principal.

**Migration**: Substituído pelo requisito "Botão de interromper processamento em background", que inclui a carga principal entre os processamentos que exibem o botão.

## ADDED Requirements

### Requirement: Botão de interromper processamento em background

O sistema DEVE exibir um botão de interromper com o ícone `process-stop.png` na barra de status, imediatamente à esquerda da barra de progresso, enquanto houver ao menos um processamento cancelável em background ativo, incluindo a carga principal de dados (download do portfólio e processamento de indicadores) e a análise fundamentalista. O botão NÃO DEVE ser exibido quando não houver processamento cancelável ativo.

#### Scenario: Botão visível durante a carga principal
- **WHEN** a carga principal de dados é iniciada em background
- **THEN** o botão de interromper DEVE ser exibido ao lado da barra de progresso

#### Scenario: Botão visível durante processamento em background
- **WHEN** a análise fundamentalista em background é iniciada
- **THEN** o botão de interromper DEVE ser exibido ao lado da barra de progresso

#### Scenario: Botão visível durante aquisição de documentos
- **WHEN** a aquisição de documentos de um ticker é iniciada em background
- **THEN** o botão de interromper DEVE ser exibido ao lado da barra de progresso

#### Scenario: Botão visível durante resumo em lote
- **WHEN** o resumo em lote dos documentos pendentes é iniciado em background
- **THEN** o botão de interromper DEVE ser exibido ao lado da barra de progresso

#### Scenario: Botão e barra somem ao fim do processamento
- **WHEN** o último processamento cancelável termina com sucesso
- **THEN** o botão de interromper e a barra de progresso DEVEM desaparecer da barra de status

## MODIFIED Requirements

### Requirement: Interrupção de todos os processamentos em background

Um único acionamento do botão de interromper DEVE sinalizar o cancelamento de todos os processamentos em background ativos, inclusive a carga principal e os jobs sobrepostos.

#### Scenario: Clique interrompe a carga principal
- **WHEN** o usuário aciona o botão de interromper com a carga principal em andamento
- **THEN** a carga principal DEVE encerrar sem aplicar resultado parcial à interface

#### Scenario: Clique interrompe a análise fundamentalista
- **WHEN** o usuário aciona o botão de interromper com a análise fundamentalista em andamento
- **THEN** a análise DEVE encerrar sem publicar resultado de sucesso

#### Scenario: Clique interrompe a aquisição de documentos
- **WHEN** o usuário aciona o botão de interromper com a aquisição de documentos em andamento
- **THEN** a aquisição DEVE encerrar sem continuar adquirindo os documentos restantes

#### Scenario: Clique interrompe o resumo em lote
- **WHEN** o usuário aciona o botão de interromper com o resumo em lote em andamento
- **THEN** o lote DEVE encerrar sem resumir os documentos restantes

#### Scenario: Jobs sobrepostos interrompidos em conjunto
- **WHEN** o usuário aciona o botão de interromper com mais de um processamento em background ativo
- **THEN** todos os processamentos ativos DEVEM encerrar

### Requirement: Token de cancelamento reiniciado por operação

Cada processamento em background DEVE observar o próprio token de cancelamento. A solicitação de cancelamento de um processamento NÃO DEVE ser herdada por um processamento que o substitui, de modo que uma nova carga principal iniciada sobre uma anterior não seja cancelada pela interrupção da anterior. A solicitação de interromper tudo DEVE alcançar os jobs ativos no momento do acionamento.

#### Scenario: Nova operação após interrupção não é cancelada
- **WHEN** o usuário interrompe um processamento, a interface fica ociosa e uma nova operação é iniciada
- **THEN** a nova operação DEVE executar normalmente, sem ser cancelada pela interrupção anterior

#### Scenario: Job sobreposto não limpa o pedido de cancelamento
- **WHEN** a interrupção é solicitada com jobs ativos e um novo job é iniciado enquanto um deles ainda está ativo
- **THEN** os jobs que estavam ativos DEVEM permanecer cancelados e o novo job DEVE iniciar com token limpo

#### Scenario: Job substituto não herda o cancelamento
- **WHEN** uma nova carga principal é iniciada enquanto uma anterior está ativa e é substituída
- **THEN** o job novo DEVE iniciar com token limpo e executar até concluir, sem observar o cancelamento do job substituído
