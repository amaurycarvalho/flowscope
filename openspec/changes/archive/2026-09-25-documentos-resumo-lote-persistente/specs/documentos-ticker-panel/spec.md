## MODIFIED Requirements

### Requirement: Resumo em lote dos documentos pendentes

Ao acionar o botão "Resumir pendentes", o sistema DEVE processar, fora da thread da interface, todos os documentos do ticker apresentado sem `long_summary`, em duas fases: preparar o texto — reutilizando o texto em cache e convertendo apenas quando ausente — e gerar o resumo via LLM, como se cada documento tivesse sido selecionado. Cada resumo gerado DEVE ser gravado no cache persistente imediatamente após a sua geração e antes de processar o próximo documento, na própria thread de trabalho, de modo que uma interrupção — cancelamento, fechamento do aplicativo ou falha — preserve todos os resumos já gerados e perca no máximo o documento em processamento. O `short_summary` e o `long_summary` resultantes DEVEM ser refletidos no catálogo do documento. O andamento DEVE ser exibido na barra de status com a barra de progresso, uma fase por vez. Documentos sem texto extraível DEVEM ser pulados, sem chamada à LLM. Ao concluir, o sistema DEVE exibir o desfecho e reavaliar o estado do botão.

#### Scenario: Lote com documentos pendentes
- **WHEN** o usuário aciona "Resumir pendentes" com a LLM configurada e documentos sem `long_summary`
- **THEN** o sistema DEVE gerar e persistir os resumos de cada documento pendente e exibir o desfecho

#### Scenario: Progresso em duas fases
- **WHEN** o lote está em andamento
- **THEN** a barra de status e a barra de progresso DEVEM exibir a fase corrente ("preparar texto" e, em seguida, "resumir") com o avanço de cada uma, indicando quantos documentos foram concluídos e o total (ex.: `Preparando textos — 3/40`)

#### Scenario: Avanço da fase é exibido durante o processamento
- **WHEN** uma fase processa vários documentos e cada um leva tempo para concluir
- **THEN** a barra de progresso e a barra de status DEVEM avançar a cada documento concluído, sem aguardar o término da fase

#### Scenario: Fase instantânea continua visível
- **WHEN** a preparação dos textos é instantânea (todos os textos já estão em cache) e o lote avança para a fase de resumo
- **THEN** a fase "preparar texto" DEVE ter sido exibida na barra de status antes de "resumir", ainda que por tempo mínimo

#### Scenario: Documento já resumido é pulado
- **WHEN** um documento do ticker já tem `long_summary`
- **THEN** ele NÃO DEVE ser reprocessado no lote

#### Scenario: Documento sem texto extraível é pulado
- **WHEN** um documento pendente não tem texto extraível
- **THEN** o sistema NÃO DEVE chamar a LLM para ele e DEVE contabilizá-lo como pulado no desfecho

#### Scenario: Resumo gerado fica disponível na lista
- **WHEN** o lote conclui
- **THEN** uma seleção posterior do agrupamento DEVE exibir o `short_summary` dos documentos resumidos

#### Scenario: Persistência imediata por documento
- **WHEN** o lote gera o resumo de um documento e avança para o próximo
- **THEN** o resumo do documento anterior já DEVE estar gravado no cache persistente, antes da geração do próximo

#### Scenario: Interrupção preserva os resumos já gerados
- **WHEN** o lote é cancelado, o aplicativo é fechado ou falha após gerar resumos de alguns documentos
- **THEN** os resumos já gerados DEVEM estar gravados no cache persistente

#### Scenario: Interrupção por erro
- **WHEN** ocorre um erro em qualquer documento durante o lote
- **THEN** o lote DEVE ser interrompido, a barra de status DEVE reportar o documento e um motivo de falha amigável, e os controles DEVEM ser liberados

#### Scenario: Resultado do lote é descartado ao trocar de ticker
- **WHEN** o ticker apresentado muda enquanto o lote está em andamento
- **THEN** os resultados do lote anterior NÃO DEVEM ser aplicados ao novo ticker
