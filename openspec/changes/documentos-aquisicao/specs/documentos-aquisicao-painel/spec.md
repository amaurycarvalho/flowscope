## Purpose

Acionar a aquisição dos documentos ao abrir ou atualizar a sub-aba "Documentos", executando-a fora da thread da interface e refletindo o resultado na árvore do ticker apresentado.

## ADDED Requirements

### Requirement: Acionamento ao abrir a sub-aba

Ao se tornar ativa, a sub-aba "Documentos" DEVE acionar a aquisição dos documentos do ticker apresentado (o mesmo da sub-aba "Evolução dos Fundamentos") antes de montar a árvore, de modo que a árvore reflita os arquivos recém-adquiridos.

#### Scenario: Ativação dispara a aquisição
- **WHEN** a sub-aba "Documentos" se torna ativa para um ticker apresentado
- **THEN** o sistema DEVE acionar a aquisição dos documentos desse ticker e, ao concluir, remontar a árvore

#### Scenario: Ticker apresentado é usado
- **WHEN** há um ticker fixado nos Fundamentos
- **THEN** a aquisição DEVE usar esse mesmo ticker, mantendo a sincronização entre as sub-abas

### Requirement: Atualização manual dispara nova aquisição

O controle de atualização da sub-aba DEVE re-executar a aquisição do ticker apresentado e remontar a árvore.

#### Scenario: Atualização manual
- **WHEN** o usuário aciona o controle de atualização
- **THEN** o sistema DEVE re-adquirir os documentos e remontar a árvore do ticker apresentado

### Requirement: Estado de carregamento e execução fora da thread da interface

A aquisição DEVE ocorrer fora da thread da interface, com um estado de carregamento visível, e a árvore DEVE ser remontada na thread da interface ao término.

#### Scenario: Carregamento visível
- **WHEN** a aquisição é iniciada
- **THEN** o sistema DEVE exibir um estado de carregamento até a conclusão

#### Scenario: Interface não bloqueia
- **WHEN** a aquisição está em andamento
- **THEN** a thread da interface DEVE permanecer responsiva

### Requirement: Falha de aquisição não interrompe a interface

Uma falha de aquisição DEVE ser tolerada, mantendo a árvore montada a partir do cache existente, sem erro fatal.

#### Scenario: Falha de rede durante a aquisição
- **WHEN** a aquisição falha por indisponibilidade de rede
- **THEN** a sub-aba DEVE permanecer utilizável, exibindo os documentos já em cache

#### Scenario: Ticker sem documentos após a aquisição
- **WHEN** o ticker não possui documentos após a aquisição
- **THEN** a sub-aba DEVE exibir o estado vazio, sem erro
