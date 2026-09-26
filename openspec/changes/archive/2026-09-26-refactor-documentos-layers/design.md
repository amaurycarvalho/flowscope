## Context

Ver `proposal.md` — Why, e o contrato em `openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md`. Estado atual relevante:

- `infrastructure/document_catalog.py` define as entidades (`DocumentoArquivo`, `CatalogoTicker`, ...), varre o cache (`DocumentCatalog.catalogo`) e monta a hierarquia (`montar_catalogo`), tudo no mesmo módulo.
- `infrastructure/document_summaries.py` persiste JSON por escopo e `infrastructure/document_texts.py` persiste JSON por escopo (Documentos; inalterado — `noticias-cache-sharding` particiona o cache de notícias por ano e mês); `application/document_text_port.py` já define a porta `DocumentTextStore`.
- `presentation/gui/charts/document_tree_panel.py` instancia `DocumentCatalog`, `JsonDocumentSummaryStore`, `JsonDocumentTextStore` e `JsonGuidanceStore` diretamente; `document_summary.py` e `document_guidance.py` contêm serviços (`DocumentSummaryService`, `GuidanceService`) que orquestram I/O + LLM.
- `document_grouping.py` renderiza Markdown a partir de entidades de infraestrutura.
- Guardrail: a allowlist tem 16 entradas `presentation -> infrastructure`, das quais 8 são desta fatia (`document_flow_mixin`, `document_grouping`, `document_guidance`, `document_summary`, `document_tree_panel`, `document_tree_view`, `resumos_job` e `chat/documentos.py`).
- Estado após `documentos-resumo-lote-persistente` e `noticias-resumo-lote-ordenado`: `infrastructure/document_summaries.py` serializa `salvar` com um lock; `DocumentSummaryService` ganhou `atualizar` (reflete sem gravar); e `document_flow_mixin.py`/`resumos_job.py` concentram o seam de persistência do lote no worker (`persistir_no_lote`, `gerar_e_persistir`, `refletir_resumo`). Esses elementos fazem parte do comportamento a preservar e migram junto.
- Estado após `noticias-cache-sharding`: o escopo de cache das notícias é particionado por ano e mês (`NOTICIAS-<ANO>-<MES>.json`), derivado da chave por um wrapper de notícias; `JsonDocumentTextStore`/`JsonDocumentSummaryStore` e o layout dos escopos de Documentos permanecem inalterados. A assinatura da porta `DocumentTextStore` (`obter`/`salvar`) não muda; esta fatia continua movendo apenas os adaptadores de Documentos.

## Goals / Non-Goals

**Goals:**

- Colocar entidades de catálogo em `domain/documents`.
- Colocar portas, montagem do catálogo e serviços de resumo/guidance em `application`.
- Fazer `document_tree_panel` depender de portas/use cases, recebidos por injeção do composition root.
- Remover as 8 entradas de documentos da allowlist.
- Migrar testes puros para `test_domain`/`test_application`.
- Preservar o seam de persistência do lote no worker ao mover os serviços/job.

**Non-Goals:**

- Não mexer na fatia de Notícias (`noticias_catalogo`, `noticias_panel`), que reaproveita `montar_catalogo` e será tratada em `refactor-noticias-layers` (inclui a ordenação `NoticiasPanel.pendentes_ordenados`).
- Não criar specs novas; o comportamento é preservado.
- Não redesenhar a árvore/preview nem trocar widgets.

## Decisions

### D1 — Entidades em `domain/documents`, montagem em `application`

`DocumentoArquivo`, `CategoriaDocumentos`, `MesDocumentos`, `AnoDocumentos` e `CatalogoTicker` vão para `domain/documents/entities.py`. A função pura `montar_catalogo` e a ordenação vão para `application/documentos/catalogo.py`, junto do caso de uso que consulta o repositório. Alternativa: manter `montar_catalogo` em `domain`. Preferimos `application` para que `domain` fique só com as entidades e o read-model fique explícito na aplicação.

### D2 — Porta `CatalogoRepository`, adaptador de filesystem

`application` define a porta `CatalogoRepository.catalogo(ticker) -> CatalogoTicker`. `infrastructure/document_catalog.py` vira o adaptador que varre `bdr/`, `informe-mensal/` e `documentos-relevantes/` e delega a montagem ao read-model da aplicação. `chave_documento` (chave estável) muda para `application`. Alternativa: caso de uso orquestrando a varredura diretamente. Rejeitada por manter I/O na aplicação.

### D3 — Porta `DocumentSummaryStore`

Espelha a `DocumentTextStore` já existente em `application`. `JsonDocumentSummaryStore` passa a implementá-la. Alternativa: usar a classe concreta na aplicação. Rejeitada por acoplar aplicação à infraestrutura.

### D4 — `DocumentSummaryService` e `GuidanceService` para `application`

Os serviços que hoje vivem em `presentation/gui/charts/document_summary.py` e `document_guidance.py` são orquestração (store + LLM), não desenho. Vão para `application/documentos/`. A apresentação apenas chama e exibe. Alternativa: mantê-los na apresentação recebendo portas. Rejeitada por manter lógica de aplicação na UI e exigir Tk nos testes.

### D5 — Painel recebe dependências prontas

`DocumentTreePanel` recebe o caso de uso de catálogo e as portas de store por parâmetro; o composition root (`app_wiring.py`) instancia os adaptadores. Sem defaults que criem infraestrutura dentro do painel. Alternativa: manter defaults `DocumentCatalog()`. Rejeitada por perpetuar o import `presentation -> infrastructure`.

### D6 — Seam de persistência do lote migra para `application`

`persistir_no_lote`, `gerar_e_persistir` e `refletir_resumo` (hoje em `document_flow_mixin.py`) e o gancho `_gerar_resumo` de `resumos_job.py` são orquestração de aplicação — gerar, gravar no worker e refletir no Tk — e migram para `application`, junto de `DocumentSummaryService` e da porta `DocumentSummaryStore`, preservando a gravação imediata após cada item. O override `persistir_no_lote() -> True` de cada painel permanece na apresentação apenas como configuração do painel. Alternativa: manter o seam na apresentação. Rejeitada por perpetuar orquestração na UI e contrariar a fronteira de view-model.

## Risks / Trade-offs

- [Fatia grande, muitos testes] → mover testes junto do código, sem reescrever; validar paridade a cada passo e encolher a allowlist só no fim.
- [Notícias reaproveita `montar_catalogo`] → o novo módulo em `application` deve ser genérico; `refactor-noticias-layers` ajusta os imports.
- [Defaults de construtor removidos quebram chamadas] → atualizar o composition root e os testes que instanciam o painel, fornecendo fakes.
- [Seam de persistência do lote perdido na migração] → mover os métodos junto do serviço/job e cobrir com os testes de cancelamento/interrupção do lote (`test_resumos_job.py`, fluxo de `refletir_resumo`).
- [Cobertura/mutation ao mover] → rodar `make test` e o guardrail ao final; recalcular se necessário.

## Migration Plan

1. Criar `domain/documents` com as entidades (sem alterar comportamento) e mover os testes de entidade.
2. Criar portas e read-model em `application`; fazer `infrastructure/document_catalog.py` implementar a porta.
3. Mover `DocumentSummaryService` e `GuidanceService` para `application`.
4. Atualizar `presentation` para injetar dependências e remover imports de `infrastructure`.
5. Remover as entradas de documentos da allowlist; migrar testes puros; rodar `make test` e `make quality-gate`.

Rollback: reverter o change restaura os módulos e a allowlist; comportamento idêntico.

## Open Questions

- Nome exato do pacote de aplicação (`application/documentos/` vs módulos soltos como `document_catalog.py`): decidir na implementação, sem impacto no contrato.
