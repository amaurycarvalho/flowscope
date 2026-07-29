## ADDED Requirements

### Requirement: Persistência de configuração LLM
O sistema DEVE estender `~/.flowscope/config.json` com bloco `llm` contendo sub-blocos `embedding` e `chat`, cada um com `provider`, `model`, `api_key` e `custom_base_url` opcional. O arquivo DEVE ser carregado na inicialização da GUI.

#### Scenario: Config completa
- **WHEN** config.json contém `{"llm": {"embedding": {"provider": "fastembed", "model": "BAAI/bge-small-pt-v1.5"}, "chat": {"provider": "openai", "model": "openai/gpt-4o", "api_key": "sk-..."}}}`
- **THEN** `load_llm_config()` DEVE retornar dicionário com os dois sub-blocos

#### Scenario: Config ausente (primeira execução)
- **WHEN** config.json não contém bloco `llm`
- **THEN** `load_llm_config()` DEVE retornar `None` para `chat.provider`, indicando que o chat não está configurado

### Requirement: Detecção de dependências [llm]
O sistema DEVE detectar se as dependências opcionais `[llm]` estão instaladas (`litellm`, `fastembed`, `PyPDF2`) e exibir mensagem amigável na GUI se ausentes: "Instale flowscope[llm] para habilitar o chat: pip install flowscope[llm]". No CLI, DEVE exibir a mesma mensagem e encerrar com código 1.

#### Scenario: Dependências ausentes na GUI
- **WHEN** a GUI inicia e `litellm` não pode ser importado
- **THEN** as abas de chat DEVEM exibir mensagem de instalação em vez do ChatPanel

#### Scenario: Dependências ausentes no CLI
- **WHEN** `flowscope --fii-index ALZR11` é executado sem `[llm]` instalado
- **THEN** o sistema DEVE imprimir "Erro: flowscope[llm] não instalado. Execute: pip install flowscope[llm]" e encerrar com código 1

### Requirement: Presets de provedores
O sistema DEVE fornecer presets pré-configurados para os provedores suportados:

| Provedor | Chat Model | Embedding Model |
|---|---|---|
| OpenAI | openai/gpt-4o | openai/text-embedding-3-small |
| Claude | claude-3-5-sonnet-latest | openai/text-embedding-3-small (fallback) |
| Gemini | gemini/gemini-2.0-flash | gemini/text-embedding-004 |
| DeepSeek | openai/deepseek-chat | openai/text-embedding-3-small (fallback) |
| Copilot | github/copilot-chat | openai/text-embedding-3-small (fallback) |
| Custom | openai/<user-specified> | openai/<user-specified> |

#### Scenario: Preset OpenAI
- **WHEN** preset "OpenAI" é selecionado
- **THEN** chat_model DEVE ser "openai/gpt-4o" e embedding_model DEVE ser "openai/text-embedding-3-small"

#### Scenario: Preset Claude usa fallback embedding
- **WHEN** preset "Claude" é selecionado
- **THEN** chat_model DEVE ser "claude-3-5-sonnet-latest" e embedding DEVE usar OpenAI como fallback
