## Context

Ver `proposal.md` — Why. Os stores `JsonDocumentTextStore` e `JsonDocumentSummaryStore` persistem um JSON por escopo com *read-modify-write* integral (`document_texts.py:54-84`; `document_summaries.py:68-105`) e derivam o **nome do arquivo do escopo** (`_path_for`). O escopo `NOTICIAS` agrega todas as notícias; os escopos de Documentos são tickers com poucos itens.

Fato decisivo: a chave estável de notícia é `noticias/<ANO>/<MES>/<hash>.html`, então **ano e mês são deriváveis da própria chave** — sem o índice e sem novo campo no item. `NoticiaArquivo.ticker` já é um rótulo de escopo (a constante `NOTICIAS`) e pode permanecer assim.

## Goals / Non-Goals

**Goals:**

- Limitar o N por arquivo, particionando os caches de texto e resumo das notícias por ano e mês.
- Derivar o shard da chave, sem depender do índice nem alterar `NoticiaArquivo.ticker` ou o fluxo compartilhado.
- Migrar o `NOTICIAS.json` anterior sem reconverter.
- Não alterar o layout nem o comportamento de Documentos.

**Non-Goals:**

- Usar SQLite.
- Particionar por grupo (não está na chave e exigiria plumbing).
- Alterar o layout dos escopos de Documentos.
- Alterar a ordem do lote, a saída exibida ou a aquisição.

## Decisions

### D1 — Shard = `NOTICIAS-<ANO>-<MES>`, derivado da chave

O escopo de cache de uma notícia passa a ser `NOTICIAS-<ANO>-<MES>` (ex.: `NOTICIAS-2026-09`), obtido parseando `noticias/<ANO>/<MES>/...` da chave estável. Resulta em `document-texts/NOTICIAS-2026-09.json` e `document-summaries/NOTICIAS-2026-09.json`. Chaves fora do padrão caem em um shard de fallback (`NOTICIAS-SEM-DATA`).

Alternativa considerada: particionar por grupo e ano — rejeitada porque o grupo não está na chave e exigiria índice/plumbing, sem ganho sobre a partição mensal.

### D2 — Wrapper de notícias, sem tocar no fluxo compartilhado

Um wrapper para o cache de notícias mapeia `(NOTICIAS, chave)` → shard e delega aos stores JSON existentes. Assim `DocumentFlowMixin`, `DocumentSummaryService`, `chat/noticias.py` e `NoticiaArquivo.ticker` permanecem inalterados; só a construção dos stores em `NoticiasCatalog`/`NoticiasPanel` passa a usar o wrapper. Documentos segue com os stores concretos e `<TICKER>.json`.

### D3 — Leitura em massa de resumos

O enriquecimento do catálogo chama `resumos(NOTICIAS)`; o wrapper varre `document-summaries/NOTICIAS-*.json`, mescla os mapas e devolve o resultado. São poucos arquivos (meses com itens) e a leitura é única por carga.

### D4 — Migração do cache de notícias anterior

Se existir `NOTICIAS.json` (texto e/ou resumo) e os shards ainda não existirem, ler o arquivo antigo uma vez e regravar por shard, parseando ano e mês de cada chave. Idempotente, tolerante a ausência/corrupção e restrita a notícias — os `<TICKER>.json` de Documentos não são tocados. O legado é removido após a migração concluir.

Alternativa considerada: invalidar e reconverter — rejeitada por repagar extração e downloads de documentos vinculados.

### D5 — Sem impacto em Documentos nem no refactor

As classes de store e as portas (`DocumentTextStore`, e a futura `DocumentSummaryStore`) não mudam. `refactor-documentos-layers` continua movendo os mesmos adaptadores; o wrapper é escopo de notícias.

## Risks / Trade-offs

- [Mais arquivos] → 12 meses × anos (poucos), muito menos que arquivo por documento.
- [Shard mensal mistura grupos] → o volume de um mês entre as quatro categorias é pequeno; se um mês dominar, particionar por dia é a evolução natural.
- [Chave malformada] → fallback `NOTICIAS-SEM-DATA`, sem erro.
- [Migração] → única e idempotente; se incompleta, degrada para reconversão, sem erro.

## Migration Plan

1. Deploy com o wrapper de shard.
2. Na primeira operação do escopo de notícias, migrar `NOTICIAS.json` (texto e resumo) para os shards; remover o legado após sucesso.
3. Rollback: reverter o código; o cache de Documentos nunca mudou e o de notícias é derivável.

## Open Questions

- Forma do wrapper (subclasse dos stores concretos vs. composição com um resolvedor `(ticker, chave) → shard`): decidir na implementação, sem impacto no contrato.
