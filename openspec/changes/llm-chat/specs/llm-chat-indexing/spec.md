## ADDED Requirements

### Requirement: MaterialFactsSource
O sistema DEVE implementar `MaterialFactsSource(DocumentSource)` usando `RegulacaoRepository` para obter fatos relevantes, assembleias e avisos de um ticker. A fonte DEVE tolerar falha por categoria, logando `logger.warning` e prosseguindo com as demais. Ticker sem `codeCVM` DEVE resultar em lista vazia.

#### Scenario: Ticker com documentos
- **WHEN** `MaterialFactsSource.obter_documentos("ALZR11")` é chamado e o repositório retorna documentos
- **THEN** os documentos DEVEM ser retornados como `DocumentoIndexavel`

#### Scenario: Ticker sem resolução
- **WHEN** o ticker não tem `codeCVM` resolvido
- **THEN** lista vazia DEVE ser retornada sem erro

#### Scenario: Falha em uma categoria
- **WHEN** a listagem de uma categoria falha
- **THEN** as outras categorias DEVEM continuar e o erro DEVE ser logado via `logger.warning`

### Requirement: NoticiasSource
O sistema DEVE implementar `NoticiasSource(DocumentSource)` usando `RegulacaoRepository` para obter as notícias do Plantão B3 no período configurado. A fonte é global de mercado e DEVE ignorar o ticker.

#### Scenario: Notícias do período
- **WHEN** `NoticiasSource.obter_documentos()` é chamado
- **THEN** as notícias do período configurado DEVEM ser retornadas como `DocumentoIndexavel`

#### Scenario: Sem notícias
- **WHEN** não há notícias no período
- **THEN** lista vazia DEVE ser retornada sem erro

### Requirement: InformeMensalSource
O sistema DEVE implementar `InformeMensalSource(DocumentSource)` que lê o cache de arquivos de informe mensal (`~/.cache/flowscope/informe-mensal/<TICKER>/...`), converte o HTML em texto para indexação e retorna vazio quando o ticker não tem documentos em cache. A aquisição/cache do informe NÃO pertence a esta fonte.

#### Scenario: Ticker com informe em cache
- **WHEN** existem arquivos no cache de informe mensal do ticker
- **THEN** a fonte DEVE produzir documentos indexáveis com o texto extraído do HTML

#### Scenario: Ticker sem informe em cache
- **WHEN** o ticker não tem arquivos no cache de informe mensal
- **THEN** lista vazia DEVE ser retornada sem erro

### Requirement: RelevantesSource
O sistema DEVE implementar `RelevantesSource(DocumentSource)` que lê o cache de documentos relevantes (`~/.cache/flowscope/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`), extrai o texto do PDF com `pypdf` e retorna vazio quando o ticker não tem documentos em cache. PDFs sem texto extraível NÃO DEVEM interromper a indexação.

#### Scenario: Ticker com PDFs em cache
- **WHEN** existem PDFs no cache de documentos relevantes do ticker
- **THEN** a fonte DEVE produzir documentos indexáveis com o texto extraído

#### Scenario: PDF sem texto extraível
- **WHEN** um PDF em cache não tem texto extraível
- **THEN** o documento DEVE ser ignorado, sem interromper os demais

#### Scenario: Ticker sem documentos
- **WHEN** o ticker não tem PDFs no cache
- **THEN** lista vazia DEVE ser retornada sem erro

### Requirement: IndexarDocumentosUseCase
O sistema DEVE expor `IndexarDocumentosUseCase` que orquestra as `DocumentSource` disponíveis para um ticker: lista documentos → extrai texto → chunk → embed → grava no VectorStore com deduplicação. Erro em uma fonte NÃO DEVE interromper as outras, e o progresso DEVE ser reportado por callback.

#### Scenario: Ticker sem dados em uma fonte
- **WHEN** uma fonte retorna vazio para o ticker
- **THEN** o use case DEVE continuar com as outras fontes sem erro

#### Scenario: Falha em uma fonte
- **WHEN** uma fonte lança exceção
- **THEN** o use case DEVE registrar o erro e continuar as demais fontes

### Requirement: ConsultarDocumentosUseCase
O sistema DEVE expor `ConsultarDocumentosUseCase` que recebe uma pergunta, o VectorStore, o `EmbeddingPort`, o `ChatPort` e um ticker opcional, executando embed → busca semântica → prompt RAG → resposta com as fontes.

#### Scenario: Sem documentos indexados
- **WHEN** o VectorStore está vazio para o ticker
- **THEN** retornar "Nenhum documento indexado. Use 'Atualizar Documentos' primeiro."

#### Scenario: Resposta com fontes
- **WHEN** há chunks relevantes para a pergunta
- **THEN** a resposta DEVE ser acompanhada dos metadados das fontes recuperadas
