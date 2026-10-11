## MODIFIED Requirements

### Requirement: Botão "Resumir pendentes" na barra de documentos

A sub-aba "Documentos" DEVE exibir um botão "Resumir pendentes" na barra de controles, imediatamente após o seletor de modelo ativo e o botão de configuração, sempre visível. O botão DEVE estar habilitado somente quando a LLM estiver configurada, nenhum resumo em lote estiver em andamento e existir, no ticker apresentado, ao menos um documento que necessite de resumo ou — quando a IA estiver ativa — ao menos um Relatório Gerencial (documento da categoria `Relatorio`, própria de FII) cuja avaliação de guidance seja acionável. Um documento necessita de resumo quando não tem `long_summary` íntegro E o seu texto não foi concluído como ausente: documentos cuja ausência definitiva de texto já foi determinada e persistida (o marcador de ausência ou conteúdo apenas em branco) NÃO DEVEM contar como pendentes. Uma avaliação de guidance é acionável quando a entrada do RG no ledger está ausente, ou está marcada como `deterministico` e a IA está funcional sem falha de interação registrada para esse RG; uma entrada determinística cuja última tentativa de IA registrou falha NÃO DEVE manter o botão habilitado. Caso contrário, o botão DEVE estar desabilitado. O Relatório Gerencial É o documento de FII usado como gatilho; não se DEVE depender da classificação de tipo do ticker, indisponível no painel. A LLM DEVE ser considerada configurada quando o provedor for diferente de `none` e as dependências `[llm]` estiverem presentes. A verificação de pendências de guidance DEVE consultar o ledger fora da thread da interface, junto da leitura do catálogo, e a thread do Tk NÃO DEVE ler o ledger ao reavaliar o botão. Ao salvar a configuração ou trocar o provedor pelo combobox, o estado do botão DEVE ser reavaliado. Durante o lote e durante as cargas de dados, o botão DEVE ser desabilitado e restaurado ao término, junto com os demais controles do painel.

#### Scenario: Botão disponível na barra

- **WHEN** o usuário navega para a sub-aba "Documentos"
- **THEN** o botão "Resumir pendentes" DEVE ser exibido imediatamente após o seletor de modelo ativo e o botão de configuração

#### Scenario: Habilitado com pendentes e LLM configurada

- **WHEN** a LLM está configurada e o ticker apresentado tem ao menos um documento sem `long_summary` cujo texto não foi concluído como ausente
- **THEN** o botão "Resumir pendentes" DEVE estar habilitado

#### Scenario: Documento sem texto extraível não habilita

- **WHEN** todos os documentos do ticker apresentado já têm `long_summary` ou tiveram a ausência de texto concluída e persistida
- **THEN** o botão "Resumir pendentes" NÃO DEVE ser habilitado por esses documentos

#### Scenario: Habilitado com RGs já resumidos pendentes de guidance

- **WHEN** a LLM está configurada e funcional, todos os documentos do ticker apresentado já têm `long_summary`, e ao menos um Relatório Gerencial (categoria `Relatorio`) tem avaliação de guidance acionável
- **THEN** o botão "Resumir pendentes" DEVE estar habilitado

#### Scenario: Falha de IA no guidance não mantém o botão

- **WHEN** a única pendência seria um Relatório Gerencial já resumido cuja última avaliação por IA falhou
- **THEN** o botão "Resumir pendentes" NÃO DEVE permanecer habilitado por conta dessa entrada

#### Scenario: Desabilitado com pendências de guidance sem IA

- **WHEN** a IA não está configurada e o único pendente é um Relatório Gerencial já resumido sem avaliação de guidance marcada como `ia`
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado

#### Scenario: Sem Relatório Gerencial não habilita por guidance

- **WHEN** o ticker apresentado só tem documentos de outras categorias, todos com `long_summary`, ainda que exista guidance no ledger
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado

#### Scenario: Desabilitado sem LLM configurada

- **WHEN** a LLM não está configurada
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado, sem ser ocultado

#### Scenario: Desabilitado sem pendentes

- **WHEN** todos os documentos do ticker apresentado já têm `long_summary`
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado

#### Scenario: Reavaliação quando o catálogo muda

- **WHEN** o último documento pendente passa a ter `long_summary` por um resumo individual (sem troca de aba)
- **THEN** o botão "Resumir pendentes" DEVE ser reavaliado e ficar desabilitado

#### Scenario: Reavaliação após salvar a configuração

- **WHEN** o usuário salva uma configuração de LLM válida no diálogo de configuração e há documentos pendentes
- **THEN** o botão "Resumir pendentes" DEVE passar a estar habilitado

#### Scenario: Reavaliação após trocar o modelo

- **WHEN** o usuário troca o provedor ativo pelo combobox e há documentos pendentes
- **THEN** o botão "Resumir pendentes" DEVE ser reavaliado conforme a disponibilidade da LLM

#### Scenario: Desabilitado durante o lote e cargas de dados

- **WHEN** um resumo em lote ou uma carga de dados está em andamento
- **THEN** o botão "Resumir pendentes" DEVE ser desabilitado junto com os demais controles do painel e restaurado ao término

### Requirement: Resumo em lote dos documentos pendentes

Ao acionar o botão "Resumir pendentes", o sistema DEVE processar, fora da thread da interface, os documentos do ticker apresentado que necessitam de resumo — sem `long_summary` íntegro cujo texto não tenha sido concluído como ausente — e os Relatórios Gerenciais (categoria `Relatorio`, própria de FII) já resumidos cuja avaliação de guidance seja acionável (entrada ausente no ledger, ou `deterministico` com a IA funcional e sem falha de interação registrada), em duas fases: preparar o texto — reutilizando o texto em cache e convertendo apenas quando ausente — e gerar o resumo via LLM, como se cada documento tivesse sido selecionado. Documentos cuja ausência definitiva de texto já foi determinada e persistida NÃO DEVEM integrar o conjunto de pendentes. Para os Relatórios Gerenciais já resumidos, a geração de resumo DEVE ser pulada e apenas a avaliação de guidance DEVE ocorrer, reaproveitando os resumos e o texto em cache, sem reextrair o arquivo. Cada resumo gerado DEVE ser gravado no cache persistente imediatamente após a sua geração e antes de processar o próximo documento, na própria thread de trabalho, de modo que uma interrupção — cancelamento, fechamento do aplicativo ou falha — preserve todos os resumos já gerados e perca no máximo o documento em processamento. O `short_summary` e o `long_summary` resultantes DEVEM ser refletidos no catálogo do documento. O andamento DEVE ser exibido na barra de status com a barra de progresso, uma fase por vez. Documentos sem texto extraível DEVEM ser pulados, sem chamada à LLM. Ao concluir, o sistema DEVE exibir o desfecho, incluindo as falhas de avaliação de guidance, e reavaliar o estado do botão.

#### Scenario: Lote com documentos pendentes
- **WHEN** o usuário aciona "Resumir pendentes" com a LLM configurada e documentos sem `long_summary` cujo texto não foi concluído como ausente
- **THEN** o sistema DEVE gerar e persistir os resumos de cada documento pendente e exibir o desfecho

#### Scenario: Documento com ausência de texto concluída não é alvo
- **WHEN** o usuário aciona "Resumir pendentes" e há um documento sem `long_summary` cuja ausência de texto já foi determinada e persistida
- **THEN** esse documento NÃO DEVE integrar o conjunto processado pelo lote

#### Scenario: Lote avalia guidance de RG já resumido
- **WHEN** o usuário aciona "Resumir pendentes" e há um Relatório Gerencial já resumido com avaliação de guidance acionável
- **THEN** o sistema DEVE avaliar o guidance desse RG sem regerar seu resumo, reaproveitando os resumos e o texto em cache

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
- **WHEN** um documento do ticker já tem `long_summary` íntegro
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

#### Scenario: Falha de guidance é reportada no desfecho
- **WHEN** a avaliação de guidance de um RG pendente falha por indisponibilidade da IA
- **THEN** o desfecho do lote DEVE informar a falha de guidance, além dos resumos gerados

#### Scenario: Resultado do lote é descartado ao trocar de ticker
- **WHEN** o ticker apresentado muda enquanto o lote está em andamento
- **THEN** os resultados do lote anterior NÃO DEVEM ser aplicados ao novo ticker
