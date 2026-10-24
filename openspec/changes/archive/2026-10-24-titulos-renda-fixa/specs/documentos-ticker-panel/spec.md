## ADDED Requirements

### Requirement: Árvore de títulos de renda fixa

A sub-aba "Documentos" DEVE exibir, sob "Direitos e obrigações", os sub-ramos "Obrigações" e "Direitos", cada um com o sub-ramo "Títulos" e, abaixo dele, os tipos de título com dados ou com ausência de fonte explícita. Cada tipo DEVE conter títulos individuais, um nó agregado ou um nó de ausência de fonte, conforme a fonte disponível.

A árvore DEVE ser montada apenas a partir do cache normalizado do ticker apresentado, sem acionar download ou extração ao exibir a sub-aba. Pastas DEVEM expandir e recolher; somente documentos DEVEM abrir.

#### Scenario: Obrigações na árvore
- **WHEN** o ticker apresentado possui obrigações de renda fixa em cache
- **THEN** a árvore DEVE exibir Direitos e obrigações → Obrigações → Títulos → tipos e títulos

#### Scenario: Direitos na árvore
- **WHEN** o ticker apresentado possui direitos de renda fixa em cache
- **THEN** a árvore DEVE exibir Direitos e obrigações → Direitos → Títulos → tipos e títulos

#### Scenario: Agregado na árvore
- **WHEN** o tipo possui apenas total por ticker
- **THEN** a árvore DEVE exibir o nó agregado do tipo, com rótulo que o distinga de um título individual

#### Scenario: Ausência de fonte na árvore
- **WHEN** o tipo não possui título nem total público por emissor
- **THEN** a árvore DEVE exibir o nó de ausência de fonte do tipo

#### Scenario: Ramo vazio preservado
- **WHEN** o ticker não possui obrigações ou direitos em cache
- **THEN** o sub-ramo correspondente DEVE existir com a indicação de ausência de dados, sem erro

#### Scenario: Exibição sem aquisição
- **WHEN** o usuário abre a sub-aba "Documentos"
- **THEN** o sistema NÃO DEVE baixar nem extrair títulos ao montar a árvore

### Requirement: Pré-visualização de título de renda fixa

Ao selecionar um título individual, a sub-aba DEVE exibir em caixa somente-leitura as "Informações gerais", as "Informações adicionais", o "LTV" quando aplicável e os "Documentos relacionados". Ao selecionar um agregado, DEVE exibir o valor total, a fonte e a data de referência. Ao selecionar um nó de ausência de fonte, DEVE exibir a explicação correspondente.

A pré-visualização NÃO DEVE disparar extração de texto, resumo por LLM ou chamada à CVM/B3. O botão "Abrir documento" DEVE permanecer desabilitado para nós de título, agregado ou ausência de fonte. Os links de documentos relacionados DEVEM ser exibidos e DEVEM poder ser abertos externamente.

#### Scenario: Pré-visualização de título individual
- **WHEN** o usuário seleciona um título individual
- **THEN** a caixa de texto DEVE exibir informações gerais, adicionais, LTV quando houver e documentos relacionados

#### Scenario: Pré-visualização de agregado
- **WHEN** o usuário seleciona um nó agregado
- **THEN** a caixa de texto DEVE exibir o valor total, a fonte e a data de referência

#### Scenario: Pré-visualização de ausência de fonte
- **WHEN** o usuário seleciona um nó de ausência de fonte
- **THEN** a caixa de texto DEVE explicar a ausência de fonte pública por título ou por emissor

#### Scenario: Botão de abrir desabilitado
- **WHEN** o usuário seleciona um nó de título ou agregado
- **THEN** o botão "Abrir documento" DEVE permanecer desabilitado

#### Scenario: Link de documento relacionado
- **WHEN** a pré-visualização de um título lista um link de documento
- **THEN** o sistema DEVE permitir abrir o link externamente, sem baixar ou resumir conteúdo

### Requirement: Expansão e seleção dos nós de títulos

Os nós de Obrigações, Direitos, Títulos, tipos e títulos DEVEM participar do estado de expansão e de seleção da árvore como nós de grupo. Ao remontar a árvore do mesmo ticker, o sistema DEVE preservar a expansão e a seleção desses nós, sem tratá-los como arquivos.

#### Scenario: Expansão preservada
- **WHEN** o usuário expande Obrigações → Títulos → Debêntures e a árvore é remontada para o mesmo ticker
- **THEN** os nós expandidos DEVEM continuar abertos

#### Scenario: Seleção preservada
- **WHEN** um título está selecionado e a árvore é remontada para o mesmo ticker
- **THEN** o título DEVE voltar a ser selecionado, quando ainda existir

#### Scenario: Duplo-clique em nó de grupo
- **WHEN** o usuário dá duplo-clique em Obrigações, Direitos, Títulos, tipo ou título
- **THEN** o nó DEVE expandir ou recolher, sem abrir arquivo
