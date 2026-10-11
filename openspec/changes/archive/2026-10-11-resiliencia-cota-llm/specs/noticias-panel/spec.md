## MODIFIED Requirements

### Requirement: Resumo curto e longo por LLM

O sistema DEVE gerar, para cada notícia, um resumo curto e um longo usando a LLM, persistindo-os em cache por notícia. A geração DEVE reutilizar o serviço de resumo existente e tolerar falhas transitórias da LLM sem interromper o processamento em lote, exceto quando a falha for de cota/limite do provedor (`LLMRateLimitError`), caso em que o lote DEVE ser interrompido imediatamente e o desfecho reportado uma única vez. Quando a LLM não estiver configurada, a sub-aba DEVE orientar a configuração.

#### Scenario: Geração de resumo
- **WHEN** a LLM está configurada e o artigo tem texto, mas não tem resumo
- **THEN** os resumos curto e longo DEVEM ser gerados e persistidos

#### Scenario: LLM não configurada
- **WHEN** a LLM não está configurada
- **THEN** a sub-aba DEVE orientar a configuração, sem gerar resumos

#### Scenario: Falha da LLM no lote
- **WHEN** a geração de resumo de um item falha por erro transitório (não de cota) durante o lote
- **THEN** o erro DEVE ser registrado e os demais itens DEVEM continuar

#### Scenario: Cota esgotada interrompe o lote
- **WHEN** a geração de resumo de um item falha com `LLMRateLimitError` durante o lote
- **THEN** o lote NÃO DEVE processar os demais itens e DEVE reportar a cota esgotada uma única vez
