## MODIFIED Requirements

### Requirement: Orientação no quadro textual da aba "Chat AI"

Quando a aba "Chat AI" estiver ativa, o quadro de texto orientativo DEVE exibir a orientação própria da aba, cobrindo objetivo, requisitos de configuração e de fundamentos, as **origens do contexto como ramos da árvore de conhecimento**, o mecanismo de navegação da LLM por um protocolo JSON determinístico, os orçamentos de contexto relevantes, a leitura estritamente do cache local, a inferência de ticker e o uso dos botões. A orientação NÃO DEVE descrever a cascata de contexto (resumos curtos/longos encadeados e índice de notícias filtrado por casamento de título), que foi substituída pela árvore navegável.

#### Scenario: Aba ativa exibe orientação
- **WHEN** a aba "Chat AI" é selecionada
- **THEN** o quadro de texto orientativo DEVE exibir o texto da aba "Chat AI"

#### Scenario: Orientação descreve a árvore de conhecimento
- **WHEN** o texto da orientação da aba "Chat AI" é inspecionado
- **THEN** ele DEVE descrever as origens do contexto como ramos da árvore de conhecimento (conhecimento do FlowScope, fundamentos, documentos, notícias e, quando houver, guidance e direitos/obrigações) e o mecanismo de navegação da LLM sobre essa árvore

#### Scenario: Orientação não descreve a cascata
- **WHEN** o texto da orientação da aba "Chat AI" é inspecionado
- **THEN** ele NÃO DEVE mencionar cascata de contexto, resumos curtos/longos encadeados nem filtragem das notícias por casamento de título

#### Scenario: Orientação entra no conhecimento da LLM
- **WHEN** o bloco de conhecimento do FlowScope é montado
- **THEN** a orientação da aba "Chat AI" DEVE integrá-lo por vir de `TAB_CONTENT`
