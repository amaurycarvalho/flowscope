# documentos-relevantes-extraction Specification

## Purpose

TBD - Update Purpose after archive.

## Requirements

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
O sistema DEVE baixar PDFs da URL `fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id={doc_id}`, validar que o conteúdo começa com `%PDF` e cachear em `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`, sem expiração. Quando o arquivo já existir, o sistema DEVE reutilizá-lo sem novo download. Conteúdo que não começa com `%PDF` DEVE ser rejeitado para aquele documento, sem interromper os demais.

#### Scenario: Download bem-sucedido de PDF válido
- **WHEN** um PDF é baixado e os primeiros 4 bytes são `%PDF`
- **THEN** o conteúdo binário DEVE ser gravado no caminho da árvore por ticker/ano/mês/categoria

#### Scenario: Conteúdo não é PDF
- **WHEN** o conteúdo baixado não começa com `%PDF`
- **THEN** o documento DEVE ser rejeitado, sem interromper os demais

#### Scenario: PDF já em cache
- **WHEN** o arquivo do documento já existe no cache
- **THEN** o sistema DEVE retornar o conteúdo do cache sem realizar download

### Requirement: Iteração por 4 categorias
O sistema DEVE iterar sobre as 4 categorias (1, 2, 3, 7) ao listar documentos relevantes para um ticker, consolidando todos os resultados em uma única lista.

#### Scenario: Todas as categorias listadas
- **WHEN** o sistema lista documentos para as 4 categorias
- **THEN** documentos de todas as categorias DEVEM ser retornados consolidados

#### Scenario: Uma categoria falha
- **WHEN** a listagem da categoria 2 (Assembleias) falha com erro HTTP
- **THEN** as outras categorias DEVEM continuar, e o erro DEVE ser logado via `logger.warning`

### Requirement: Leitura da árvore pelo catálogo de documentos
O sistema DEVE expor a leitura dos documentos relevantes em cache de um ticker, retornando os documentos existentes com seus caminhos e categorias, de forma ordenada do mais recente para o mais antigo. Um ticker sem documentos em cache DEVE resultar em lista vazia, sem erro.

#### Scenario: Documentos existentes
- **WHEN** um ticker possui arquivos em `<cache>/documentos-relevantes/<TICKER>/`
- **THEN** o sistema DEVE retornar os documentos encontrados com caminhos e categorias, do mais recente para o mais antigo

#### Scenario: Ticker sem documentos
- **WHEN** um ticker não possui arquivos no cache de documentos relevantes
- **THEN** o sistema DEVE retornar lista vazia sem erro
