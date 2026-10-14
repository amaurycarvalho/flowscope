# documento-summary Specification

## Purpose

Produz, a partir do texto de um documento, dois resumos complementares — um curto (até 450 caracteres) e um longo (até 2000 caracteres) — usando a fórmula XYZ e consumindo a porta `LLMPort` fornecida pela change `llm-core`.

## Requirements

### Requirement: Serviço de resumo de documento

O sistema DEVE fornecer `ResumirDocumentoUseCase` com um método `resumir(texto: str) -> ResumoDocumento` que recebe o texto integral de um documento e retorna um `ResumoDocumento` com `short_summary` (até 450 caracteres) e `long_summary` (até 2000 caracteres). O serviço DEVE depender apenas da porta `LLMPort`, nunca do liteLLM diretamente.

#### Scenario: Resumo de um texto
- **WHEN** `resumir(texto)` é chamado com um texto não vazio
- **THEN** um `ResumoDocumento` DEVE ser retornado com os dois campos preenchidos

#### Scenario: Texto vazio
- **WHEN** `resumir("")` é chamado
- **THEN** o serviço NÃO DEVE chamar a LLM e DEVE retornar resumos vazios

### Requirement: Prefixo de sistema estável no resumo de documentos e notícias

O sistema DEVE enviar as instruções de resumo como um prefixo de sistema (`system_prompt`) constante e a mensagem de usuário DEVE conter apenas o texto do documento. O prefixo DEVE ser idêntico entre documentos e entre as sub-abas "Documentos" e "Notícias", de modo que o provedor possa reaproveitar o cache de prompt. O orçamento de entrada e o curto-circuito de texto vazio NÃO DEVEM mudar.

#### Scenario: Instruções no prefixo de sistema
- **WHEN** `resumir(texto)` é executado com texto não vazio
- **THEN** as instruções de resumo DEVEM ser enviadas em `system_prompt` e a mensagem `user` DEVE conter apenas o texto do documento

#### Scenario: Prefixo idêntico entre itens
- **WHEN** dois documentos distintos são resumidos
- **THEN** o `system_prompt` enviado DEVE ser idêntico nos dois casos

#### Scenario: Texto vazio mantém o curto-circuito
- **WHEN** `resumir("")` é chamado
- **THEN** nenhuma chamada à LLM DEVE ocorrer e resumos vazios DEVEM ser retornados

### Requirement: Fórmula XYZ no prompt

O sistema DEVE instruir a LLM, no prefixo de sistema, a resumir usando a fórmula XYZ — X: o que o texto diz; Y: por que isso importa; Z: o que se conclui — tanto para o resumo curto quanto para o longo, e DEVE solicitar os dois resumos em uma única chamada de completion. O prompt DEVE pedir o resumo curto em **1 a 2 frases** e o longo em **parágrafos** (não uma contagem exata de caracteres), declarando um orçamento de caracteres dimensionado para acomodar a fórmula XYZ: **400** para o curto e **1.800** para o longo, abaixo dos tetos de salvaguarda. O prompt DEVE orientar a planejar X, Y e Z para caber no orçamento, sem omitir a conclusão (Z). O prompt DEVE ainda exigir resposta sem markdown, listas, títulos ou comentários, sem nada antes de `CURTO:` nem depois do resumo longo, e que o conteúdo se baseie exclusivamente no documento fornecido.

#### Scenario: Prompt contém a fórmula e os orçamentos
- **WHEN** o prompt é montado para um documento
- **THEN** ele DEVE conter as instruções XYZ e os orçamentos de 400 caracteres para o resumo curto e 1800 para o longo

#### Scenario: Prompt pede frases, não uma contagem exata
- **WHEN** o prompt é montado
- **THEN** ele DEVE solicitar o curto em 1 a 2 frases e o longo em parágrafos, para reduzir o risco de corte no meio da frase

#### Scenario: Prompt orça o XYZ
- **WHEN** o prompt é montado
- **THEN** ele DEVE instruir a planejar X, Y e Z dentro do orçamento, sem cortar a conclusão (Z)

#### Scenario: Prompt restringe o formato e exige fidelidade
- **WHEN** o prefixo de sistema é montado
- **THEN** ele DEVE vetar markdown, listas, títulos e comentários, delimitar a saída por `CURTO:`/`LONGO:` e exigir que a resposta se baseie exclusivamente no documento

#### Scenario: Uma chamada por documento
- **WHEN** `resumir(texto)` é executado
- **THEN** exatamente uma chamada a `LLMPort.complete` DEVE ser realizada

### Requirement: Limites de caracteres

O serviço DEVE garantir que `short_summary` não ultrapasse 450 caracteres e que `long_summary` não ultrapasse 2000 caracteres, truncando o resultado quando necessário. O truncamento DEVE ser feito em **fronteira de frase** e, na ausência dela, de **palavra**, de modo que o resumo NÃO termine no meio de uma palavra; somente quando não houver nenhuma fronteira dentro do teto é que o corte duro é aceitável.

#### Scenario: Resumo curto excedente
- **WHEN** a resposta da LLM para o resumo curto tem mais de 450 caracteres
- **THEN** `short_summary` DEVE ser truncado para, no máximo, 450 caracteres, terminando em fim de frase ou palavra

#### Scenario: Resumo longo excedente
- **WHEN** a resposta da LLM para o resumo longo tem mais de 2000 caracteres
- **THEN** `long_summary` DEVE ser truncado para, no máximo, 2000 caracteres, terminando em fim de frase ou palavra

#### Scenario: Sem fronteira no trecho
- **WHEN** não há fim de frase nem espaço dentro do teto
- **THEN** o texto DEVE ser truncado no teto como último recurso

### Requirement: Regeneração de resumos truncados

Resumos já persistidos que não terminam em pontuação final (corte no meio da palavra/frase) DEVEM ser considerados desatualizados e regerados pelo lote "Resumir pendentes", sem exigir limpeza manual do cache; resumos que terminam em pontuação final NÃO DEVEM ser regerados.

#### Scenario: Resumo truncado é regerado
- **WHEN** o lote processa um documento cujo resumo persistido termina no meio de uma palavra
- **THEN** o resumo DEVE ser refeito e regravado

#### Scenario: Resumo íntegro não é regerado
- **WHEN** o resumo persistido termina em pontuação final
- **THEN** ele NÃO DEVE ser refeito

### Requirement: Limite de entrada

O serviço DEVE limitar o tamanho do texto enviado à LLM a um orçamento máximo de caracteres, truncando a entrada quando o documento for maior, para evitar exceder a janela de contexto do modelo.

#### Scenario: Documento muito longo
- **WHEN** o texto do documento excede o orçamento de entrada
- **THEN** apenas os primeiros caracteres até o orçamento DEVEM ser enviados à LLM

### Requirement: Propagação das exceções tipadas

O serviço DEVE propagar as exceções tipadas da `llm-core` (`LLMUnavailableError`, `LLMConfigurationError`, `LLMCommunicationError`, `LLMProviderError`, `LLMServiceUnavailableError`, `LLMRateLimitError`) para que o consumidor decida como exibir a falha.

#### Scenario: LLM indisponível
- **WHEN** a porta lança `LLMUnavailableError`
- **THEN** a exceção DEVE propagar para o consumidor sem ser convertida

#### Scenario: Falha de comunicação
- **WHEN** a porta lança `LLMCommunicationError`
- **THEN** a exceção DEVE propagar para o consumidor sem ser convertida

#### Scenario: Provedor temporariamente indisponível
- **WHEN** a porta lança `LLMServiceUnavailableError`
- **THEN** a exceção DEVE propagar para o consumidor sem ser convertida

### Requirement: Resiliência ao formato de resposta

O serviço DEVE interpretar a resposta da LLM em busca dos resumos curto e longo e, quando o formato esperado não for identificável, DEVE usar a resposta inteira como `long_summary` e os primeiros 450 caracteres como `short_summary`, sem falhar.

#### Scenario: Formato inesperado
- **WHEN** a resposta não contém os delimitadores esperados
- **THEN** o serviço DEVE preencher `long_summary` com a resposta e `short_summary` com seus primeiros 450 caracteres
