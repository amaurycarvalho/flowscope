## Why

O FlowScope vai consumir LLMs (resumo de documentos, chat RAG), mas ainda não existe uma camada base de LLM: configuração de provedores, cliente via liteLLM, controle de cota (RPM) e tratamento explícito de erros. Sem essa base, cada change de consumo reimplementaria configuração e chamadas, e chamadas rápidas em sequência estourariam a cota do provedor, gerando erros, retries e tokens desperdiçados.

Esta change é a fundação reutilizável de LLM: expõe uma porta genérica de completion, presets de provedores, persistência no `config.json`, rate limiting configurável e exceções tipadas que os consumidores usam para decidir. A change `llm-chat` passa a herdá-la, e uma change futura de resumo de documentos consumirá a mesma porta.

## What Changes

- Novo grupo opcional `[llm]` em `pyproject.toml` com `litellm` (`pip install flowscope[llm]`).
- Novo domínio `domain/llm/`: porta genérica `LLMPort` (completion) e hierarquia de exceções (`LLMUnavailableError`, `LLMConfigurationError`, `LLMCommunicationError`, `LLMProviderError`, `LLMRateLimitError`).
- Nova infraestrutura `infrastructure/llm/`: presets de provedores (`none`, `openai`, `gemini`, `copilot`, `claude`, `deepseek`, `ollama`, `custom`), adaptador `LiteLLMChatAdapter` via `litellm.completion()` com `custom_llm_provider`, rate limiter configurável (RPM, default 5), load/save de config, detecção das dependências `[llm]` e factory `create_llm_provider(config)`.
- Bloco `llm.chat` no `~/.flowscope/config.json` com `provider` (default `none`), `api_url`, `model`, `api_key` e `rpm`, preservando as demais preferências do arquivo.
- Diálogo de configuração de LLM na GUI (modal e não redimensionável) com dropdown de presets, `api_url`, `model`, chave de API mascarada, RPM, botão "Salvar" e botão "Testar" — este envia um texto `hello` pela porta `LLMPort` e exibe sucesso ou o motivo da falha.
- Botão "I.A." na barra da sub-aba "Documentos" (logo após "Abrir documento") que abre o diálogo de configuração e segue o bloqueio global dos demais botões durante as cargas de dados.
- README com a seção de instalação `pip install flowscope[llm]`.
- Adaptação da change `llm-chat` para herdar `llm-core` (remove a duplicação de cliente de chat, config e diálogo, mantendo embeddings, VectorStore, RAG e o ChatPanel).

## Capabilities

### New Capabilities

- `llm-provider`: porta `LLMPort`, adaptador liteLLM, presets de provedores, rate limiter com RPM configurável, exceções tipadas e factory.
- `llm-config`: persistência do bloco `llm.chat` no `config.json`, default `none`, detecção das dependências `[llm]` e presets de configuração.
- `llm-gui`: diálogo de configuração de provedores LLM com presets, chave de API e botão "Testar".

### Modified Capabilities

- `documentos-ticker-panel`: a barra da sub-aba "Documentos" passa a incluir o botão "I.A." logo após "Abrir documento".

## Impact

- **Dependências**: `[llm] = ["litellm>=1.50"]`; `pypdf>=4` já é dependência base; `fastembed` permanece como extensão de `[llm]` introduzida pela `llm-chat`.
- **Config**: novo bloco `llm.chat` em `~/.flowscope/config.json`; ausência ou `provider: "none"` indica LLM indisponível.
- **GUI**: novo diálogo de configuração e novo botão na sub-aba "Documentos".
- **Changes relacionadas**: `llm-chat` passa a depender de `llm-core`; a futura change de resumo de documentos consumirá `LLMPort`.
- **Sem rede por padrão**: nenhuma chamada LLM ocorre enquanto o provedor for `none`.
