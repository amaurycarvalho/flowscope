## ADDED Requirements

### Requirement: Estado derivado do botão "Resumir pendentes" durante o lote

Enquanto um resumo em lote estiver em andamento, o estado derivado do botão "Resumir pendentes" DEVE permanecer desabilitado, ainda que o catálogo mude (documentos passando a ter `long_summary`) ou que a reavaliação de estado seja disparada no meio do processamento. Ao término do lote — conclusão ou interrupção — o estado DEVE ser reavaliado considerando a disponibilidade remanescente: habilitado se a LLM estiver configurada e ainda houver documentos sem `long_summary`; desabilitado caso contrário.

#### Scenario: Reavaliação por documento resumido não reabilita durante o lote
- **WHEN** o lote está em andamento e documentos do ticker passam a ter `long_summary` a cada resultado aplicado
- **THEN** o botão "Resumir pendentes" DEVE permanecer desabilitado durante todo o processamento, até o término

#### Scenario: Reavaliação intermediária por resumo individual não reabilita durante o lote
- **WHEN** o lote está em andamento e uma reavaliação do catálogo é disparada (por resumo individual concorrente ou recarregamento do painel)
- **THEN** o botão "Resumir pendentes" DEVE permanecer desabilitado

#### Scenario: Reabilitação ao término com pendentes restantes
- **WHEN** o lote é interrompido por erro e ainda há documentos do ticker sem `long_summary`
- **THEN** o botão "Resumir pendentes" DEVE voltar a ficar habilitado

#### Scenario: Desabilitado ao término sem pendentes restantes
- **WHEN** o lote conclui e todos os documentos do ticker já têm `long_summary`
- **THEN** o botão "Resumir pendentes" DEVE permanecer desabilitado
