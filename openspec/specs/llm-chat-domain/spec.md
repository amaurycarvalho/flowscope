# llm-chat-domain Specification

## Purpose

Define as entidades de conversa em memória usadas pelas sub-abas de chat do FlowScope.

## Requirements

### Requirement: Entidade ChatMessage

O sistema DEVE possuir uma entidade `ChatMessage` dataclass com `role` ("user" ou "assistant"), `content` (str), `sources` (lista opcional com metadados dos chunks-fonte), `timestamp` (datetime) e `enviar_ao_modelo` (bool, `True` por padrão), que indica se a mensagem participa do histórico textual enviado à LLM. `sources` DEVE ser lista vazia quando não informada.

#### Scenario: Mensagem do usuário
- **WHEN** `ChatMessage(role="user", content="Qual foi o último rendimento?")` é criada
- **THEN** `role` DEVE ser "user", `content` DEVE ser preservado e `sources` DEVE ser lista vazia

#### Scenario: Mensagem do assistente com fontes
- **WHEN** `ChatMessage(role="assistant", content="O último rendimento foi...", sources=[{"descricao": "Fato Relevante 15/07"}])` é criada
- **THEN** `sources` DEVE conter a lista de metadados para exibição na GUI

#### Scenario: Mensagem fora do histórico do modelo
- **WHEN** `ChatMessage(role="assistant", content="...", enviar_ao_modelo=False)` é criada
- **THEN** `enviar_ao_modelo` DEVE ser `False`, sinalizando que a mensagem NÃO DEVE compor o histórico enviado à LLM

### Requirement: Entidade ChatSession

O sistema DEVE possuir uma entidade `ChatSession` in-memory, sem persistência, contendo uma lista de `ChatMessage` e os métodos `add_message(msg)` e `clear()`. A aba de chat DEVE começar com uma sessão limpa.

#### Scenario: Nova sessão vazia
- **WHEN** `ChatSession()` é criada
- **THEN** `messages` DEVE ser lista vazia

#### Scenario: Adicionar e limpar mensagens
- **WHEN** três mensagens são adicionadas e `clear()` é chamado
- **THEN** `messages` DEVE voltar a ser lista vazia
