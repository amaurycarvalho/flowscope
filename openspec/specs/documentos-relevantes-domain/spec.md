# documentos-relevantes-domain Specification

## Purpose

TBD - Update Purpose after archive.

## Requirements

### Requirement: Entidade DocumentoRelevante
O sistema DEVE possuir uma entidade `DocumentoRelevante` dataclass representando um documento não estruturado em PDF, contendo `ticker` (str), `id_fnet` (str | None), `id_documento` (str), `categoria` (str: "Fato Relevante", "Assembleia", "Comunicado ao Mercado", "Relatorio"), `descricao` (str), `data_referencia` (date | None), `data_entrega` (str), `url` (str), `tamanho_bytes` (int | None) e `data_extracao` (datetime). A entidade DEVE conter apenas metadados de aquisição, sem texto extraído e sem representação textual para indexação.

#### Scenario: DocumentoRelevante com metadados
- **WHEN** um `DocumentoRelevante` é criado com os metadados de um PDF de Assembleia
- **THEN** todos os campos de metadados DEVEM ser acessíveis

### Requirement: Mapeamento de categorias
O sistema DEVE mapear os valores numéricos da API para nomes legíveis e para o slug usado na pasta de cache: `1` → `"Fato Relevante"` / `"fato-relevante"`, `2` → `"Assembleia"` / `"assembleia"`, `3` → `"Comunicado ao Mercado"` / `"comunicado"`, `7` → `"Relatorio"` / `"relatorio"`.

#### Scenario: Categoria 1
- **WHEN** a API retorna `category: "1"`
- **THEN** o sistema DEVE armazenar `"Fato Relevante"` no campo `categoria` e usar `"fato-relevante"` na pasta de cache

#### Scenario: Categoria 7
- **WHEN** a API retorna `category: "7"`
- **THEN** o sistema DEVE armazenar `"Relatorio"` no campo `categoria` e usar `"relatorio"` na pasta de cache
