## ADDED Requirements

### Requirement: Listagem de documentos relevantes por categoria
O sistema DEVE adicionar método `listar_documentos_relevantes(id_fnet, data_inicio, data_fim, category)` ao `B3FundosClient`, usando endpoint `GetReportsRelevants` com token contendo `category` (1, 2, 3, 7). O método DEVE iterar paginação e cachear resultado com TTL de 1 dia.

#### Scenario: Listagem de uma categoria específica
- **WHEN** `listar_documentos_relevantes("20294", "2026-01-01", "2026-07-29", category=2)` é chamado
- **THEN** apenas documentos da categoria Assembleias DEVEM ser retornados

#### Scenario: Paginação em múltiplas páginas
- **WHEN** a resposta contém `totalPages=3`
- **THEN** o sistema DEVE realizar requisições para as 3 páginas e consolidar resultados

#### Scenario: id_fnet é None
- **WHEN** o ticker não foi resolvido (id_fnet=None)
- **THEN** o método DEVE retornar lista vazia sem erro

### Requirement: Download de PDF com validação
O sistema DEVE baixar PDFs da URL `fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id={doc_id}`, validar que o conteúdo começa com `%PDF`, e cachear em `~/.cache/flowscope/pdfs/pdf_{doc_id}.pdf`.

#### Scenario: Download bem-sucedido de PDF válido
- **WHEN** um PDF é baixado e os primeiros 4 bytes são `%PDF`
- **THEN** o conteúdo binário DEVE ser retornado e cacheado em disco

#### Scenario: Conteúdo não é PDF
- **WHEN** o conteúdo baixado não começa com `%PDF`
- **THEN** uma exceção descritiva DEVE ser lançada

#### Scenario: PDF já em cache
- **WHEN** o arquivo `pdf_{doc_id}.pdf` já existe no cache
- **THEN** o sistema DEVE retornar o conteúdo do cache sem realizar download

### Requirement: Extração de texto via PyPDF2
O sistema DEVE extrair texto de PDFs usando PyPDF2, concatenando o texto de todas as páginas. Erros de extração DEVEM resultar em string vazia, sem interromper o pipeline.

#### Scenario: Extração bem-sucedida
- **WHEN** PyPDF2 extrai texto de 3 páginas
- **THEN** o texto DEVE ser a concatenação do texto das 3 páginas

#### Scenario: PDF sem texto extraível
- **WHEN** PyPDF2 não consegue extrair texto de nenhuma página
- **THEN** o sistema DEVE retornar string vazia sem lançar exceção

### Requirement: Iteração por 4 categorias
O sistema DEVE iterar sobre as 4 categorias (1, 2, 3, 7) ao listar documentos relevantes para um ticker, consolidando todos os resultados em uma única lista.

#### Scenario: Todas as categorias listadas
- **WHEN** o sistema lista documentos para as 4 categorias
- **THEN** documentos de todas as categorias DEVEM ser retornados consolidados

#### Scenario: Uma categoria falha
- **WHEN** a listagem da categoria 2 (Assembleias) falha com erro HTTP
- **THEN** as outras categorias DEVEM continuar, e o erro DEVE ser logado via `logger.warning`

### Requirement: `RelevantesSource` como DocumentSource
O sistema DEVE implementar `RelevantesSource` herdando de `DocumentSource` (ABC definida em `llm-chat`), usando `B3FundosClient` para listagem e download, PyPDF2 para extração de texto, e retornando `DocumentoRelevante.to_text()` para indexação.

#### Scenario: RelevantesSource implementa DocumentSource
- **WHEN** `RelevantesSource` é instanciada com `B3FundosClient`
- **THEN** `listar()` DEVE retornar metadados de documentos e `obter_texto()` DEVE retornar texto extraído do PDF

#### Scenario: Ticker sem documentos
- **WHEN** `listar()` é chamado para um ticker sem documentos relevantes
- **THEN** lista vazia DEVE ser retornada sem erro
