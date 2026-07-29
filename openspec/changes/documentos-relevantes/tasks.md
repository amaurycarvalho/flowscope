## 1. Pré-requisito

- [ ] 1.1 Verificar que `structured-earnings` está implementada (B3FundosClient, CacheManager, ticker-resolution, value objects)
- [ ] 1.2 Verificar que PyPDF2 está disponível (já no grupo `[llm]` do pyproject.toml)

## 2. Domínio — Entidade

- [ ] 2.1 Implementar `DocumentoRelevante` dataclass em `domain/structured/entities.py` com todos os campos e `to_text()`
- [ ] 2.2 Implementar `_MAPA_CATEGORIAS = {1: "Fato Relevante", 2: "Assembleia", 3: "Comunicado ao Mercado", 7: "Relatorio"}` e função `mapear_categoria(codigo: str) -> str`
- [ ] 2.3 Atualizar `domain/structured/__init__.py`

## 3. Testes do Domínio

- [ ] 3.1 Testar `DocumentoRelevante` criação e `to_text()` com texto e sem texto
- [ ] 3.2 Testar `mapear_categoria` com todos os códigos

## 4. Infraestrutura — B3FundosClient

- [ ] 4.1 Implementar `listar_documentos_relevantes(id_fnet, data_inicio, data_fim, category)` — endpoint `GetReportsRelevants`, token com `category`, paginação, cache TTL 1 dia
- [ ] 4.2 Tratar `id_fnet=None` retornando lista vazia
- [ ] 4.3 Implementar `baixar_pdf(id_documento)` — download via `exibirDocumento?id=`, validação `%PDF`, cache binário em `~/.cache/flowscope/pdfs/`
- [ ] 4.4 Implementar `extrair_texto_pdf(pdf_bytes)` — PyPDF2, concatena páginas, retorna string vazia em falha
- [ ] 4.5 Implementar `listar_todos_documentos_relevantes(id_fnet, data_inicio, data_fim)` — itera 4 categorias, consolida resultados, loga warning em falhas de categoria

## 5. Infraestrutura — RelevantesSource

- [ ] 5.1 Implementar `RelevantesSource(DocumentSource)` em `infrastructure/document_sources/relevantes_source.py`
- [ ] 5.2 `categoria` property retornando `"relevantes"`
- [ ] 5.3 `listar(ticker, data_inicio, data_fim)` — resolve ticker, lista 4 categorias, retorna lista de `DocumentoMeta`
- [ ] 5.4 `obter_texto(meta)` — baixa PDF, extrai texto, retorna `DocumentoRelevante.to_text()`

## 6. Testes da Infraestrutura

- [ ] 6.1 Testar `listar_documentos_relevantes` com mock de HTTP (fixture JSON de resposta)
- [ ] 6.2 Testar `listar_documentos_relevantes` com id_fnet=None
- [ ] 6.3 Testar `baixar_pdf` com PDF válido, conteúdo não-PDF, e cache hit
- [ ] 6.4 Testar `extrair_texto_pdf` com PDF válido e PDF sem texto
- [ ] 6.5 Testar `RelevantesSource` com mock de `B3FundosClient` — `listar()` e `obter_texto()`
- [ ] 6.6 Testar `RelevantesSource` com ticker sem resolução — retorna vazio

## 7. Quality Gate

- [ ] 7.1 Executar `make lint` e corrigir warnings/erros
- [ ] 7.2 Executar `make test` e garantir todos os testes passam
- [ ] 7.3 Verificar que testes de `structured-earnings` continuam passando
