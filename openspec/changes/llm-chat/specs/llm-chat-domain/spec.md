## ADDED Requirements

### Requirement: Protocolo DocumentoIndexavel
O sistema DEVE definir um protocolo `DocumentoIndexavel` com método `to_text() -> str` que produz uma representação textual densa do documento, adequada para chunking e embedding. As entidades `DocumentoProvento` e `InformeMensal` das changes `fii-structured-earnings` e `fii-informe-mensal` DEVEM implementar este protocolo.

#### Scenario: DocumentoProvento implementa DocumentoIndexavel
- **WHEN** `DocumentoProvento.to_text()` é chamado
- **THEN** o texto DEVE conter nome do fundo, CNPJ, ticker, tipo de provento, valor, data, isento IR e nota de isenção em formato legível

#### Scenario: InformeMensal implementa DocumentoIndexavel
- **WHEN** `InformeMensal.to_text()` é chamado
- **THEN** o texto DEVE conter nome do fundo, CNPJ, composição da carteira com totais, resultados (receitas/despesas), indicadores, e outras informações

### Requirement: Entidade ChatMessage
O sistema DEVE possuir uma entidade `ChatMessage` dataclass com `role` ("user" ou "assistant"), `content` (str), `sources` (list[dict] opcional com metadados dos chunks-fonte) e `timestamp` (datetime).

#### Scenario: Mensagem do usuário
- **WHEN** `ChatMessage(role="user", content="Qual foi o último rendimento?")` é criada
- **THEN** `role` deve ser "user", `content` deve ser preservado, `sources` deve ser lista vazia

#### Scenario: Mensagem do assistente com fontes
- **WHEN** `ChatMessage(role="assistant", content="O último rendimento foi...", sources=[{"descricao": "Fato Relevante 15/07", "url": "..."}])` é criada
- **THEN** `sources` deve conter a lista de metadados para exibição na GUI

### Requirement: Entidade ChatSession
O sistema DEVE possuir uma entidade `ChatSession` (in-memory, sem persistência) contendo uma lista de `ChatMessage` e métodos `add_message(msg)` e `clear()`. Cada aba de chat começa com uma sessão limpa.

#### Scenario: Nova sessão vazia
- **WHEN** `ChatSession()` é criada
- **THEN** `messages` deve ser lista vazia

#### Scenario: Adicionar e limpar mensagens
- **WHEN** 3 mensagens são adicionadas e `clear()` é chamado
- **THEN** `messages` deve voltar a ser lista vazia

### Requirement: ABC DocumentSource
O sistema DEVE definir uma classe abstrata `DocumentSource` com métodos `listar(ticker, data_inicio, data_fim) -> list[dict]`, `obter_texto(doc_meta) -> str` e `categoria -> str`. Cada fonte concreta (Proventos, InformeMensal, Relevantes) implementa a ABC.

#### Scenario: DocumentSource define interface comum
- **WHEN** uma classe herda de `DocumentSource` e implementa todos os métodos abstratos
- **THEN** a classe deve ser aceita por `IndexarDocumentosUseCase` como fonte de documentos
