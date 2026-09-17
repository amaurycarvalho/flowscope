## MODIFIED Requirements

### Requirement: Construção de token Base64 conforme RFC-004
O sistema DEVE construir o token Base64 para `GetMaterialFacts` a partir de um payload JSON contendo exatamente os campos aceitos pela API: `language`, `codeCVM`, `year`, `dateInitial`, `dateFinal`, `category`, `pageNumber` e `pageSize`. O sistema NÃO DEVE usar os nomes `linguagem`, `dataInicial`, `dataFinal` ou `categoria`, que a API ignora e que resultam em listagem vazia.

#### Scenario: Token gerado corresponde ao payload esperado
- **WHEN** o payload `{"language": "pt-br", "codeCVM": "9512", "year": 2026, "dateInitial": "2026-01-01", "dateFinal": "2026-12-31", "category": "4", "pageNumber": 1, "pageSize": 20}` é codificado
- **THEN** o token Base64 resultante DEVE ser usado na URL `.../CompanyCall/GetMaterialFacts/{token}`

#### Scenario: Listagem retorna documentos com os campos aceitos
- **WHEN** `listar_fatos_relevantes(code_cvm="9512", categoria="4", data_inicio="2024-01-01", data_fim="2024-12-31")` é chamado com o payload corrigido
- **THEN** a API DEVE retornar os fatos relevantes do período, sem lista vazia
