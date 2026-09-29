## ADDED Requirements

### Requirement: Remontagem pelo término do job, sem polling na interface

A remontagem da árvore de notícias após um cancelamento DEVE ser disparada pelo término do job que ainda estava encerrando, não por um laço de espera ativa na thread da interface. A thread do Tk NÃO DEVE executar polling repetido (ex.: consultas periódicas `is_alive`) aguardando o worker terminar. A remontagem DEVE preservar a carga mais recente: se um novo "Atualizar" já tiver começado, a remontagem do job encerrado NÃO DEVE sobrescrever o resultado da carga nova.

#### Scenario: Cancelamento remonta sem polling
- **WHEN** o usuário cancela a aquisição de notícias
- **THEN** a árvore DEVE ser remontada com os itens já persistidos quando o job publicar o término, sem a thread da interface consultar periodicamente a thread de trabalho

#### Scenario: Carga nova tem precedência
- **WHEN** um novo "Atualizar" é iniciado antes de o worker cancelado encerrar
- **THEN** a remontagem do job encerrado NÃO DEVE sobrescrever a árvore da carga nova

#### Scenario: Interface não fica em espera ativa
- **WHEN** há um job de notícias em cancelamento
- **THEN** a thread da interface NÃO DEVE manter um laço de espera ativa enquanto o worker encerra
