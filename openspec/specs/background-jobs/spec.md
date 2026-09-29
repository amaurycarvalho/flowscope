# background-jobs Specification

## Purpose

Oferecer um ponto único para submeter, agendar, cancelar e observar processamentos assíncronos da interface, eliminando a orquestração duplicada de thread, fila, watchdog e drenagem hoje espalhada pelos jobs da camada de apresentação.

## Requirements

### Requirement: Submissão de trabalho assíncrono

O sistema DEVE oferecer um componente único que aceite um trabalho (uma chamada executável) e o execute fora da thread do Tk, devolvendo um identificador de job que permita acompanhar progresso, resultado, erro e término. O trabalho submetido NÃO DEVE executar na thread do Tk.

#### Scenario: Trabalho não bloqueia a interface

- **WHEN** um trabalho é submetido ao componente
- **THEN** a thread do Tk DEVE permanecer livre para processar eventos enquanto o trabalho executa

#### Scenario: Identificação do job

- **WHEN** um trabalho é submetido
- **THEN** o componente DEVE devolver um identificador que distinga aquele job dos demais ativos

### Requirement: Políticas de agendamento para requisições concorrentes

O componente DEVE permitir associar cada trabalho a uma política de agendamento que determine o comportamento quando outra requisição do mesmo grupo já estiver ativa: substituir a anterior (`latest_wins`), enfileirar serializando a execução (`serialize`) ou executar de forma independente (`parallel`).

#### Scenario: Substituição da requisição anterior

- **WHEN** um trabalho com política `latest_wins` é submetido enquanto outro do mesmo grupo está ativo
- **THEN** o job anterior DEVE ser cancelado e seu resultado descartado, e o novo job DEVE executar

#### Scenario: Requisição idêntica é descartada

- **WHEN** um trabalho `latest_wins` com uma `key` igual à de um job ativo do mesmo grupo é submetido
- **THEN** a nova requisição DEVE ser ignorada, sem cancelar nem reiniciar o job ativo

#### Scenario: Serialização de requisições

- **WHEN** um trabalho com política `serialize` é submetido enquanto outro do mesmo grupo está ativo
- **THEN** a nova requisição NÃO DEVE executar em paralelo com a ativa

#### Scenario: Execução independente

- **WHEN** um trabalho com política `parallel` é submetido enquanto outro do mesmo grupo está ativo
- **THEN** ambos os jobs DEVEM executar de forma independente, sem cancelar um ao outro

### Requirement: Cancelamento por job

Cada job DEVE observar o próprio token de cancelamento, independente dos demais jobs. Uma solicitação de cancelamento de um job NÃO DEVE afetar jobs não relacionados, e um job iniciado após uma substituição NÃO DEVE herdar a solicitação de cancelamento do job substituído.

#### Scenario: Cancelamento isolado por job

- **WHEN** o cancelamento de um job é solicitado
- **THEN** apenas esse job DEVE encerrar, preservando os demais jobs ativos

#### Scenario: Job substituto não herda cancelamento

- **WHEN** um job é substituído por outro da mesma política `latest_wins`
- **THEN** o novo job DEVE iniciar com token de cancelamento limpo

#### Scenario: Cancelamento cooperativo no laço de trabalho

- **WHEN** o cancelamento de um job em laço é solicitado
- **THEN** o laço DEVE verificar o token no início de cada unidade e encerrar sem processar as seguintes

### Requirement: Drenagem única de eventos na thread do Tk

O componente DEVE publicar os eventos de progresso, resultado, erro e término por meio de uma fila e drená-los em um único ponto agendado na thread do Tk, entregando cada evento ao callback registrado. As mensagens de um job substituído DEVEM ser descartadas.

#### Scenario: Eventos entregues na thread do Tk

- **WHEN** um worker publica um evento
- **THEN** o callback correspondente DEVE ser invocado na thread do Tk

#### Scenario: Drenagem independe de job ativo

- **WHEN** o último job é cancelado antes de sua fila ser drenada
- **THEN** os eventos terminais DEVEM ser consumidos e o estado da interface DEVE ser restaurado sem aguardar a thread de trabalho encerrar

#### Scenario: Evento de job obsoleto é descartado

- **WHEN** um job substituído publica um evento depois de perder a vez
- **THEN** o evento NÃO DEVE alterar o estado apresentado

### Requirement: Isolamento de thread entre worker e widgets

O worker NÃO DEVE acessar widgets do Tk nem estruturas exclusivas da thread do Tk; toda atualização de interface DEVE ocorrer a partir dos callbacks executados na thread do Tk.

#### Scenario: Worker não toca em widget

- **WHEN** um trabalho é executado pelo componente
- **THEN** ele DEVE comunicar resultados apenas por eventos, sem manipular widgets diretamente

### Requirement: Watchdog de inatividade e liveness centralizado

O componente DEVE detectar jobs que morreram sem publicar término e jobs sem progresso por tempo excessivo, encerrando-os e publicando o término para que a interface seja restaurada. O comportamento DEVE ser uniforme para todos os jobs gerenciados.

#### Scenario: Job morto sem término

- **WHEN** a thread de trabalho encerra sem publicar o término e a fila está vazia
- **THEN** o componente DEVE publicar o término do job

#### Scenario: Job sem progresso por tempo excessivo

- **WHEN** um job permanece sem progresso além do limite de inatividade
- **THEN** o componente DEVE encerrá-lo e publicar o término

### Requirement: Ciclo de vida refletido no estado ocupado

O componente DEVE publicar eventos de início e fim de cada job para que a autoridade de estado ocupado contabilize operações ativas, o botão de interromper e o cursor, mantendo a contagem equilibrada mesmo em substituição, cancelamento ou falha.

#### Scenario: Início e fim equilibrados

- **WHEN** um job é submetido e depois termina por sucesso, erro ou cancelamento
- **THEN** a contagem de operações ativas DEVE retornar ao valor anterior

#### Scenario: Substituição mantém o equilíbrio

- **WHEN** um job é substituído por outro antes de concluir
- **THEN** o término do job substituído DEVE ser contabilizado e a interface DEVE permanecer no estado ocupado pelo job novo
