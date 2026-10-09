## MODIFIED Requirements

### Requirement: Conhecimento do próprio FlowScope na árvore

O sistema DEVE compor o conhecimento do FlowScope a partir dos textos de orientação das sub-abas e das informações da aba Sobre (apresentação, licença, versão), expondo-o como os ramos `/flowscope/abas`, `/flowscope/abas/<aba>/subabas`, `/flowscope/indicadores` e `/flowscope/meta` da árvore de conhecimento. Os ramos `/flowscope/abas` e `/flowscope/indicadores` DEVEM ser expostos apenas quando tiverem itens; sem itens, o ramo DEVE ser omitido em vez de existir como folha vazia. O conteúdo pesado NÃO DEVE integrar o manifesto; a LLM DEVE obtê-lo por navegação, inclusive para perguntas sobre o próprio aplicativo.

#### Scenario: Pergunta sobre o próprio FlowScope
- **WHEN** o usuário pergunta o que é o FlowScope ou como funciona uma sub-aba
- **THEN** os ramos `/flowscope/abas`, `/flowscope/abas/<aba>/subabas` e `/flowscope/meta` DEVEM ser resolvíveis e o conteúdo DEVE estar acessível por `obter`

#### Scenario: Bloco presente nos dois chats
- **WHEN** uma pergunta é feita no Chat Geral ou no Chat Ticker
- **THEN** os ramos de conhecimento do FlowScope DEVEM existir na árvore

#### Scenario: Conhecimento descoberto por navegação
- **WHEN** a LLM precisa do propósito de uma aba ou sub-aba
- **THEN** ela DEVE descobri-lo por `listar`/`obter`, não por um bloco pré-injetado no manifesto

#### Scenario: Ramo de indicadores vazio é omitido
- **WHEN** não há indicadores curados para expor
- **THEN** o ramo `/flowscope/indicadores` NÃO DEVE existir e `existe(/flowscope/indicadores)` DEVE ser falso, sem erro

### Requirement: Fundamentos na árvore

O sistema DEVE expor os dados da tabela de fundamentos carregada no momento como os ramos `/fundamentos/tickers`, `/fundamentos/campos` e `/fundamentos/valores/<ticker>` da árvore, cobrindo a watchlist completa. Cada sub-ramo de fundamentos (`/fundamentos/tickers`, `/fundamentos/campos` e `/fundamentos/valores`) DEVE ser exposto apenas quando tiver itens; sem itens, DEVE ser omitido em vez de existir como folha vazia. O ticker referido na pergunta DEVE ser identificado pela LLM a partir do texto da pergunta, sem seletor de escopo na interface. Quando não houver dados carregados, o sistema DEVE orientar o usuário a carregá-los, sem falhar.

#### Scenario: Fundamentos da watchlist
- **WHEN** há fundamentos carregados e uma pergunta é feita na aba "Chat AI"
- **THEN** os tickers da watchlist completa DEVEM aparecer em `/fundamentos/tickers`

#### Scenario: Identificação do ticker pela LLM
- **WHEN** a pergunta menciona um ticker específico
- **THEN** a LLM DEVE identificar o ticker a partir da pergunta e obter a linha em `/fundamentos/valores/<ticker>`, sem que a interface ofereça um seletor de escopo

#### Scenario: Sem dados carregados
- **WHEN** não há fundamentos carregados
- **THEN** o sistema DEVE orientar a carregar os dados, sem erro

#### Scenario: Sub-ramo de fundamentos vazio é omitido
- **WHEN** há tickers mas não há campos ou valores serializados
- **THEN** os sub-ramos `/fundamentos/campos` e `/fundamentos/valores` NÃO DEVEM existir, sem gerar `nao_interno` ao navegar
