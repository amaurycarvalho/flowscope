## ADDED Requirements

### Requirement: Sub-aba Fundamentos exibe a análise fundamentalista real

A sub-aba "Fundamentos" da aba "Análise Geral" DEVE ser populada com a análise fundamentalista dos tickers carregados, exibindo, por ticker, a identidade (ticker, nome, tipo, sub-tipo), os dados de dividendo (última data-com, último dividendo e tendência) e as métricas disponíveis. Colunas cuja fonte ainda não está disponível DEVEM ser exibidas como `N/A`, sem impedir a exibição das demais.

#### Scenario: Tickers carregados populam a tabela
- **WHEN** o usuário carrega dados para uma watchlist e navega para a sub-aba "Fundamentos"
- **THEN** a tabela DEVE exibir uma linha por ticker com nome, tipo/sub-tipo e dados de dividendo preenchidos, e `N/A` nas métricas ainda indisponíveis

#### Scenario: Ticker sem dados fundamentalistas
- **WHEN** um ticker não resolve para identidade/proventos na B3
- **THEN** a tabela DEVE exibir a linha com os campos disponíveis e `N/A` nos demais, sem remover o ticker

### Requirement: Análise fundamentalista executada em background com progresso

A análise fundamentalista DEVE ser executada fora da thread da interface, de modo que a janela permaneça responsiva durante a aquisição, e DEVE reportar progresso por ticker/etapa na barra de status. A thread de trabalho NÃO DEVE acessar widgets do Tk diretamente; os resultados e o progresso DEVEM ser entregues à thread da interface por meio de uma fila consumida periodicamente.

#### Scenario: Interface responsiva durante a aquisição
- **WHEN** a análise fundamentalista está em andamento
- **THEN** a interface DEVE continuar respondendo a eventos e exibir progresso da operação

#### Scenario: Resultado entregue na thread da interface
- **WHEN** a thread de trabalho conclui a análise
- **THEN** os resultados DEVEM ser publicados na thread do Tk antes de atualizar a tabela

### Requirement: Descarte de resultados obsoletos

Quando uma nova carga de dados é iniciada antes da conclusão de uma análise fundamentalista anterior, o sistema DEVE descartar os resultados da execução obsoleta e exibir apenas os da carga mais recente.

#### Scenario: Nova carga invalida execução anterior
- **WHEN** o usuário inicia uma nova carga enquanto uma análise anterior ainda está em andamento
- **THEN** os resultados da execução anterior NÃO DEVEM ser exibidos na tabela

### Requirement: Atualização da tabela ao trocar de sub-aba

Os resultados da análise fundamentalista DEVEM ser armazenados por ticker e aplicados à tabela quando a sub-aba "Fundamentos" for selecionada, sem reexecutar a aquisição a cada troca de sub-aba.

#### Scenario: Troca para Fundamentos reutiliza resultados
- **WHEN** a análise já foi concluída e o usuário seleciona a sub-aba "Fundamentos"
- **THEN** a tabela DEVE ser atualizada com os resultados armazenados sem nova requisição à B3
