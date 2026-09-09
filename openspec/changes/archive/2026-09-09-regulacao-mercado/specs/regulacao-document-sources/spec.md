## ADDED Requirements

### Requirement: MaterialFactsSource implementa DocumentSource ABC
O sistema DEVE fornecer `MaterialFactsSource` como uma implementação concreta do ABC `DocumentSource` definido em `llm-chat`, capaz de obter documentos regulatórios de qualquer ticker via `GetMaterialFacts`.

#### Scenario: MaterialFactsSource obtém documentos para PETR4
- **WHEN** `MaterialFactsSource.obter_documentos(ticker="PETR4")` é chamado
- **THEN** a fonte DEVE resolver o codeCVM de PETR4
- **AND** DEVE iterar sobre as 5 categorias de `CategoriaMaterialFact`
- **AND** DEVE retornar uma lista de `DocumentoIndexavel` (entidades com `to_text()`)

#### Scenario: MaterialFactsSource retorna vazio para ticker sem codeCVM
- **WHEN** `MaterialFactsSource.obter_documentos(ticker="TICKER_SEM_CVM")` é chamado
- **THEN** a fonte DEVE retornar lista vazia sem lançar exceção

#### Scenario: MaterialFactsSource tolera falha em uma categoria
- **WHEN** a API falha para a categoria "Aviso aos Debenturistas" mas sucede para as demais
- **THEN** a fonte DEVE continuar processando as outras categorias
- **AND** DEVE logar warning sobre a falha, sem interromper o fluxo

### Requirement: NoticiasSource implementa DocumentSource ABC
O sistema DEVE fornecer `NoticiasSource` como uma implementação concreta do ABC `DocumentSource`, capaz de obter notícias do Plantão B3 independentemente de ticker.

#### Scenario: NoticiasSource obtém notícias sem exigir ticker
- **WHEN** `NoticiasSource.obter_documentos()` é chamado (ticker é ignorado)
- **THEN** a fonte DEVE consultar o Plantão B3 para o período configurado
- **AND** DEVE retornar uma lista de `DocumentoIndexavel` (entidades `NoticiaB3`)

#### Scenario: NoticiasSource com período padrão de 30 dias
- **WHEN** `NoticiasSource` é instanciada sem parâmetros de data
- **THEN** o período de consulta DEVE ser os últimos 30 dias a partir da data atual

### Requirement: Integração com IndexarDocumentosUseCase
As fontes `MaterialFactsSource` e `NoticiasSource` DEVEM ser registráveis no `IndexarDocumentosUseCase` do `llm-chat`, sem exigir modificações no use case existente (design plugável via ABC).

#### Scenario: Registro de fontes no use case
- **WHEN** `IndexarDocumentosUseCase` recebe uma lista contendo `MaterialFactsSource` e `NoticiasSource`
- **THEN** o use case DEVE iterar sobre ambas as fontes e indexar seus documentos no VectorStore

### Requirement: Localização das implementações de DocumentSource
As implementações de `DocumentSource` para dados regulatórios DEVEM residir em `infrastructure/document_sources/` (mesmo diretório das fontes de `llm-chat`): `material_facts_source.py` e `noticias_source.py`.

#### Scenario: Importação segue padrão do projeto
- **WHEN** `from flowscope.infrastructure.document_sources.material_facts_source import MaterialFactsSource` é executado
- **THEN** a classe DEVE estar disponível e ser instanciável
