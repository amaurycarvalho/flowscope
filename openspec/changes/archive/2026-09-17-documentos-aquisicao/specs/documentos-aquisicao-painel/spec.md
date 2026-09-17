## Purpose

Exibir o catálogo de documentos em cache ao abrir a sub-aba "Documentos" e acionar, apenas sob demanda pelo usuário, a aquisição de novos documentos em thread de trabalho, refletindo o resultado na árvore do ticker apresentado.

## ADDED Requirements

### Requirement: Exibição do catálogo de leitura ao abrir a sub-aba

Ao se tornar ativa, a sub-aba "Documentos" DEVE exibir apenas os documentos constantes no catálogo de leitura do cache do ticker apresentado (o mesmo da sub-aba "Evolução dos Fundamentos"), sem acionar nenhuma aquisição ou download.

#### Scenario: Ativação exibe o cache
- **WHEN** a sub-aba "Documentos" se torna ativa para um ticker apresentado
- **THEN** o sistema DEVE montar a árvore somente com os documentos do catálogo de leitura do cache, sem realizar download

#### Scenario: Ticker sem documentos em cache
- **WHEN** o ticker apresentado não possui documentos no catálogo de leitura
- **THEN** a sub-aba DEVE exibir o estado vazio, sem acionar aquisição

#### Scenario: Ticker apresentado é usado
- **WHEN** há um ticker selecionado na tabela de Fundamentos
- **THEN** a exibição DEVE usar esse mesmo ticker, mantendo a sincronização entre as sub-abas

### Requirement: Atualização manual dispara nova aquisição

O botão "Atualizar" da sub-aba DEVE acionar a aquisição dos documentos do ticker apresentado em uma janela de 12 meses até a data de referência, reutilizando sem novo download os documentos já existentes em cache e remontando a árvore ao final.

#### Scenario: Atualização manual
- **WHEN** o usuário aciona o botão "Atualizar"
- **THEN** o sistema DEVE adquirir os documentos da janela de 12 meses até a data de referência e remontar a árvore do ticker apresentado

#### Scenario: Documentos já em cache não são rebaixados
- **WHEN** um documento da janela de 12 meses já existe em cache
- **THEN** o sistema DEVE reutilizá-lo sem novo download

#### Scenario: Sem aquisição configurada apenas revarre
- **WHEN** o botão "Atualizar" é acionado sem callback de aquisição definido
- **THEN** o sistema DEVE apenas revarrer o catálogo de leitura do cache

### Requirement: Botão "Abrir documento" habilitado conforme a seleção

O botão de abertura DEVE ser rotulado "Abrir documento" e DEVE permanecer desabilitado enquanto nenhum arquivo estiver selecionado, habilitando-se apenas quando um documento for selecionado na árvore.

#### Scenario: Nenhum documento selecionado
- **WHEN** a sub-aba é exibida sem arquivo selecionado
- **THEN** o botão "Abrir documento" DEVE estar desabilitado

#### Scenario: Documento selecionado
- **WHEN** o usuário seleciona um arquivo na árvore
- **THEN** o botão "Abrir documento" DEVE estar habilitado

#### Scenario: Pasta selecionada
- **WHEN** o usuário seleciona uma pasta (ticker, ano, mês ou categoria) na árvore
- **THEN** o botão "Abrir documento" DEVE permanecer desabilitado

### Requirement: Estado de carregamento, progresso e execução fora da thread da interface

A aquisição acionada pelo botão "Atualizar" DEVE ocorrer fora da thread da interface. Enquanto estiver em execução, o sistema DEVE desabilitar os botões da aplicação (incluindo os botões "Atualizar" e "Abrir documento" da sub-aba), ativar o cursor de espera (hourglass) e atualizar a barra de status e a barra de progresso com o andamento da aquisição; ao término, DEVE restaurar os controles e remontar a árvore na thread da interface. Os botões "Atualizar" e "Abrir documento" DEVEM integrar o mesmo mecanismo de bloqueio global dos demais botões, ficando desabilitados durante qualquer operação da aplicação.

#### Scenario: Andamento visível
- **WHEN** a aquisição é iniciada
- **THEN** o sistema DEVE exibir o andamento na barra de status e na barra de progresso até a conclusão

#### Scenario: Controles bloqueados durante a aquisição
- **WHEN** a aquisição está em andamento
- **THEN** os botões da aplicação DEVEM estar desabilitados e o cursor de espera (hourglass) ativo

#### Scenario: Botões bloqueados durante outras operações
- **WHEN** uma carga de dados ou outra operação da aplicação está em andamento
- **THEN** os botões "Atualizar" e "Abrir documento" da sub-aba DEVEM estar desabilitados, como os demais botões da aplicação

#### Scenario: "Abrir documento" reavaliado ao restaurar
- **WHEN** a operação termina
- **THEN** o botão "Abrir documento" DEVE refletir a seleção corrente, habilitado apenas quando houver um documento selecionado

#### Scenario: Restauração ao término
- **WHEN** a aquisição termina, com sucesso ou falha
- **THEN** os botões DEVEM ser restaurados, a barra de progresso limpa e a árvore remontada

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
