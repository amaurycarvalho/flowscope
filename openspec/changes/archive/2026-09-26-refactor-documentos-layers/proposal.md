## Why

A fatia de Documentos concentra o maior volume de testes de UI do programa: `test_document_tree_panel.py` tem 133 testes, dos quais 73 exigem `DISPLAY` e não rodam no CI headless. Ao mesmo tempo, as entidades de catálogo (`DocumentoArquivo`, `CatalogoTicker`) vivem em `infrastructure/document_catalog.py` e a apresentação importa stores de infraestrutura diretamente (`document_tree_panel`, `document_summary`, `document_guidance`, `document_grouping`). Esta fatia move as entidades e as regras para `domain`/`application`, deixando a apresentação apenas desenhar, e migra os testes puros para as camadas internas.

## What Changes

- Entidades de catálogo (`DocumentoArquivo`, `CategoriaDocumentos`, `MesDocumentos`, `AnoDocumentos`, `CatalogoTicker`) saem de `infrastructure/document_catalog.py` para `domain/documents/`.
- Porta `CatalogoRepository` e caso de uso de consulta do catálogo em `application`, incluindo a montagem/ordenação do catálogo e a derivação da chave estável do documento.
- `infrastructure/document_catalog.py` passa a implementar a porta varrendo o cache (apenas I/O), usando as entidades de domínio.
- Porta `DocumentSummaryStore` em `application` (a `DocumentTextStore` já existe); `JsonDocumentSummaryStore` e `JsonDocumentTextStore` passam a implementá-las.
- `DocumentSummaryService` e `GuidanceService` saem de `presentation/gui/charts/` para `application`.
- `document_tree_panel` recebe as dependências por injeção (caso de uso + portas) pelo composition root, sem importar `infrastructure`.
- Remoção das entradas correspondentes de `tests/architecture/allowlist.txt`.
- Migração de testes puros de documentos para `tests/test_domain`/`tests/test_application`; o painel mantém apenas testes de wiring, estado e thread.

## Capabilities

### New Capabilities

### Modified Capabilities

Opta por não alterar specs (`skip_specs: true`): refatoração que preserva o comportamento observável, implementando o contrato `layer-boundaries` do change `clean-architecture-layering`.

## Impact

- **Depende de**: `add-layer-architecture-guardrails` (allowlist e teste de fronteira).
- **Código movido**: `infrastructure/document_catalog.py`, `infrastructure/document_summaries.py`, `infrastructure/document_texts.py`; `presentation/gui/charts/document_tree_panel.py`, `document_tree_view.py`, `document_grouping.py`, `document_summary.py`, `document_guidance.py`, `document_flow_mixin.py`; `presentation/gui/resumos_job.py`; `presentation/gui/chat/documentos.py`.
- **Novos tipos**: `domain/documents/*`, portas e serviços em `application`.
- **Testes migrados**: ~60 dos 133 testes do painel, além de `test_document_summaries.py` (9), `test_document_texts.py` (10) e `test_document_catalog.py` (10) reorganizados por camada; os ~73 marcados `needs_display` caem para o subconjunto de wiring/estado/thread.
- **Sem alteração de comportamento**: árvore, preview, resumos e guidance permanecem idênticos.
