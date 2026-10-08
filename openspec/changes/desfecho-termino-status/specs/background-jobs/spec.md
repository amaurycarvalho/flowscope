## ADDED Requirements

### Requirement: Desfecho terminal do job

O componente DEVE registrar e publicar, no término de cada job, um desfecho terminal entre `SUCESSO`, `FALHA`, `CANCELADO` e `ABORTADO`. O desfecho DEVE ser declarado pelo trabalho quando este recupera ou declara uma falha, e DEVE ser derivado automaticamente quando o trabalho retorna normalmente (`SUCESSO`), quando uma exceção não tratada escapa (`FALHA`) ou quando o cancelamento do job é solicitado (`CANCELADO`). O término NÃO DEVE classificar o job como `FALHA` a partir da mera presença de eventos de erro, para que falhas de item recuperadas pelo trabalho não sejam confundidas com falha do job.

#### Scenario: Retorno normal resulta em sucesso

- **WHEN** o trabalho retorna sem declarar falha
- **THEN** o desfecho do job DEVE ser `SUCESSO`

#### Scenario: Exceção não tratada resulta em falha

- **WHEN** o trabalho lança uma exceção que não trata
- **THEN** o desfecho do job DEVE ser `FALHA`

#### Scenario: Falha de item recuperada não classifica o job como falha

- **WHEN** o trabalho publica o erro de um item e prossegue, concluindo os demais
- **THEN** o desfecho do job NÃO DEVE ser `FALHA` por causa desse item

#### Scenario: Cancelamento resulta em cancelado

- **WHEN** o cancelamento do job é solicitado e o trabalho encerra
- **THEN** o desfecho do job DEVE ser `CANCELADO`

#### Scenario: Desfecho acompanha o término

- **WHEN** um job termina por qualquer desfecho
- **THEN** o evento de término entregue à interface DEVE carregar o desfecho do job

## MODIFIED Requirements

### Requirement: Watchdog de inatividade e liveness centralizado

O componente DEVE detectar jobs que morreram sem publicar término e jobs sem progresso por tempo excessivo, encerrando-os com o desfecho `ABORTADO` e publicando o término para que a interface seja restaurada e informada do encerramento involuntário. O comportamento DEVE ser uniforme para todos os jobs gerenciados.

#### Scenario: Job morto sem término

- **WHEN** a thread de trabalho encerra sem publicar o término e a fila está vazia
- **THEN** o componente DEVE publicar o término do job com desfecho `ABORTADO`

#### Scenario: Job sem progresso por tempo excessivo

- **WHEN** um job permanece sem progresso além do limite de inatividade
- **THEN** o componente DEVE encerrá-lo com desfecho `ABORTADO` e publicar o término
