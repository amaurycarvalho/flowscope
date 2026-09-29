## ADDED Requirements

### Requirement: Montagem assíncrona a partir do cache local

O sistema DEVE montar a árvore e a pré-visualização da sub-aba "Notícias" a partir do cache local fora da thread da interface, exibindo um estado de carregamento durante a leitura e aplicando o resultado por evento na thread do Tk. A leitura continua limitada ao cache local, sem consultar a B3, e trocar de aba ou acionar "Atualizar" DEVE descartar leituras obsoletas.

#### Scenario: Abertura com estado de carregamento
- **WHEN** a sub-aba "Notícias" é aberta
- **THEN** a leitura do cache local DEVE ocorrer fora da thread da interface e a árvore DEVE ser montada por evento ao concluir

#### Scenario: Interface responsiva durante a leitura
- **WHEN** a leitura do índice e a verificação do HTML dos itens está em andamento
- **THEN** a thread do Tk DEVE continuar processando eventos

#### Scenario: Sem consulta à B3
- **WHEN** a sub-aba "Notícias" é aberta ou o usuário troca de aba
- **THEN** nenhuma requisição à B3 DEVE ser feita durante a leitura do cache local

#### Scenario: Cache frio resulta em estado vazio
- **WHEN** não há índice nem itens em cache
- **THEN** a sub-aba DEVE exibir o estado vazio, sem erro

#### Scenario: Leitura obsoleta descartada
- **WHEN** uma nova leitura é iniciada antes de a anterior concluir
- **THEN** o resultado da leitura anterior NÃO DEVE sobrescrever a árvore montada pela mais recente
