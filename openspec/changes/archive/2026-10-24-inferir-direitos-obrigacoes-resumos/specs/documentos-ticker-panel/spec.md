## ADDED Requirements

### Requirement: Fase de inferência no lote "Resumir pendentes"

Ao concluir a geração de resumos, o lote "Resumir pendentes" DEVE executar uma fase opcional de inferência de direitos e obrigações quando a flag `renda_fixa.inferir_no_resumo` estiver ligada, houver LLM configurada e a cobertura oficial do ticker estiver vazia ou parcial. A fase DEVE usar os resumos longos já persistidos, sem reextrair PDFs, e DEVE publicar progresso próprio ("inferência de direitos e obrigações") antes da finalização. Falha ou cancelamento da inferência NÃO DEVEM invalidar os resumos já gravados.

#### Scenario: Inferência após os resumos
- **WHEN** o lote gera resumos e a flag de inferência está ligada com cobertura oficial parcial
- **THEN** a fase de inferência DEVE ser executada depois dos resumos e antes da finalização

#### Scenario: Flag desligada mantém o lote atual
- **WHEN** a flag de inferência está desligada
- **THEN** o lote DEVE concluir sem fase adicional e sem chamadas de inferência

#### Scenario: Falha da inferência preserva resumos
- **WHEN** a inferência falha após os resumos terem sido gravados
- **THEN** os resumos DEVEM permanecer e o desfecho DEVE distinguir a falha da inferência

#### Scenario: Cancelamento na inferência
- **WHEN** o usuário cancela durante a fase de inferência
- **THEN** o lote DEVE encerrar sem apagar os resumos e as inferências já persistidas

### Requirement: Estado do botão considera inferência pendente

O botão "Resumir pendentes" DEVE ser habilitado também quando, com a flag ligada, a LLM configurada e a cobertura oficial vazia ou parcial, existir ao menos um resumo longo de Relatório Gerencial ou Relatório Mensal ainda não inferido. Sem essa condição, a inclusão da inferência NÃO DEVE manter o botão habilitado apenas por si só.

#### Scenario: Inferência pendente habilita o botão
- **WHEN** não há documentos sem resumo, mas existe inferência pendente elegível
- **THEN** o botão "Resumir pendentes" DEVE estar habilitado

#### Scenario: Flag desligada não habilita
- **WHEN** a flag de inferência está desligada e não há documentos sem resumo nem guidance acionável
- **THEN** o botão "Resumir pendentes" DEVE permanecer desabilitado
