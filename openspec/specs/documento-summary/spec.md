# documento-summary Specification

## Purpose

Produz, a partir do texto de um documento, dois resumos complementares — um curto (até 280 caracteres) e um longo (até 1500 caracteres) — usando a fórmula XYZ e consumindo a porta `LLMPort` fornecida pela change `llm-core`.

## Requirements

### Requirement: Serviço de resumo de documento

O sistema DEVE fornecer `ResumirDocumentoUseCase` com um método `resumir(texto: str) -> ResumoDocumento` que recebe o texto integral de um documento e retorna um `ResumoDocumento` com `short_summary` (até 280 caracteres) e `long_summary` (até 1500 caracteres). O serviço DEVE depender apenas da porta `LLMPort`, nunca do liteLLM diretamente.

#### Scenario: Resumo de um texto
- **WHEN** `resumir(texto)` é chamado com um texto não vazio
- **THEN** um `ResumoDocumento` DEVE ser retornado com os dois campos preenchidos

#### Scenario: Texto vazio
- **WHEN** `resumir("")` é chamado
- **THEN** o serviço NÃO DEVE chamar a LLM e DEVE retornar resumos vazios

### Requirement: Fórmula XYZ no prompt

O serviço DEVE instruir a LLM a resumir usando a fórmula XYZ — X: o que o texto diz; Y: por que isso importa; Z: o que se conclui — tanto para o resumo curto quanto para o longo, e DEVE solicitar os dois resumos em uma única chamada de completion.

#### Scenario: Prompt contém a fórmula e os limites
- **WHEN** o prompt é montado para um documento
- **THEN** ele DEVE conter as instruções XYZ, o limite de 280 caracteres para o resumo curto e o limite de 1500 para o longo

#### Scenario: Uma chamada por documento
- **WHEN** `resumir(texto)` é executado
- **THEN** exatamente uma chamada a `LLMPort.complete` DEVE ser realizada

### Requirement: Limites de caracteres

O serviço DEVE garantir que `short_summary` não ultrapasse 280 caracteres e que `long_summary` não ultrapasse 1500 caracteres, truncando o resultado quando necessário.

#### Scenario: Resumo curto excedente
- **WHEN** a resposta da LLM para o resumo curto tem mais de 280 caracteres
- **THEN** `short_summary` DEVE ser truncado para 280 caracteres

#### Scenario: Resumo longo excedente
- **WHEN** a resposta da LLM para o resumo longo tem mais de 1500 caracteres
- **THEN** `long_summary` DEVE ser truncado para 1500 caracteres

### Requirement: Limite de entrada

O serviço DEVE limitar o tamanho do texto enviado à LLM a um orçamento máximo de caracteres, truncando a entrada quando o documento for maior, para evitar exceder a janela de contexto do modelo.

#### Scenario: Documento muito longo
- **WHEN** o texto do documento excede o orçamento de entrada
- **THEN** apenas os primeiros caracteres até o orçamento DEVEM ser enviados à LLM

### Requirement: Propagação das exceções tipadas

O serviço DEVE propagar as exceções tipadas da `llm-core` (`LLMUnavailableError`, `LLMConfigurationError`, `LLMCommunicationError`, `LLMProviderError`, `LLMRateLimitError`) para que o consumidor decida como exibir a falha.

#### Scenario: LLM indisponível
- **WHEN** a porta lança `LLMUnavailableError`
- **THEN** a exceção DEVE propagar para o consumidor sem ser convertida

#### Scenario: Falha de comunicação
- **WHEN** a porta lança `LLMCommunicationError`
- **THEN** a exceção DEVE propagar para o consumidor sem ser convertida

### Requirement: Resiliência ao formato de resposta

O serviço DEVE interpretar a resposta da LLM em busca dos resumos curto e longo e, quando o formato esperado não for identificável, DEVE usar a resposta inteira como `long_summary` e os primeiros 280 caracteres como `short_summary`, sem falhar.

#### Scenario: Formato inesperado
- **WHEN** a resposta não contém os delimitadores esperados
- **THEN** o serviço DEVE preencher `long_summary` com a resposta e `short_summary` com seus primeiros 280 caracteres
