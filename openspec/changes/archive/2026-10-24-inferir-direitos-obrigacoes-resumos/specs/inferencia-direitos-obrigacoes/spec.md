## Purpose

Extrair, validar e persistir direitos e obrigações de renda fixa citados nos resumos de documentos, preservando a proveniência e a precedência dos dados oficiais da CVM.

## ADDED Requirements

### Requirement: Extração estruturada a partir de resumos

O sistema DEVE inferir direitos e obrigações exclusivamente a partir dos resumos longos já persistidos de documentos do ticker, sem reabrir o PDF, reextrair texto ou baixar dados. A resposta da LLM DEVE ser validada em um esquema estruturado com tipo de título, papel (obrigação ou direito), descrição, documento de origem, trecho de evidência e confiança. Tipos fora do enum conhecido DEVEM ser descartados, e itens sem evidência ou sem documento de origem NÃO DEVEM ser persistidos.

#### Scenario: Inferência a partir de resumo existente
- **WHEN** um Relatório Gerencial ou Relatório Mensal tem resumo longo persistido e a inferência é executada
- **THEN** os itens extraídos DEVEM conter tipo, papel, evidência, documento de origem e confiança

#### Scenario: Resposta inválida é descartada
- **WHEN** a LLM devolve um tipo desconhecido ou um item sem evidência
- **THEN** o item NÃO DEVE ser persistido e a inferência DEVE continuar com os demais itens válidos

#### Scenario: PDF não é reaberto
- **WHEN** a inferência é executada para um documento já resumido
- **THEN** nenhuma extração de PDF ou download DEVE ocorrer

### Requirement: Cache e proveniência das inferências

O sistema DEVE persistir as inferências em `<cache>/direitos-obrigacoes/inferencias/<TICKER>.json`, separado do cache oficial, com `parser_version`/versão do prompt, `fonte=LLM`, `adquirido_em` e, por item, documento, trecho, confiança e data de referência. A inferência DEVE ser reutilizada quando o hash do documento e a versão do prompt não mudarem, e substituída atomicamente quando houver mudança.

#### Scenario: Primeira inferência grava o cache
- **WHEN** não existe cache de inferências e a extração produz itens válidos
- **THEN** o arquivo do ticker DEVE ser gravado atomicamente com a proveniência de cada item

#### Scenario: Repetição sem mudança reutiliza
- **WHEN** o documento e a versão do prompt não mudaram desde a última inferência
- **THEN** a LLM NÃO DEVE ser chamada novamente para aquele documento

#### Scenario: Documento alterado invalida
- **WHEN** o hash do resumo do documento muda
- **THEN** a inferência daquele documento DEVE ser refeita e o cache substituído

### Requirement: Elegibilidade e feature flag

A inferência DEVE ocorrer somente quando a flag `renda_fixa.inferir_no_resumo` estiver ligada, houver LLM configurada e a cobertura oficial do ticker estiver vazia ou parcial para ao menos um tipo. A flag desligada DEVE manter o comportamento atual do lote, sem chamadas adicionais à LLM.

#### Scenario: Flag desligada
- **WHEN** `renda_fixa.inferir_no_resumo` é `false`
- **THEN** nenhuma inferência DEVE ser executada e o lote DEVE concluir como antes

#### Scenario: Cobertura oficial completa
- **WHEN** os dados oficiais já cobrem todos os tipos do ticker
- **THEN** a inferência NÃO DEVE ser executada

#### Scenario: Cobertura parcial
- **WHEN** existe ao menos um tipo sem fonte oficial ou com ausência explícita
- **THEN** a inferência DEVE ser executada para os documentos elegíveis do ticker

### Requirement: Precedência do dado oficial

Itens inferidos NUNCA DEVEM substituir, alterar ou completar silenciosamente um item oficial. Em conflito de tipo e identificação, o item oficial DEVE prevalecer e o item inferido correspondente NÃO DEVE ser exibido como se fosse oficial. Itens sem correspondência oficial PODEM ser exibidos como inferidos, sempre rotulados.

#### Scenario: Conflito com título oficial
- **WHEN** a inferência cita um título que já existe na fonte oficial
- **THEN** o item oficial DEVE permanecer e o inferido NÃO DEVE sobrescrevê-lo

#### Scenario: Item apenas inferido
- **WHEN** a inferência cita um título ausente das fontes oficiais
- **THEN** o item DEVE ser exibido como inferido pela IA, com a proveniência do documento

### Requirement: Falha e cancelamento não perdem resumos

Falha da LLM, resposta inválida ou cancelamento durante a inferência NÃO DEVEM desfazer os resumos já gerados nem interromper a gravação dos demais itens concluídos. O desfecho da inferência DEVE ser distinto do desfecho dos resumos.

#### Scenario: Falha da LLM na inferência
- **WHEN** a LLM falha durante a inferência
- **THEN** os resumos persistidos DEVEM permanecer e o desfecho DEVE registrar a falha da inferência separadamente

#### Scenario: Cancelamento durante a inferência
- **WHEN** o usuário cancela o lote durante a inferência
- **THEN** os itens já inferidos e persistidos DEVEM ser preservados e a operação DEVE encerrar sem erro fatal
