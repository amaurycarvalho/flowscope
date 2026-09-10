## MODIFIED Requirements

### Requirement: Análise fundamentalista executada em background com progresso

A análise fundamentalista DEVE ser executada fora da thread da interface, de modo que a janela permaneça responsiva durante a aquisição, e DEVE reportar progresso por ticker/etapa na barra de status. O progresso DEVE ser exibido na barra de progresso da barra de status, informando o número de tickers processados sobre o total, iniciando em `0/N` e avançando a cada ticker concluído. A thread de trabalho NÃO DEVE acessar widgets do Tk diretamente; os resultados e o progresso DEVEM ser entregues à thread da interface por meio de uma fila consumida periodicamente.

#### Scenario: Interface responsiva durante a aquisição
- **WHEN** a análise fundamentalista está em andamento
- **THEN** a interface DEVE continuar respondendo a eventos e exibir progresso da operação

#### Scenario: Resultado entregue na thread da interface
- **WHEN** a thread de trabalho conclui a análise
- **THEN** os resultados DEVEM ser publicados na thread do Tk antes de atualizar a tabela

#### Scenario: Barra de progresso inicia em zero
- **WHEN** a análise fundamentalista é iniciada
- **THEN** a barra de progresso DEVE ser exibida com `0/N` tickers processados

#### Scenario: Barra de progresso avança por ticker
- **WHEN** um ticker é concluído
- **THEN** a barra de progresso DEVE avançar para o número de tickers processados sobre o total

## ADDED Requirements

### Requirement: Glifos consistentes na barra de status

A barra de status DEVE usar glifos que renderizam de forma consistente nas plataformas suportadas. Mensagens de progresso DEVEM ser prefixadas por um marcador consistente (ex.: `•`) em vez do glifo de informação `ℹ`, mantendo os ícones de desfecho já existentes (ex.: `✓` e `⚠`).

#### Scenario: Progresso usa marcador consistente
- **WHEN** o progresso da análise fundamentalista é exibido
- **THEN** a mensagem DEVE usar um marcador que renderiza de forma consistente, e não o glifo `ℹ`

#### Scenario: Desfecho mantém os ícones existentes
- **WHEN** a carga conclui com sucesso ou com falha
- **THEN** os ícones de desfecho (`✓` e `⚠`) DEVEM ser mantidos
