## Purpose

Orquestra a cascata de recuperação sobre a porta `LLMPort` da `llm-core`, mantendo o número de chamadas baixo e tratando a resposta do modelo de forma tolerante.

## ADDED Requirements

### Requirement: Consumo do LLMPort do llm-core

O sistema DEVE consumir a porta `LLMPort`, a factory `create_llm_provider` e `load_llm_config` fornecidas pela change `llm-core`, sem definir cliente, porta ou factory de LLM próprios. A configuração de completion DEVE vir do bloco `llm.chat`.

#### Scenario: Consulta usa o LLMPort
- **WHEN** o caso de uso do chat envia um prompt
- **THEN** a chamada DEVE usar um `LLMPort` criado por `create_llm_provider` a partir de `llm.chat`

#### Scenario: LLM indisponível
- **WHEN** o provedor é `none` ou as dependências `[llm]` estão ausentes
- **THEN** o sistema DEVE propagar `LLMUnavailableError` para a GUI exibir o estado não configurado

### Requirement: Orquestração da cascata em até duas chamadas

O sistema DEVE resolver cada pergunta em no máximo duas chamadas de completion: a primeira com os resumos curtos e longos do escopo; a segunda, quando necessária, com o texto integral dos documentos-alvo. Quando a primeira chamada já responder, a segunda NÃO DEVE ocorrer.

#### Scenario: Resposta nos resumos
- **WHEN** a primeira chamada devolve uma resposta suficiente
- **THEN** apenas uma chamada de completion DEVE ter sido feita

#### Scenario: Necessidade do texto integral
- **WHEN** a primeira chamada devolve documentos-alvo sem resposta conclusiva
- **THEN** uma segunda chamada DEVE ler o texto integral desses alvos

### Requirement: Contrato de resposta estruturada tolerante

O sistema DEVE solicitar à LLM uma resposta em formato delimitado/JSON contendo a resposta e a lista de chaves de documentos-alvo, e DEVE interpretar a saída de forma tolerante: quando o formato não for reconhecido, a resposta inteira DEVE ser tratada como texto.

#### Scenario: Formato reconhecido
- **WHEN** a LLM responde no formato delimitado com resposta e lista de documentos
- **THEN** o sistema DEVE extrair a resposta e os documentos-alvo

#### Scenario: Formato não reconhecido
- **WHEN** a resposta não segue o formato esperado
- **THEN** o texto inteiro DEVE ser tratado como resposta, sem nova rodada

### Requirement: Prompt de sistema

O prompt DEVE instruir a LLM a responder apenas com base no contexto fornecido, a citar as fontes usadas, a identificar o ticker referido na pergunta e a admitir quando não houver informação suficiente.

#### Scenario: Instruções no prompt
- **WHEN** o prompt é construído
- **THEN** ele DEVE conter as instruções de restringir-se ao contexto, citar fontes, identificar o ticker e admitir insuficiência
