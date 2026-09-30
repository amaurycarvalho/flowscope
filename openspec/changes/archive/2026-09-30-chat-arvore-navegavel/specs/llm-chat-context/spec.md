## REMOVED Requirements

### Requirement: Cascata de recuperação de documentos

**Reason**: A recuperação em cascata (resumos → texto integral) é substituída pela navegação da árvore de conhecimento, com granularidade fina por nó e seleção orientada pela LLM.

**Migration**: Usar os nós `/documentos/<ticker>/curto`, `/documentos/<ticker>/longo` e `/documentos/<ticker>/texto` da capability `llm-chat-tree`, navegados por `listar`/`obter`/`contar`/`buscar`.

### Requirement: Confirmação por quantidade de documentos-alvo

**Reason**: A confirmação por quantidade de documentos é substituída por um gate único de tokens de navegação por turno, que pede autorização pelo custo adicional real.

**Migration**: Usar o gate de tokens de navegação por turno da `llm-chat-llm` e a negativa estruturada da `llm-chat-tree`.

### Requirement: Contexto inicial sob demanda com janela de entrada limitada

**Reason**: O manifesto estável pequeno torna o parâmetro `input_limitado` desnecessário: o prefixo passa a conter apenas o manifesto e a LLM descobre os recursos navegando a árvore.

**Migration**: Remover `input_limitado`; o conhecimento, os fundamentos e os resumos passam a ser nós da árvore (`llm-chat-tree`).

### Requirement: Confirmação de recursos iniciais sob demanda

**Reason**: Sem `input_limitado`, não há carga especial de recursos iniciais a confirmar; o custo de navegação é governado pelo gate único de tokens.

**Migration**: Usar o gate de tokens de navegação por turno da `llm-chat-llm`.

### Requirement: Contexto estável com revalidação por assinatura

**Reason**: A revalidação por assinatura do bloco estável é absorvida pelo manifesto da árvore, que já define assinatura e reuso byte-a-byte.

**Migration**: Usar o requisito "Manifesto estável como prefixo cacheável" da `llm-chat-tree`.

### Requirement: Conhecimento do próprio FlowScope

**Reason**: O bloco de conhecimento deixa de ser um texto pré-montado e passa a ser exposto como ramos navegáveis da árvore.

**Migration**: Substituído por "Conhecimento do próprio FlowScope na árvore".

### Requirement: Contexto de fundamentos

**Reason**: Os fundamentos deixam de ser um bloco pré-injetado no prefixo e passam a ser ramos navegáveis da árvore.

**Migration**: Substituído por "Fundamentos na árvore".

## MODIFIED Requirements

### Requirement: Fontes adicionais de contexto

O sistema DEVE permitir registrar fontes adicionais de contexto no chat, além do conhecimento do FlowScope, dos fundamentos e dos documentos, expondo-as como ramos da árvore de conhecimento resolvíveis por caminho. Falha ou ausência de conteúdo de uma fonte adicional NÃO DEVE impedir a resposta nem quebrar os demais ramos.

#### Scenario: Fonte adicional presente
- **WHEN** uma fonte adicional retorna conteúdo para a pergunta
- **THEN** o seu conteúdo DEVE ser exposto como ramo da árvore e resolvido por caminho

#### Scenario: Fonte adicional indisponível
- **WHEN** uma fonte adicional falha ou retorna vazio
- **THEN** a árvore DEVE ser montada sem o ramo daquela fonte, sem erro e sem afetar os demais ramos

### Requirement: Orçamento de contexto

O sistema DEVE limitar o volume de texto de cada nó enviado à LLM por meio de tetos em tokens (por nó e por operação), truncando o excedente e registrando aviso no log quando o limite for atingido. Os tetos em caracteres DEVEM ser substituídos por tetos em tokens.

#### Scenario: Limite excedido
- **WHEN** o contexto montado excede o teto global
- **THEN** o conteúdo DEVE ser truncado e um aviso DEVE ser registrado no log

#### Scenario: Tetos em tokens por operação
- **WHEN** uma operação de navegação produz mais dados que o teto da operação
- **THEN** o resultado DEVE ser truncado conforme o teto, sinalizando o truncamento

## ADDED Requirements

### Requirement: Conhecimento do próprio FlowScope na árvore

O sistema DEVE compor o conhecimento do FlowScope a partir dos textos de orientação das sub-abas e das informações da aba Sobre (apresentação, licença, versão), expondo-o como os ramos `/flowscope/abas`, `/flowscope/abas/<aba>/subabas`, `/flowscope/indicadores` e `/flowscope/meta` da árvore de conhecimento. O conteúdo pesado NÃO DEVE integrar o manifesto; a LLM DEVE obtê-lo por navegação, inclusive para perguntas sobre o próprio aplicativo.

#### Scenario: Pergunta sobre o próprio FlowScope
- **WHEN** o usuário pergunta o que é o FlowScope ou como funciona uma sub-aba
- **THEN** os ramos `/flowscope/abas`, `/flowscope/abas/<aba>/subabas` e `/flowscope/meta` DEVEM ser resolvíveis e o conteúdo DEVE estar acessível por `obter`

#### Scenario: Bloco presente nos dois chats
- **WHEN** uma pergunta é feita no Chat Geral ou no Chat Ticker
- **THEN** os ramos de conhecimento do FlowScope DEVEM existir na árvore

#### Scenario: Conhecimento descoberto por navegação
- **WHEN** a LLM precisa do propósito de uma aba ou sub-aba
- **THEN** ela DEVE descobri-lo por `listar`/`obter`, não por um bloco pré-injetado no manifesto

### Requirement: Fundamentos na árvore

O sistema DEVE expor os dados da tabela de fundamentos carregada no momento como os ramos `/fundamentos/tickers`, `/fundamentos/campos` e `/fundamentos/valores/<ticker>` da árvore, cobrindo a watchlist completa. O ticker referido na pergunta DEVE ser identificado pela LLM a partir do texto da pergunta, sem seletor de escopo na interface. Quando não houver dados carregados, o sistema DEVE orientar o usuário a carregá-los, sem falhar.

#### Scenario: Fundamentos da watchlist
- **WHEN** há fundamentos carregados e uma pergunta é feita na aba "Chat AI"
- **THEN** os tickers da watchlist completa DEVEM aparecer em `/fundamentos/tickers`

#### Scenario: Identificação do ticker pela LLM
- **WHEN** a pergunta menciona um ticker específico
- **THEN** a LLM DEVE identificar o ticker a partir da pergunta e obter a linha em `/fundamentos/valores/<ticker>`, sem que a interface ofereça um seletor de escopo

#### Scenario: Sem dados carregados
- **WHEN** não há fundamentos carregados
- **THEN** o sistema DEVE orientar a carregar os dados, sem erro
