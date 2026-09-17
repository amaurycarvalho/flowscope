## ADDED Requirements

### Requirement: Protocolo DocumentoIndexavel
O sistema DEVE definir um protocolo `DocumentoIndexavel` com método `to_text() -> str`, que produz uma representação textual densa do documento, adequada para chunking e embedding. As entidades de documento já implementadas que possuem `to_text()` (por exemplo, `DocumentoProvento`, `DocumentoMaterialFact`, `Assembleia` e `NoticiaB3`) satisfazem este protocolo.

#### Scenario: Documento com to_text
- **WHEN** `DocumentoProvento.to_text()` é chamado
- **THEN** o texto DEVE conter os metadados e valores do documento em formato legível

#### Scenario: Documento sem to_text não é indexável
- **WHEN** uma entidade não implementa `to_text()`
- **THEN** ela NÃO DEVE ser aceita como `DocumentoIndexavel` pelo pipeline

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
O sistema DEVE definir uma classe abstrata `DocumentSource` com a propriedade `categoria -> str` e o método `obter_documentos(ticker: str | None = None) -> list[DocumentoIndexavel]`. Cada fonte concreta implementa a ABC e isola o pipeline de indexação.

#### Scenario: DocumentSource define interface comum
- **WHEN** uma classe herda de `DocumentSource` e implementa `categoria` e `obter_documentos`
- **THEN** a classe deve ser aceita por `IndexarDocumentosUseCase` como fonte de documentos

#### Scenario: Ticker opcional
- **WHEN** `obter_documentos()` é chamado sem ticker
- **THEN** a fonte DEVE retornar os documentos globais que não dependem de ticker (ou lista vazia)
