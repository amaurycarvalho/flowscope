## Why

Os documentos não estruturados da B3 (Assembleias, Comunicados, Fatos Relevantes e Relatórios) são PDFs relevantes para análise de um ticker, mas hoje não há aquisição nem cache local deles. Esta change adiciona a listagem via `GetReportsRelevants`, o download com validação e o cache dos PDFs em uma árvore por ticker/ano/mês/categoria, tornando-os acessíveis à sub-aba de documentos. Fica separada das demais fontes por isolar o domínio de PDFs (download binário, validação `%PDF` e cache de arquivos).

## What Changes

- Novo método `listar_documentos_relevantes(id_fnet, data_inicio, data_fim, category)` no `B3FundosClient`, usando `GetReportsRelevants` com iteração pelas 4 categorias (1=Fatos Relevantes, 2=Assembleias, 3=Comunicados, 7=Relatórios), paginação e cache de listagem (TTL 1 dia).
- Download dos PDFs via `exibirDocumento?id=` com validação de assinatura `%PDF`.
- Cache binário em `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`, sem expiração.
- Nova entidade `DocumentoRelevante` com metadados (ticker, id, categoria, descrição, datas, url) — **sem** `texto_extraido` e **sem** `to_text()`.
- Mapeamento de categorias da API para nomes e slugs de pasta.
- Ticker-agnóstico: retorna lista vazia quando a resolução falha ou o ticker não tem documentos.
- Remover do escopo a preparação para o `llm-chat` (`DocumentoRelevante.to_text()`, `RelevantesSource`/`DocumentSource`, extração de texto para embedding), transferida para a change `llm-chat`.

## Capabilities

### New Capabilities

- `documentos-relevantes-domain`: entidade `DocumentoRelevante` (metadados) e mapeamento de categorias (nome e slug de pasta).
- `documentos-relevantes-extraction`: listagem por categoria via `GetReportsRelevants`, download com validação `%PDF` e cache em árvore por ticker/ano/mês/categoria.

### Modified Capabilities

_Nenhuma. Esta change adiciona ao `B3FundosClient` e ao domínio de documentos sem modificar requisitos de specs existentes._

## Impact

- **Dependência**: reutiliza `B3FundosClient` e `CacheManager` já implementados.
- **Código**: extensão de `infrastructure/b3/funds_client/` e `domain/structured/`; sem módulos de aplicação próprios.
- **Cache**: nova raiz `~/.cache/flowscope/documentos-relevantes/`; listagem com cache TTL 1 dia.
- **APIs**: `GetReportsRelevants` em `sistemaswebb3-listados.b3.com.br`; PDFs em `fnet.bmfbovespa.com.br`.
- **Transferência**: extração de texto e fonte de indexação passam para `llm-chat` e para a change `visualizacao-documentos` (preview).
