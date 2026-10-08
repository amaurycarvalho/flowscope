## MODIFIED Requirements

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
