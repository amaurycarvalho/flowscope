## Context

Ver `proposal.md` — Why, e o contrato em
`openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md`.
Estado atual relevante:

- `infrastructure/b3/noticias_tipos.py` define a whitelist (`TERMOS_EXCEPCIONAIS`),
  a tabela de tipos (`TIPOS_NOTICIA`), o fallback (`TIPO_OUTROS`),
  `normalizar_texto`, `noticia_excepcional` e `classificar_tipo` — tudo puro.
- `infrastructure/b3/noticias_catalogo.py` define `NoticiaArquivo`,
  `SecaoNoticias`, `CatalogoNoticias`, `TITULO_NOTICIAS` e `NoticiasCatalog`, que
  lê o índice (`NoticiasIndexStore`) e os shards de resumo/texto
  (`NoticiasSummaryStore`, `NoticiasTextStore`), sem tocar a B3.
- `infrastructure/b3/noticias_aquisicao.py` mantém `SECOES_ORDEM`,
  `SECAO_GERAL`, `ESCOPO_NOTICIAS`, `NoticiasCache` e `data_noticia` (parsing).
- `presentation/gui/charts/noticias_panel.py` instancia `NoticiasCatalog` e os
  stores, decide a ordem do lote (`pendentes_ordenados`, `_chave_ordenacao`,
  `_data_ordinal`), a regra de apontador pendente (`_apontador_pendente`,
  `texto_utilizavel`) e a extração do corpo (`_texto_do_arquivo`).
- `presentation/gui/chat/noticias.py` monta o índice compacto (`_montar`),
  intercala por seção (`_intercalar`, `_agrupar_por_secao`, `_ordem_secoes`) e
  deriva a chave curta (`_chave_curta`) — lógica pura —, além de ler o texto via
  `NoticiasTextStore` e `texto_preview`.
- Guardrail: a allowlist tem 3 entradas de notícias (`noticias_panel.py`,
  `noticias_tree_view.py`, `chat/noticias.py`).
- Estado após `refactor-documentos-layers`: entidades de catálogo e read-model em
  `domain/documents`/`application/documentos`; `DocumentTreePanel` recebe caso de
  uso e portas por injeção; a allowlist foi encolhida em 9 entradas.
- Estado após `noticias-cache-sharding`: o texto de notícias é particionado por
  ano e mês nos shards; a assinatura de leitura/gravação não muda nesta fatia.

## Goals / Non-Goals

**Goals:**

- Colocar a classificação e as entidades de notícia em `domain/noticias`.
- Colocar porta, read-model, ordenação do lote e índice do chat em `application`.
- Fazer `NoticiasPanel` depender de portas/casos de uso, recebidos por injeção do
  composition root, sem importar `infrastructure`.
- Remover as 3 entradas de notícias da allowlist.
- Migrar os testes puros para `test_domain`/`test_application`.

**Non-Goals:**

- Não mover parsing/I/O para `domain`: `noticias_index`, `noticias_shards`,
  `noticias_carga`, `noticias_vinculo` e `data_noticia` permanecem em
  `infrastructure`.
- Não mexer na fatia de Documentos nem no armazenamento particionado das
  notícias (`noticias-cache-sharding`); apenas reaproveitar o read-model
  `montar_catalogo`.
- Não redesenhar a árvore/preview nem trocar widgets.
- Não alterar a montagem de contexto do chat como um todo; esta fatia trata a
  fonte de notícias (`FonteNoticias`), e `refactor-chat-context-layers` cuida do
  restante do contexto.

## Decisions

### D1 — Classificação e entidades em `domain/noticias`

`TERMOS_EXCEPCIONAIS`, `TIPOS_NOTICIA`, `TIPO_OUTROS`, `normalizar_texto`,
`noticia_excepcional` e `classificar_tipo` vão para
`domain/noticias/classificacao.py`. As entidades `NoticiaArquivo`,
`SecaoNoticias`, `CatalogoNoticias` e a constante `TITULO_NOTICIAS` vão para
`domain/noticias/entities.py`. Alternativa: manter a classificação em
`application`. Rejeitada por ser regra de domínio pura, sem I/O.

### D2 — Catálogo de notícias como adaptador da porta, reutilizando o read-model

`application/noticias/catalogo.py` define a porta `NoticiasRepository`
(reaproveitando `CatalogoRepository`/`montar_catalogo` de
`application/documentos`) e o caso de uso de consulta. `noticias_catalogo.py`
vira o adaptador que lê índice/shards e delega a montagem ao read-model, já
preparando a data de publicação de forma ordenável. Alternativa: manter a
montagem no adaptador. Rejeitada por deixar regra de agrupamento fora de
`application`.

### D3 — Ordenação do lote como read-model de `application`

`pendentes_ordenados` e a chave determinista migram para
`application/noticias/lote.py`, operando sobre as entidades de domínio. A data
de publicação é interpretada uma única vez (no adaptador/caso de uso) e exposta
como ordinal, para que a ordenação seja pura e determinista. Alternativa:
manter a ordenação no painel. Rejeitada por perpetuar regra de negócio na UI e
exigir Tk nos testes.

### D4 — Índice compacto do chat em `application`

`application/noticias/fonte_chat.py` concentra `_montar` (índice com teto de
caracteres), `_intercalar`, `_agrupar_por_secao`, `_ordem_secoes` e
`_chave_curta` sobre as entidades de domínio. `FonteNoticias` (apresentação)
apenas injeta o store de texto/extrator e formata o bloco final. Alternativa:
manter a montagem na apresentação. Rejeitada por misturar orquestração e
desenho.

### D5 — Painel recebe dependências prontas

`NoticiasPanel` recebe caso de uso e portas por parâmetro, espelhando
`DocumentTreePanel`; o composition root (`app_wiring.py`) instancia os
adaptadores. Sem defaults que criem infraestrutura dentro do painel. Alternativa:
manter defaults `NoticiasCatalog()`. Rejeitada por perpetuar o import
`presentation -> infrastructure`.

### D6 — Parsing de data permanece em `infrastructure`

`data_noticia` é parsing e fica em `infrastructure`. O adaptador/caso de uso
expõe a data já interpretada (ordinal) na entidade lida; a aplicação ordena sem
reparsear. Alternativa: mover `data_noticia` para `domain`. Rejeitada para
respeitar o non-goal de não mover parsing.

## Risks / Trade-offs

- [Grafo de notícias grande] → mover na ordem das dependências (entidades e
  classificação antes dos adaptadores) e validar paridade a cada passo.
- [`NoticiasCatalog` também alimenta o chat] → migrar a fonte de notícias do chat
  junto desta fatia, para não criar dependência cruzada entre `application` e
  `presentation`.
- [Ordenação depender de parsing] → preparar o ordinal no adaptador e cobrir com
  testes puros de ordenação determinista.
- [Cobertura/mutation ao mover] → rodar `make test` e o guardrail ao final;
  recalcular se necessário.

## Migration Plan

1. Criar `domain/noticias` com classificação e entidades; atualizar importadores.
2. Criar porta, read-model de catálogo, ordenação do lote e índice do chat em
   `application/noticias`.
3. Fazer `noticias_catalogo.py` implementar a porta e manter os shards/índice
   como adaptadores.
4. Injetar dependências no `NoticiasPanel` e na fonte de notícias do chat; ajustar
   `app_wiring`/`app_tab_layout`.
5. Remover as 3 entradas da allowlist; migrar testes puros; rodar `make test` e
   `make quality-gate`.

Rollback: reverter o change restaura os módulos e a allowlist; comportamento
idêntico.

## Open Questions

- Nome exato do pacote (`application/noticias/` vs módulos soltos) e a divisão de
  `domain/noticias` em `entities.py`/`classificacao.py`: decidir na
  implementação, sem impacto no contrato.
- O campo de data ordinal pode ser derivado no adaptador (infraestrutura) ou no
  caso de uso (aplicação); o contrato observável não muda.
