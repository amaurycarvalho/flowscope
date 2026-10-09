## MODIFIED Requirements

### Requirement: Conhecimento do próprio FlowScope na árvore

O sistema DEVE compor o conhecimento do FlowScope a partir dos textos de orientação das sub-abas e das informações da aba Sobre (apresentação, licença, versão), expondo-o como os ramos `/flowscope/abas`, `/flowscope/abas/<aba>`, `/flowscope/abas/<aba>/subabas`, `/flowscope/indicadores` e `/flowscope/meta` da árvore de conhecimento. Os ramos `/flowscope/abas` e `/flowscope/indicadores` DEVEM ser expostos apenas quando tiverem itens; sem itens, o ramo DEVE ser omitido em vez de existir como folha vazia. O ramo `/flowscope/abas/<aba>` DEVE existir como nó interno navegável cujos filhos são as sub-abas. A LLM DEVE conseguir descobrir os nomes das abas e das sub-abas por navegação, e o manifesto DEVE anunciar o caminho da aba e as sub-abas de cada aba. O conteúdo pesado NÃO DEVE integrar o manifesto (nem como metadado): a LLM DEVE obtê-lo por navegação, inclusive para perguntas sobre o próprio aplicativo.

#### Scenario: Pergunta sobre o próprio FlowScope
- **WHEN** o usuário pergunta o que é o FlowScope ou como funciona uma sub-aba
- **THEN** os ramos `/flowscope/abas`, `/flowscope/abas/<aba>/subabas` e `/flowscope/meta` DEVEM ser resolvíveis e o conteúdo DEVE estar acessível por `obter`

#### Scenario: Bloco presente nos dois chats
- **WHEN** uma pergunta é feita no Chat Geral ou no Chat Ticker
- **THEN** os ramos de conhecimento do FlowScope DEVEM existir na árvore

#### Scenario: Conhecimento descoberto por navegação
- **WHEN** a LLM precisa do propósito de uma aba ou sub-aba
- **THEN** ela DEVE descobri-lo por `listar`/`obter`, não por um bloco pré-injetado no manifesto

#### Scenario: Aba navegável e sub-abas descobertas
- **WHEN** a LLM lista `/flowscope/abas` e em seguida `/flowscope/abas/<aba>`
- **THEN** o manifesto DEVE anunciar o caminho da aba e as sub-abas DEVEM ser descobríveis por `listar`, para a LLM obter o texto desejado sem adivinhar nomes

#### Scenario: Ramo de indicadores vazio é omitido
- **WHEN** não há indicadores curados para expor
- **THEN** o ramo `/flowscope/indicadores` NÃO DEVE existir e `existe(/flowscope/indicadores)` DEVE ser falso, sem erro
