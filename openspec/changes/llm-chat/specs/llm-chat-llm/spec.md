## ADDED Requirements

### Requirement: Consumo do LLMPort do llm-core

O sistema DEVE consumir a porta `LLMPort` e a factory `create_llm_provider` fornecidas pela change `llm-core` para enviar o prompt RAG, sem definir cliente, protocolo ou factory de LLM próprios. A configuração de completion DEVE vir do bloco `llm.chat` gerenciado pela `llm-core`.

#### Scenario: Consulta usa o LLMPort
- **WHEN** o `ConsultarDocumentosUseCase` envia o prompt RAG
- **THEN** a chamada DEVE usar um `LLMPort` criado por `create_llm_provider` a partir de `llm.chat`

#### Scenario: LLM indisponível
- **WHEN** o provedor é `none` ou as dependências `[llm]` estão ausentes
- **THEN** o caso de uso DEVE propagar `LLMUnavailableError` para a GUI exibir o estado não configurado

### Requirement: Construção de prompt RAG

O sistema DEVE construir o prompt RAG combinando um `system_prompt` fixo com os chunks recuperados como contexto e a pergunta do usuário. O system_prompt DEVE instruir o LLM a responder apenas com base nos documentos e citar fontes.

#### Scenario: Prompt com contexto e pergunta
- **WHEN** o prompt é construído com 3 chunks e a pergunta "Qual o último rendimento?"
- **THEN** o prompt final DEVE conter: instruções do sistema, os 3 chunks formatados com fonte e data, e a pergunta do usuário
