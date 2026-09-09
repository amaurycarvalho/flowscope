## ADDED Requirements

### Requirement: Entidades de domínio regulatório
O sistema DEVE definir entidades de domínio imutáveis (dataclasses) para todos os tipos de dados regulatórios e de mercado: `CensuraPublica`, `CondicaoExcepcional`, `NoticiaB3`, `FatoRelevante`, `Assembleia`, `AvisoAcionista`, `AvisoDebenturista` e `DocumentoMaterialFact`.

#### Scenario: CensuraPublica com campos obrigatórios
- **WHEN** uma `CensuraPublica` é instanciada
- **THEN** ela DEVE conter os campos `titulo: str`, `ticker: str | None`, `data: str`, `conteudo: str`

#### Scenario: CondicaoExcepcional com campos de tabela
- **WHEN** uma `CondicaoExcepcional` é instanciada
- **THEN** ela DEVE conter os campos `companhia: str`, `segmento: str | None`, `condicao: str`, `data_concessao: str | None`, `prazo: str | None`

#### Scenario: NoticiaB3 com metadados de publicação
- **WHEN** uma `NoticiaB3` é instanciada
- **THEN** ela DEVE conter os campos `titulo: str`, `data_publicacao: str`, `url: str | None`, `agencia: str`

#### Scenario: FatoRelevante com referência CVM
- **WHEN** um `FatoRelevante` é instanciado
- **THEN** ele DEVE conter os campos `code_cvm: str`, `empresa: str`, `ticker: str`, `data_referencia: str`, `data_entrega: str | None`, `categoria: str`, `tipo: str | None`, `especie: str | None`, `assunto: str`, `status: str | None`, `url_documento: str | None`

### Requirement: Value objects de domínio regulatório
O sistema DEVE definir value objects imutáveis para validação de dados regulatórios: `CodeCVM` (código CVM da empresa), `CategoriaDocumento` (enum de categorias), `UrlDocumento` (URL de documento CVM).

#### Scenario: CodeCVM valida formato numérico
- **WHEN** um `CodeCVM` é instanciado com valor "9512"
- **THEN** o value object DEVE armazenar o valor e expor `str(code_cvm)` como string

#### Scenario: CategoriaDocumento como enum das categorias conhecidas
- **WHEN** `CategoriaDocumento` é consultado
- **THEN** ele DEVE conter os membros: `ASSEMBLEIAS = "1"`, `AVISO_ACIONISTAS = "3"`, `FATOS_RELEVANTES = "4"`, `AVISO_DEBENTURISTAS = "48"`, `RELATORIO_PROVENTOS = "107"`

### Requirement: to_text() em todas as entidades para VectorStore
Todas as entidades de domínio regulatório DEVEM implementar o protocolo `DocumentoIndexavel` expondo um método `to_text() -> str` que produz uma representação textual semanticamente densa, adequada para chunking e embedding no VectorStore do `llm-chat`.

#### Scenario: FatoRelevante.to_text() inclui ticker, data e assunto
- **WHEN** `fato_relevante.to_text()` é chamado
- **THEN** o texto DEVE incluir o ticker da empresa, a data de referência, a categoria do documento e o assunto

#### Scenario: CensuraPublica.to_text() inclui ticker e conteúdo
- **WHEN** `censura.to_text()` é chamado
- **THEN** o texto DEVE incluir o ticker (se disponível), a data da censura e o conteúdo descritivo

#### Scenario: NoticiaB3.to_text() inclui título e data
- **WHEN** `noticia.to_text()` é chamado
- **THEN** o texto DEVE incluir o título da notícia, a data de publicação e a agência
