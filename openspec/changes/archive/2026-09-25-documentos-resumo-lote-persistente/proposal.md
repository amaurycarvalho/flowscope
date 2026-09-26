## Why

No lote "Resumir pendentes" da sub-aba "Documentos", cada resumo só chega ao disco quando a thread do Tk drena a mensagem correspondente. Como a fila não é drenada no cancelamento (`app_resumos_actions.py:110`) e nada é gravado se o aplicativo for fechado durante o lote, resumos já gerados pela LLM podem ser perdidos por uma interrupção. O custo da chamada à LLM torna essa perda cara.

## What Changes

- Cada resumo passa a ser **gravado imediatamente após a geração**, na thread de trabalho do lote, antes de processar o próximo documento — em vez de esperar a aplicação na thread do Tk.
- Introduz um **seam reutilizável** no fluxo compartilhado (`DocumentFlowMixin` + `ResumosPendentesJob`): gerar e persistir no worker, publicar o resultado e a thread do Tk apenas refletir em memória e pré-visualização, sem escrever no store.
- Torna `JsonDocumentSummaryStore.salvar` **segura a escritas concorrentes** (lock), preservando os resumos já gravados e evitando *lost update* entre o lote e a pré-visualização individual.
- Interrupção por cancelamento, fechamento do aplicativo ou crash passa a preservar todos os resumos já gerados; perde-se no máximo o item em processamento.
- Comportamento observável dos demais painéis permanece igual.

## Capabilities

### New Capabilities

<!-- nenhuma -->

### Modified Capabilities

- `documentos-ticker-panel`: o resumo em lote dos documentos pendentes passa a persistir cada resumo imediatamente após a geração, sobrevivendo a interrupções.

## Impact

- **Código afetado**: `presentation/gui/resumos_job.py`, `presentation/gui/app_resumos_actions.py`, `presentation/gui/charts/document_flow_mixin.py`, `presentation/gui/charts/document_tree_panel.py`, `infrastructure/document_summaries.py`.
- **Testes afetados**: `tests/test_presentation` (lote, aplicação de resultado, cancelamento) e `tests/test_infrastructure` (concorrência da store).
- **Depende de**: nada. Introduz o seam reutilizado por `noticias-resumo-lote-ordenado`.
- **Sem dependências externas novas**; usa `threading` da biblioteca padrão.
