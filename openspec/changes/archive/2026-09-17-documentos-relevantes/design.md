## Context

Ver `proposal.md - Why`. O RFC-003 descreve a aquisição de documentos não estruturados (PDFs) de tickers da B3. A infraestrutura base (`B3FundosClient`, `CacheManager`, resolução de ticker) já existe. Esta change adiciona o endpoint `GetReportsRelevants` e o pipeline de PDFs (listar → baixar → validar → cachear em árvore). O texto extraído e a indexação não fazem parte desta change.

A change é ticker-agnóstica: qualquer ticker pode ser consultado; para tickers que não são fundos, a resolução retorna `None` e o pipeline retorna lista vazia.

## Goals / Non-Goals

**Goals:**
- Método `listar_documentos_relevantes(category)` no `B3FundosClient`.
- Download de PDFs com validação (`%PDF`) e cache em `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`.
- Entidade `DocumentoRelevante` com metadados e mapeamento de categorias (nome + slug).
- Iteração pelas 4 categorias com tolerância a falhas.

**Non-Goals:**
- Extração de texto do PDF (preview e indexação) — pertence a `visualizacao-documentos` e `llm-chat`.
- `to_text()`/`DocumentSource`/`RelevantesSource` — transferidos para `llm-chat`.
- OCR em PDFs (apenas PDFs válidos são cacheados).
- CLI própria (o catálogo/sub-aba de documentos cobre).

## Decisions

### 1. Raiz de cache própria e árvore com categoria

**Decisão**: `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`, sem TTL. Reutiliza `CacheManager.get_cache_dir()` como raiz.

**Alternativas**: (a) cache plano `pdfs/pdf_{id}.pdf` (perde ticker/ano/mês/categoria e não é varredura por fonte); (b) árvore `bdr/` (semântica errada). A raiz própria com categoria atende à árvore da sub-aba e mantém o cache BDR intacto.

### 2. Sem texto extraído na entidade

**Decisão**: `DocumentoRelevante` guarda apenas metadados. A extração de texto do PDF para preview fica em `visualizacao-documentos`; para indexação, em `llm-chat`.

**Racional**: separa aquisição/cache (esta change) de consumo (preview/indexação), evitando dependência de biblioteca de PDF no caminho de aquisição.

### 3. Endpoint `exibirDocumento` para o PDF

A URL de visualização (`visualizarDocumento`) serve o viewer; o download usa `exibirDocumento?id={doc_id}`. Mesmo endpoint já usado para os documentos estruturados (type=40/41), com validação `%PDF`.

## Risks / Trade-offs

- **[Risco] PDFs grandes consomem memória** → Download com `response.content`; para PDFs > 50MB, considerar leitura em chunks no futuro.
- **[Trade-off] Sem OCR/extração** → PDFs baseados em imagem ficam apenas como arquivo; preview textual e indexação são responsabilidade de quem consome.
- **[Risco] `GetReportsRelevants` mudar de contrato** → Testes de contrato com fixture JSON e tolerância a falha por categoria.

## Migration Plan

1. Adicionar `listar_documentos_relevantes` ao cliente B3.
2. Implementar download + validação + cache em árvore.
3. Implementar entidade e mapeamento de categorias.
4. Consumir a árvore pela sub-aba de documentos (change `visualizacao-documentos`) e pelo `llm-chat`.
5. Rollback: mudanças aditivas; remover o módulo restaura o comportamento anterior.
