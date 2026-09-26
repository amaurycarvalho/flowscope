## Why

O escopo `NOTICIAS` concentra todas as notícias em um único `NOTICIAS.json` em cada store — texto e resumo — e cada operação faz *read-modify-write* integral (o `obter` também relê o arquivo inteiro), resultando em custo ~O(N²) com N grande. Medição de `JsonDocumentTextStore.salvar` (1 KB/item): ~1,0 ms/notícia com N=50 → ~4,3 ms/notícia com N=400 (total ~3,6x ao dobrar N). Os escopos de Documentos são tickers com poucos itens e não sofrem o problema.

## What Changes

- Os caches JSON de **texto e resumo** das notícias passam a ser **particionados por ano e mês**: `document-texts/NOTICIAS-<ANO>-<MES>.json` e `document-summaries/NOTICIAS-<ANO>-<MES>.json`. Cada leitura/escrita toca apenas o shard do item, levando o custo de O(N²) para a soma dos quadrados por shard.
- O shard é **derivado da própria chave estável** (`noticias/<ANO>/<MES>/<hash>.html`): não é preciso o índice nem um novo campo no item. Um **wrapper de notícias** mapeia `(NOTICIAS, chave)` para o shard e delega aos stores JSON existentes.
- `NoticiaArquivo.ticker` continua `NOTICIAS`, e o fluxo compartilhado (`DocumentFlowMixin`, `DocumentSummaryService`, chat) permanece inalterado.
- A leitura em massa de resumos do catálogo passa a **mesclar os shards**.
- **BREAKING (formato do cache de notícias)**: o `NOTICIAS.json` anterior (texto e resumo) é migrado uma única vez para os shards, parseando ano e mês da chave e sem reconverter.
- **Documentos permanece inalterado** (um JSON por ticker) e **sem SQLite**.

## Capabilities

### New Capabilities

<!-- nenhuma -->

### Modified Capabilities

- `documento-texto-cache`: o texto das notícias passa a ser particionado por ano e mês; o layout dos escopos de Documentos permanece igual. (O cache de resumo de notícias não tem spec de persistência própria; sua partição preserva o comportamento e fica no design.)

## Impact

- **Código afetado**: wrapper de shard de notícias em `infrastructure` (deriva o shard da chave e mescla resumos) e os pontos que hoje instanciam os stores concretos para notícias — `infrastructure/b3/noticias_catalogo.py` e `presentation/gui/charts/noticias_panel.py`; migração dos caches antigos. `infrastructure/document_texts.py`, `document_summaries.py` e o wiring de `chat/noticias.py` permanecem como estão.
- **Testes afetados**: `test_noticias_catalogo.py`, `test_noticias_panel.py`; os testes de Documentos permanecem verdes.
- **Interage com**: `refactor-documentos-layers` (nenhum impacto: classes, portas e layout de Documentos não mudam) e `documentos-resumo-lote-persistente`/`noticias-resumo-lote-ordenado` (durabilidade/ordem preservadas; só o escopo de gravação muda, transparente pelo wrapper).
- **Sem dependências novas**; usa apenas a biblioteca padrão.
