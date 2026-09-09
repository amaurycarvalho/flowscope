## ADDED Requirements

### Requirement: Listagem paginada de fatos relevantes por categoria
O sistema DEVE consultar o endpoint `listedCompaniesProxy/CompanyCall/GetMaterialFacts` com token Base64, suportando paginação automática para recuperar todos os documentos de uma categoria e período.

#### Scenario: Listagem de assembleias da Petrobras em 2026
- **WHEN** `listar_fatos_relevantes(code_cvm="9512", categoria="1", data_inicio="2026-01-01", data_fim="2026-12-31")` é chamado
- **THEN** o sistema DEVE retornar uma lista de documentos da categoria Assembleias
- **AND** cada documento DEVE conter os campos: `company`, `dateReference`, `delivery`, `deliveryDate`, `status`, `category`, `type`, `kind`, `version`, `subject`, `urlSearch`, `urlDownload`

#### Scenario: Paginação automática quando totalPages > 1
- **WHEN** a resposta da API indica `totalPages: 4`
- **THEN** o sistema DEVE iterar sobre as páginas 2, 3 e 4 automaticamente
- **AND** retornar a lista concatenada de todos os resultados

#### Scenario: Sem resultados retorna lista vazia
- **WHEN** uma consulta não encontra documentos no período
- **THEN** o sistema DEVE retornar uma lista vazia sem lançar exceção

### Requirement: Mapeamento de categorias de documentos CVM
O sistema DEVE suportar as 5 categorias documentadas de `GetMaterialFacts`, representadas pelo enum `CategoriaMaterialFact`: Assembleias (1), Aviso aos Acionistas (3), Fatos Relevantes (4), Aviso aos Debenturistas (48), Relatório de Proventos (107).

#### Scenario: Iteração sobre todas as categorias
- **WHEN** o sistema itera sobre `list(CategoriaMaterialFact)`
- **THEN** DEVE produzir 5 valores com os códigos "1", "3", "4", "48", "107"

#### Scenario: Categoria inválida rejeitada
- **WHEN** uma categoria com código "99" é passada para o método de listagem
- **THEN** o sistema DEVE rejeitar com erro de validação antes da requisição HTTP

### Requirement: Cache de listagem com TTL de 1 dia
As listagens de fatos relevantes DEVEM ser cacheadas via `CacheManager` com TTL de 1 dia, usando chave composta por `codeCVM`, `categoria`, `data_inicio` e `data_fim`.

#### Scenario: Segunda consulta no mesmo dia retorna do cache
- **WHEN** `listar_fatos_relevantes(code_cvm="9512", categoria="4", ...)` é chamado duas vezes no mesmo dia
- **THEN** a segunda chamada DEVE retornar do cache sem nova requisição HTTP

### Requirement: Conversão para entidades de domínio
Os resultados brutos da API `GetMaterialFacts` DEVEM ser convertidos para as entidades de domínio `FatoRelevante`, `Assembleia`, ou `AvisoAcionista`/`AvisoDebenturista` conforme a categoria do documento.

#### Scenario: Documento de categoria 4 vira FatoRelevante
- **WHEN** um resultado da API tem `category: "Fatos Relevantes"`
- **THEN** o sistema DEVE instanciar uma entidade `FatoRelevante` com os campos mapeados

#### Scenario: Documento de categoria 1 vira Assembleia
- **WHEN** um resultado da API tem `category: "Assembleia"`
- **THEN** o sistema DEVE instanciar uma entidade `Assembleia` com tipo, espécie e pauta

### Requirement: Construção de token Base64 conforme RFC-004
O sistema DEVE construir o token Base64 para `GetMaterialFacts` a partir de um payload JSON contendo: `linguagem`, `codeCVM`, `year`, `dataInicial`, `dataFinal`, `categoria`, `pageNumber`, `pageSize`.

#### Scenario: Token gerado corresponde ao payload esperado
- **WHEN** o payload `{"linguagem": "pt-br", "codeCVM": "9512", "year": 2026, "dataInicial": "2026-01-01", "dataFinal": "2026-12-31", "categoria": "4", "pageNumber": 1, "pageSize": 20}` é codificado
- **THEN** o token Base64 resultante DEVE ser usado na URL `.../CompanyCall/GetMaterialFacts/{token}`
