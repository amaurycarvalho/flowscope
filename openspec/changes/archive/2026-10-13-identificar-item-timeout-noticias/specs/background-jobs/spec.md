## ADDED Requirements

### Requirement: Descrição da atividade corrente do job

O contexto entregue ao worker DEVE permitir descrever a atividade ou o item em processamento no momento. A descrição DEVE ficar disponível ao componente enquanto o job estiver ativo, para ser usada quando o job for encerrado involuntariamente. Atualizar a descrição NÃO DEVE contar como progresso para o watchdog, de modo que um item travado continue sendo detectado pela inatividade.

#### Scenario: Worker descreve o item corrente

- **WHEN** o worker descreve a atividade ou o item que está processando
- **THEN** a descrição DEVE ficar associada ao job ativo

#### Scenario: Descrever não impede o watchdog

- **WHEN** o worker atualiza a descrição mas permanece sem progresso além do limite de inatividade
- **THEN** o job DEVE continuar sendo encerrado por inatividade

## MODIFIED Requirements

### Requirement: Watchdog de inatividade e liveness centralizado

O componente DEVE detectar jobs que morreram sem publicar término e jobs sem progresso por tempo excessivo, encerrando-os com o desfecho `ABORTADO` e publicando o término para que a interface seja restaurada e informada do encerramento involuntário. O comportamento DEVE ser uniforme para todos os jobs gerenciados. Ao encerrar um job por inatividade ou por thread morta sem término, o componente DEVE registrar no log o identificador, o grupo e a descrição da atividade corrente informada pelo job, quando houver, de modo que o item em processamento no momento do encerramento seja identificável.

#### Scenario: Job morto sem término

- **WHEN** a thread de trabalho encerra sem publicar o término e a fila está vazia
- **THEN** o componente DEVE publicar o término do job com desfecho `ABORTADO`

#### Scenario: Job sem progresso por tempo excessivo

- **WHEN** um job permanece sem progresso além do limite de inatividade
- **THEN** o componente DEVE encerrá-lo com desfecho `ABORTADO` e publicar o término

#### Scenario: Encerramento involuntário nomeia a atividade corrente

- **WHEN** um job que descreveu a atividade corrente é encerrado por inatividade ou por thread morta sem término
- **THEN** o registro do encerramento DEVE incluir a descrição da atividade corrente

#### Scenario: Encerramento sem descrição permanece legível

- **WHEN** um job sem descrição de atividade é encerrado involuntariamente
- **THEN** o registro DEVE incluir o identificador e o grupo, sem exigir a descrição
