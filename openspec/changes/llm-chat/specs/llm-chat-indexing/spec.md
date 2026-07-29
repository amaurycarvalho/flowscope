## ADDED Requirements

### Requirement: ProventosSource
O sistema DEVE implementar `ProventosSource(DocumentSource)` usando `ProventosRepository` (de `structured-earnings`). Se a resolução do ticker retornar `None`, a fonte DEVE retornar lista vazia.

#### Scenario: Ticker de fundo — dados disponíveis
- **WHEN** `ProventosSource.listar("ALZR11", "2026-01-01", "2026-07-29")`
- **THEN** documentos de proventos DEVEM ser retornados

#### Scenario: Ticker de ação — sem dados
- **WHEN** `ProventosSource.listar("PETR4", "2026-01-01", "2026-07-29")`
- **THEN** lista vazia DEVE ser retornada sem erro

### Requirement: InformeMensalSource
O sistema DEVE implementar `InformeMensalSource(DocumentSource)` usando `InformeMensalRepository` (de `informe-mensal`). Ticker sem resolução retorna vazio.

### Requirement: RelevantesSource
O sistema DEVE implementar `RelevantesSource(DocumentSource)` usando `B3FundosClient.listar_documentos_relevantes(category)`, baixando PDFs e extraindo texto com PyPDF2.

#### Scenario: PDF corrompido
- **WHEN** conteúdo baixado não começa com `%PDF`
- **THEN** exceção com "Arquivo não é um PDF válido"

### Requirement: B3FundosClient.listar_documentos_relevantes
Novo método no `B3FundosClient` usando endpoint `GetReportsRelevants` com parâmetro `category` (1,2,3,7), paginação e cache.

### Requirement: IndexarDocumentosUseCase
Orquestra 3 `DocumentSource` para um ticker: lista → texto → chunk → embed → VectorStore com deduplicação. Erro em uma fonte não interrompe as outras.

#### Scenario: Ticker sem dados em fonte
- **WHEN** `ProventosSource` retorna vazio para `PETR4`
- **THEN** o use case DEVE continuar com as outras fontes sem erro

### Requirement: ConsultarDocumentosUseCase
Recebe pergunta, VectorStore, EmbeddingPort, ChatPort e ticker opcional. Embed → search → prompt RAG → resposta com fontes.

#### Scenario: Sem documentos indexados
- **WHEN** VectorStore está vazio para o ticker
- **THEN** retornar "Nenhum documento indexado. Use 'Atualizar Documentos' primeiro."
