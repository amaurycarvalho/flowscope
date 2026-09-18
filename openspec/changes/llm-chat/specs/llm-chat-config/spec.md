## ADDED Requirements

### Requirement: Persistência da configuração de embedding

O sistema DEVE persistir a configuração de embedding no sub-bloco `llm.embedding` de `~/.flowscope/config.json`, contendo `provider`, `model`, `api_key` e `custom_base_url` opcional. A configuração de completion (`llm.chat`) é propriedade da change `llm-core` e NÃO DEVE ser redefinida aqui. O arquivo DEVE ser carregado na inicialização da GUI.

#### Scenario: Config de embedding completa
- **WHEN** config.json contém `{"llm": {"embedding": {"provider": "fastembed", "model": "BAAI/bge-small-pt-v1.5"}, "chat": {"provider": "openai", "model": "gpt-4o-mini", "api_key": "sk-..."}}}`
- **THEN** a leitura da configuração de embedding DEVE retornar o provedor e o modelo configurados

#### Scenario: Config ausente (primeira execução)
- **WHEN** config.json não contém o bloco `llm.embedding`
- **THEN** a leitura DEVE retornar o provedor padrão `fastembed`

### Requirement: Detecção de dependências [llm]

O sistema DEVE estender a detecção de dependências `[llm]` da `llm-core` para também exigir `fastembed`, exibindo mensagem amigável na GUI se ausente: "Instale flowscope[llm] para habilitar o chat: pip install flowscope[llm]". No CLI, DEVE exibir a mesma mensagem e encerrar com código 1.

#### Scenario: Dependências ausentes na GUI
- **WHEN** a GUI inicia e `fastembed` não pode ser importado
- **THEN** as abas de chat DEVEM exibir mensagem de instalação em vez do ChatPanel

#### Scenario: Dependências ausentes no CLI
- **WHEN** `flowscope --index ALZR11` é executado sem `[llm]` instalado
- **THEN** o sistema DEVE imprimir "Erro: flowscope[llm] não instalado. Execute: pip install flowscope[llm]" e encerrar com código 1

### Requirement: Presets de embedding

O sistema DEVE fornecer presets pré-configurados para os provedores de embedding suportados:

| Provedor | Embedding Model |
|---|---|
| fastembed (local, default) | BAAI/bge-small-pt-v1.5 |
| OpenAI | text-embedding-3-small |
| Gemini | text-embedding-004 |
| Custom | definido pelo usuário |

#### Scenario: Preset OpenAI
- **WHEN** o preset "OpenAI" é selecionado para embedding
- **THEN** o modelo DEVE ser "text-embedding-3-small"

#### Scenario: Preset local
- **WHEN** nenhum preset de embedding é configurado
- **THEN** o provedor DEVE ser `fastembed` com o modelo `BAAI/bge-small-pt-v1.5`
