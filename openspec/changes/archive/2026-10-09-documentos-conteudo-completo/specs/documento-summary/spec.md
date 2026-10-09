## MODIFIED Requirements

### Requirement: Fórmula XYZ no prompt

O serviço DEVE instruir a LLM a resumir usando a fórmula XYZ — X: o que o texto diz; Y: por que isso importa; Z: o que se conclui — tanto para o resumo curto quanto para o longo, e DEVE solicitar os dois resumos em uma única chamada de completion. O prompt DEVE pedir o resumo curto em **1 a 2 frases** e o longo em **parágrafos** (não uma contagem exata de caracteres), mantendo os tetos de caracteres apenas como salvaguarda.

#### Scenario: Prompt contém a fórmula e os limites
- **WHEN** o prompt é montado para um documento
- **THEN** ele DEVE conter as instruções XYZ e os tetos de 280 caracteres para o resumo curto e 1500 para o longo

#### Scenario: Prompt pede frases, não uma contagem exata
- **WHEN** o prompt é montado
- **THEN** ele DEVE solicitar o curto em 1 a 2 frases e o longo em parágrafos, para reduzir o risco de corte no meio da frase

#### Scenario: Uma chamada por documento
- **WHEN** `resumir(texto)` é executado
- **THEN** exatamente uma chamada a `LLMPort.complete` DEVE ser realizada

### Requirement: Limites de caracteres

O serviço DEVE garantir que `short_summary` não ultrapasse 280 caracteres e que `long_summary` não ultrapasse 1500 caracteres, truncando o resultado quando necessário. O truncamento DEVE ser feito em **fronteira de frase** e, na ausência dela, de **palavra**, de modo que o resumo NÃO termine no meio de uma palavra; somente quando não houver nenhuma fronteira dentro do teto é que o corte duro é aceitável.

#### Scenario: Resumo curto excedente
- **WHEN** a resposta da LLM para o resumo curto tem mais de 280 caracteres
- **THEN** `short_summary` DEVE ser truncado para, no máximo, 280 caracteres, terminando em fim de frase ou palavra

#### Scenario: Resumo longo excedente
- **WHEN** a resposta da LLM para o resumo longo tem mais de 1500 caracteres
- **THEN** `long_summary` DEVE ser truncado para, no máximo, 1500 caracteres, terminando em fim de frase ou palavra

#### Scenario: Sem fronteira no trecho
- **WHEN** não há fim de frase nem espaço dentro do teto
- **THEN** o texto DEVE ser truncado no teto como último recurso

## ADDED Requirements

### Requirement: Regeneração de resumos truncados

Resumos já persistidos que não terminam em pontuação final (corte no meio da palavra/frase) DEVEM ser considerados desatualizados e regerados pelo lote "Resumir pendentes", sem exigir limpeza manual do cache; resumos que terminam em pontuação final NÃO DEVEM ser regerados.

#### Scenario: Resumo truncado é regerado
- **WHEN** o lote processa um documento cujo resumo persistido termina no meio de uma palavra
- **THEN** o resumo DEVE ser refeito e regravado

#### Scenario: Resumo íntegro não é regerado
- **WHEN** o resumo persistido termina em pontuação final
- **THEN** ele NÃO DEVE ser refeito
