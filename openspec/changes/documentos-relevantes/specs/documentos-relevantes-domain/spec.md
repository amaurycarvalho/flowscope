## ADDED Requirements

### Requirement: Entidade DocumentoRelevante
O sistema DEVE possuir uma entidade `DocumentoRelevante` dataclass representando um documento não estruturado em PDF, contendo `ticker` (str), `id_fnet` (str | None), `id_documento` (str), `categoria` (str: "Fato Relevante", "Assembleia", "Comunicado", "Relatorio"), `descricao` (str), `data_referencia` (date | None), `data_entrega` (str), `url` (str), `texto_extraido` (str), `tamanho_bytes` (int | None) e `data_extracao` (datetime). A entidade DEVE expor `to_text()` para alimentar o VectorStore.

#### Scenario: DocumentoRelevante com texto extraído
- **WHEN** um `DocumentoRelevante` é criado com texto extraído de um PDF de Assembleia
- **THEN** `to_text()` DEVE retornar texto contendo ticker, categoria, descrição, data e o texto extraído completo

#### Scenario: DocumentoRelevante sem texto (PDF ilegível)
- **WHEN** `texto_extraido` é string vazia (PDF sem texto extraível)
- **THEN** `to_text()` DEVE retornar texto com metadados, indicando "Sem conteúdo textual extraível"

### Requirement: Mapeamento de categorias
O sistema DEVE mapear os valores numéricos da API para nomes legíveis: `1` → `"Fato Relevante"`, `2` → `"Assembleia"`, `3` → `"Comunicado ao Mercado"`, `7` → `"Relatorio"`.

#### Scenario: Categoria 1
- **WHEN** a API retorna `category: "1"`
- **THEN** o sistema DEVE armazenar `"Fato Relevante"` no campo `categoria`
