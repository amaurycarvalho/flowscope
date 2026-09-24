## Purpose

Disponibiliza o conteúdo das notícias em cache como fonte adicional de contexto da aba de chat "Chat AI", com a relevância por ticker inferida pela LLM.

## ADDED Requirements

### Requirement: Notícias no contexto do Chat AI

O sistema DEVE disponibilizar as notícias em cache como fonte adicional de contexto da aba "Chat AI", incluindo título, data, agência e o texto/resumo dos artigos do período.

#### Scenario: Pergunta sobre notícias
- **WHEN** o usuário pergunta sobre notícias recentes na aba "Chat AI"
- **THEN** o contexto DEVE incluir as notícias em cache do período

### Requirement: Relevância por ticker inferida pela LLM

O sistema NÃO DEVE exigir um seletor de escopo de ticker. As notícias do período DEVEM ser oferecidas ao contexto e a LLM DEVE selecionar as relacionadas ao ticker referido na pergunta, inferido a partir dela.

#### Scenario: Pergunta sobre um ticker
- **WHEN** a pergunta menciona um ticker específico
- **THEN** a LLM DEVE usar as notícias relacionadas a esse ticker, sem filtro prévio na montagem do contexto

#### Scenario: Pergunta geral de mercado
- **WHEN** a pergunta é sobre o mercado sem um ticker específico
- **THEN** as notícias do período DEVEM estar disponíveis no contexto

### Requirement: Integração com o ponto de extensão do llm-chat

O sistema DEVE registrar as notícias como fonte adicional de contexto por meio do ponto de extensão exposto pela change `llm-chat`, sem alterar a ordem da cascata de documentos.

#### Scenario: Fonte registrada
- **WHEN** a aba "Chat AI" monta o contexto
- **THEN** as notícias DEVEM ser consideradas uma fonte adicional, ao lado do conhecimento do FlowScope, dos fundamentos e dos documentos

#### Scenario: Cache frio de notícias
- **WHEN** não há notícias em cache
- **THEN** o contexto DEVE ser montado sem notícias, sem erro
