## Why

A fatia de Notícias concentra regras de domínio e de aplicação na apresentação e
em módulos de infraestrutura: a classificação por tipo e a whitelist de eventos
vivem em `infrastructure/b3/noticias_tipos.py`; as entidades de catálogo
(`NoticiaArquivo`, `SecaoNoticias`, `CatalogoNoticias`) em
`infrastructure/b3/noticias_catalogo.py`; e `noticias_panel.py` decide a
ordenação do lote, a derivação de data, a regra de apontador pendente e a
extração do corpo, enquanto `presentation/gui/chat/noticias.py` monta o índice
compacto do chat. Os três módulos de apresentação importam `infrastructure`
diretamente. Esta fatia move classificação e entidades para `domain`/`application`,
deixa o painel apenas desenhar e remove as três entradas da allowlist.

## What Changes

- Classificação de notícias (`TERMOS_EXCEPCIONAIS`, `TIPOS_NOTICIA`,
  `TIPO_OUTROS`, `normalizar_texto`, `noticia_excepcional`, `classificar_tipo`)
  sai de `infrastructure/b3/noticias_tipos.py` para `domain`.
- Entidades de catálogo (`NoticiaArquivo`, `SecaoNoticias`, `CatalogoNoticias`,
  `TITULO_NOTICIAS`) e a ordenação do lote (`pendentes_ordenados` e chave
  determinista) saem de `infrastructure`/`presentation` para
  `domain`/`application`.
- `infrastructure/b3/noticias_catalogo.py` permanece como adaptador de leitura do
  índice/cache, implementando a porta de catálogo e reaproveitando o read-model
  `montar_catalogo` de `application/documentos`.
- A montagem do índice compacto do chat e a intercalação por seção
  (`FonteNoticias._montar`, `_intercalar`, `_agrupar_por_secao`, `_ordem_secoes`)
  passam para `application`; a apresentação apenas injeta store/texto e exibe.
- `NoticiasPanel` recebe caso de uso e portas por injeção (mesmo padrão do
  `DocumentTreePanel`), sem importar `infrastructure`; `NoticiasTreeView` importa
  entidades de `domain`.
- Remoção das três entradas de notícias de `tests/architecture/allowlist.txt`.
- Migração dos testes puros de notícias (classificação, ordenação do lote, índice
  do chat, extração) para `tests/test_domain`/`tests/test_application`; o painel
  mantém apenas wiring, estado e thread.

## Capabilities

### New Capabilities

### Modified Capabilities

Opta por não alterar specs (`skip_specs: true`): refatoração que preserva o
comportamento observável, implementando o contrato `layer-boundaries` do change
`clean-architecture-layering`.

## Impact

- **Depende de**: `add-layer-architecture-guardrails` (allowlist e teste de
  fronteira) e `refactor-documentos-layers` (read-model `montar_catalogo`, portas
  de store e padrão de injeção do `DocumentTreePanel`).
- **Código movido**: `infrastructure/b3/noticias_tipos.py`,
  `infrastructure/b3/noticias_catalogo.py`;
  `presentation/gui/charts/noticias_panel.py`,
  `presentation/gui/charts/noticias_tree_view.py`;
  `presentation/gui/chat/noticias.py`.
- **Novos tipos**: `domain/noticias/*`; portas, read-models e casos de uso em
  `application/noticias/*`.
- **Testes migrados**: testes puros de `test_noticias_panel.py` (42, dos quais 21
  exigem `DISPLAY`) e de `test_noticias_chat_context.py` para
  `tests/test_domain`/`tests/test_application`; o painel fica com o subconjunto
  de wiring/estado/thread.
- **Sem alteração de comportamento**: árvore, pré-visualização, resumos,
  ordenação do lote e índice do chat permanecem idênticos.
