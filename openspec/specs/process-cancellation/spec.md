# process-cancellation Specification

## Purpose

Permitir que o usuário interrompa processamentos longos executados em background (análise fundamentalista, aquisição de documentos e resumo em lote) por meio de um botão dedicado na barra de status, encerrando de fato o trabalho e devolvendo a interface ao estado ocioso.

## Requirements

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

### Requirement: Cancelamento cooperativo dos loops de trabalho

Os laços de trabalho dos processamentos em background DEVEM verificar a solicitação de cancelamento no início de cada unidade de trabalho e encerrar de imediato, descartando as unidades restantes. O cancelamento NÃO DEVE ser registrado nem apresentado como falha ou erro técnico.

#### Scenario: Loop encerra na próxima unidade após o pedido
- **WHEN** a solicitação de cancelamento é feita enquanto um loop processa uma lista de tickers, documentos ou resumos
- **THEN** o loop DEVE encerrar sem processar as unidades seguintes

#### Scenario: Cancelamento não é tratado como falha
- **WHEN** um processamento é interrompido pelo botão
- **THEN** o sistema NÃO DEVE registrar aviso de falha do job nem exibir mensagem de erro técnico

#### Scenario: Unidades já concluídas são preservadas
- **WHEN** a aquisição de documentos é interrompida após alguns documentos terem sido adquiridos
- **THEN** os documentos já adquiridos DEVEM permanecer disponíveis

#### Scenario: Resultado parcial da análise fundamentalista é descartado
- **WHEN** a análise fundamentalista é interrompida
- **THEN** os resultados já calculados NÃO DEVEM ser aplicados à interface

### Requirement: Desfecho visual da interrupção

Ao detectar a interrupção solicitada pelo usuário, o sistema DEVE finalizar a interface imediatamente, sem aguardar o término da thread de trabalho: o botão de interromper e a barra de progresso DEVEM desaparecer, os controles e o cursor DEVEM ser restaurados aos estados anteriores e a barra de status DEVE exibir "Processamento interrompido.". Mensagens de sucesso do processamento interrompido NÃO DEVEM ser exibidas.

Quando o término decorrer de encerramento involuntário pelo watchdog, o sistema DEVE finalizar a interface e exibir uma mensagem indicando o encerramento por inatividade, sem apresentar mensagem de sucesso. Quando o término decorrer de falha fatal que nenhum tratador de erro consumiu, o sistema DEVE exibir um aviso genérico de falha, orientando a consultar o log. Quando um tratador de erro já tiver exibido a mensagem específica da falha, essa mensagem NÃO DEVE ser sobrescrita pelo desfecho genérico. O aviso de desfecho NÃO DEVE ser emitido quando o job termina com sucesso.

#### Scenario: Barra e botão somem ao interromper

- **WHEN** o usuário aciona o botão de interromper
- **THEN** o botão e a barra de progresso DEVEM desaparecer sem aguardar o fim da thread de trabalho

#### Scenario: Mensagem de interrupção na barra de status

- **WHEN** o processamento é interrompido pelo usuário
- **THEN** a barra de status DEVE exibir "Processamento interrompido."

#### Scenario: Sucesso suprimido após interrupção

- **WHEN** o usuário interrompe a aquisição de documentos ou o resumo em lote
- **THEN** o sistema NÃO DEVE exibir as mensagens de sucesso "Documentos atualizados!" nem "Resumos gerados"

#### Scenario: Controles e cursor restaurados

- **WHEN** o processamento é interrompido pelo usuário
- **THEN** os controles DEVEM voltar aos estados anteriores e o cursor "watch" DEVE ser removido

#### Scenario: Encerramento involuntário informado

- **WHEN** um job é encerrado pelo watchdog por inatividade ou por thread morta sem término
- **THEN** a barra de status DEVE exibir uma mensagem informando o encerramento, e NÃO DEVE exibir "Processamento interrompido." nem mensagem de sucesso

#### Scenario: Falha fatal não reportada informada

- **WHEN** um job termina em falha fatal e nenhum tratador de erro exibiu mensagem
- **THEN** a barra de status DEVE exibir um aviso genérico de falha, e NÃO DEVE permanecer com a mensagem de sucesso anterior

#### Scenario: Falha fatal já reportada não é sobrescrita

- **WHEN** um job termina em falha fatal e o tratador de erro exibiu a mensagem específica
- **THEN** a mensagem específica DEVE ser preservada na barra de status

#### Scenario: Término com sucesso não emite aviso de desfecho

- **WHEN** um job termina com sucesso e nenhuma mensagem foi solicitada pelas ações do fluxo
- **THEN** o sistema NÃO DEVE emitir aviso de interrupção, aborto ou falha

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
