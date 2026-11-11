# Spec Delta — llm-chat-domain

## ADDED Requirements

### Requirement: Fonte consultada estruturada

O sistema DEVE representar cada fonte consultada como um valor com `caminho` textual obrigatório, correspondente a um caminho da árvore de conhecimento, e `rotulo` textual opcional. O caminho DEVE identificar a origem do dado e o rótulo DEVE ser apenas uma descrição legível, nunca a identidade da fonte.

#### Scenario: Fonte com caminho e rótulo
- **WHEN** uma fonte consultada é representada
- **THEN** ela DEVE conter o caminho da árvore e, quando houver, o rótulo legível

#### Scenario: Fonte sem rótulo
- **WHEN** uma fonte consultada é representada sem rótulo
- **THEN** o caminho DEVE ser preservado e o rótulo DEVE permanecer ausente

## MODIFIED Requirements

### Requirement: Entidade ChatMessage

O sistema DEVE possuir uma entidade `ChatMessage` dataclass com `role` ("user" ou "assistant"), `content` (str), `sources` (lista opcional de fontes consultadas estruturadas, cada uma com `caminho` e `rotulo` opcional), `timestamp` (datetime) e `enviar_ao_modelo` (bool, `True` por padrão), que indica se a mensagem participa do histórico textual enviado à LLM. `sources` DEVE ser lista vazia quando não informada.

#### Scenario: Mensagem do usuário
- **WHEN** `ChatMessage(role="user", content="Qual foi o último rendimento?")` é criada
- **THEN** `role` DEVE ser "user", `content` DEVE ser preservado e `sources` DEVE ser lista vazia

#### Scenario: Mensagem do assistente com fontes
- **WHEN** `ChatMessage(role="assistant", content="O último rendimento foi...", sources=[FonteChat(caminho="/documentos/PETR4/<chave>/texto", rotulo="Fato Relevante 15/07")])` é criada
- **THEN** `sources` DEVE conter a lista de fontes estruturadas para exibição na GUI

#### Scenario: Mensagem fora do histórico do modelo
- **WHEN** `ChatMessage(role="assistant", content="...", enviar_ao_modelo=False)` é criada
- **THEN** `enviar_ao_modelo` DEVE ser `False`, sinalizando que a mensagem NÃO DEVE compor o histórico enviado à LLM
