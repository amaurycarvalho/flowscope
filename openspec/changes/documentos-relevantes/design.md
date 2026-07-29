## Context

O RFC-003 descreve a extração de documentos não estruturados (PDFs) de tickers listados na B3: Assembleias, Comunicados, Fatos Relevantes e Relatórios. A change `structured-earnings` estabelece a infraestrutura base (`B3FundosClient`, `CacheManager`, `ticker-resolution`). Esta change estende essa infraestrutura com um novo endpoint (`GetReportsRelevants`) e pipeline de PDFs (download → validação → extração de texto → cache).

A change é ticker-agnóstica: qualquer ticker pode ser consultado. Para tickers que não são fundos, a resolução retorna `None` e o pipeline retorna lista vazia.

Esta change fornece a terceira e última `DocumentSource` para o `llm-chat`, complementando `ProventosSource` e `InformeMensalSource`.

## Goals / Non-Goals

**Goals:**
- Novo método `listar_documentos_relevantes(category)` no `B3FundosClient`
- Download de PDFs com validação (`%PDF`) e cache binário
- Extração de texto via PyPDF2 com fallback para PDFs sem texto
- Entidade `DocumentoRelevante` com `to_text()`
- `RelevantesSource` implementando `DocumentSource` (ABC do `llm-chat`)
- Iteração por 4 categorias com tolerância a falhas

**Non-Goals:**
- OCR em PDFs (apenas texto extraível)
- Parsing estruturado do conteúdo dos PDFs (texto bruto, sem semântica)
- Interface CLI própria (o `--index` do `llm-chat` já cobre)

## Decisions

### 1. PyPDF2 para extração de texto

**Alternativa**: pdfplumber (mais robusto, tabelas).
**Decisão**: PyPDF2.

**Racional**: pdfplumber adiciona ~10MB em deps (pdfminer.six). Para o caso de uso (chunk de texto para embedding), a qualidade de extração do PyPDF2 é suficiente. O texto não precisa de formatação preservada — o embedding captura semântica, não layout.

### 2. Cache binário de PDFs

Os PDFs são cacheados como arquivos binários em `~/.cache/flowscope/pdfs/pdf_{id_documento}.pdf`. Sem TTL — documentos históricos não mudam. O `CacheManager` existente é usado para a listagem (TTL 1 dia), mas o download usa cache de arquivo simples (Path.exists()).

### 3. `RelevantesSource` definida em `documentos-relevantes`, não em `llm-chat`

A implementação concreta de `RelevantesSource` vive nesta change, no módulo `infrastructure/document_sources/relevantes_source.py`. O `llm-chat` apenas importa e registra a fonte. Mesmo padrão de `ProventosSource` e `InformeMensalSource`.

### 4. Endpoint `exibirDocumento` para download de PDF

A URL de visualização (`visualizarDocumento`) serve o HTML; o download do PDF usa `exibirDocumento?id={doc_id}`. O `B3FundosClient` já lida com ambos os endpoints (type=40/41 usa `exibirDocumento` para HTML; documentos relevantes usa `exibirDocumento` para PDF).

### 5. Estrutura de diretórios (extensão)

```
src/flowscope/
├── domain/structured/
│   └── entities.py          # + DocumentoRelevante
├── infrastructure/
│   ├── b3/
│   │   └── funds_client.py  # + listar_documentos_relevantes()
│   └── document_sources/
│       └── relevantes_source.py  # RelevantesSource(DocumentSource)
```

## Risks / Trade-offs

- **[Risco] PyPDF2 falha em PDFs com encoding não padrão** → Fallback: texto vazio, log warning. O pipeline continua com outros documentos.
- **[Risco] PDFs grandes consomem memória** → Download em streaming (`response.content`). Para PDFs > 50MB, considerar `iter_content` com chunked reading no futuro.
- **[Trade-off] Sem OCR** → PDFs baseados em imagem (scaneados) não terão texto extraível. Cobre a maioria dos documentos da B3 (gerados digitalmente).
