## ADDED Requirements

### Requirement: ChatPort protocol
O sistema DEVE definir um protocolo `ChatPort` com método `chat(messages: list[dict], system_prompt: str) -> str` que envia histórico de mensagens e retorna a resposta do LLM como string.

#### Scenario: Chat com histórico
- **WHEN** `chat([{"role": "user", "content": "Olá"}], system_prompt="Seja conciso")` é chamado
- **THEN** a resposta do LLM DEVE ser retornada como string

### Requirement: LiteLLMChatAdapter
O sistema DEVE implementar `LiteLLMChatAdapter` usando `litellm.completion()`, aceitando `model` e `api_key` como parâmetros. O adaptador DEVE suportar presets para OpenAI, Claude, Gemini, DeepSeek, Copilot e OpenAI-compatible (custom base_url).

#### Scenario: Chat via OpenAI
- **WHEN** `LiteLLMChatAdapter(model="openai/gpt-4o", api_key="sk-...")` é usado
- **THEN** `litellm.completion()` DEVE ser chamado com o modelo e chave configurados

#### Scenario: Chat via DeepSeek com base_url customizada
- **WHEN** `LiteLLMChatAdapter(model="openai/deepseek-chat", api_key="sk-...", base_url="https://api.deepseek.com/v1")` é usado
- **THEN** a chamada DEVE usar a `base_url` customizada

#### Scenario: Erro de API tratado
- **WHEN** a chamada à API falha
- **THEN** uma exceção com mensagem descritiva incluindo o status HTTP DEVE ser lançada

### Requirement: Construção de prompt RAG
O sistema DEVE construir o prompt RAG combinando um `system_prompt` fixo com os chunks recuperados como contexto e a pergunta do usuário. O system_prompt DEVE instruir o LLM a responder apenas com base nos documentos e citar fontes.

#### Scenario: Prompt com contexto e pergunta
- **WHEN** o prompt é construído com 3 chunks e a pergunta "Qual o último rendimento?"
- **THEN** o prompt final DEVE conter: instruções do sistema, os 3 chunks formatados com fonte e data, e a pergunta do usuário

### Requirement: Factory de chat provider
O sistema DEVE fornecer `create_chat_provider(config: dict) -> ChatPort` que instancia `LiteLLMChatAdapter` com modelo e chave da configuração.

#### Scenario: Provider configurado
- **WHEN** config tem `{"provider": "openai", "model": "openai/gpt-4o", "api_key": "sk-..."}`
- **THEN** `LiteLLMChatAdapter` DEVE ser retornado com as credenciais corretas
