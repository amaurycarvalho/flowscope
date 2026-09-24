## Purpose

Persiste a configuração do provedor de embedding, detecta suas dependências e oferece presets de provedores suportados.

## ADDED Requirements

### Requirement: Persistência da configuração de embedding

O sistema DEVE persistir a configuração de embedding no sub-bloco `llm.embedding` de `~/.flowscope/config.json`, contendo `provider`, `model`, `api_key` e `custom_base_url` opcional, preservando as demais chaves do arquivo. O arquivo DEVE ser carregado na inicialização da GUI.

#### Scenario: Config de embedding completa
- **WHEN** config.json contém `{"llm": {"embedding": {"provider": "fastembed", "model": "BAAI/bge-small-pt-v1.5"}, "chat": {"provider": "openai"}}}`
- **THEN** a leitura da configuração de embedding DEVE retornar o provedor e o modelo configurados

#### Scenario: Config ausente (primeira execução)
- **WHEN** config.json não contém o bloco `llm.embedding`
- **THEN** a leitura DEVE retornar o provedor padrão `fastembed`

### Requirement: Detecção de dependências [llm]

O sistema DEVE estender a detecção de dependências `[llm]` da `llm-core` para também exigir `fastembed`, exibindo mensagem amigável na GUI e encerrando com código 1 no CLI quando ausente: "Instale flowscope[llm] para habilitar o chat: pip install flowscope[llm]".

#### Scenario: Dependências ausentes na GUI
- **WHEN** a GUI inicia e `fastembed` não pode ser importado
- **THEN** a indexação DEVE exibir a mensagem de instalação em vez de falhar

#### Scenario: Dependências ausentes no CLI
- **WHEN** `flowscope --index ALZR11` é executado sem `[llm]` instalado
- **THEN** o sistema DEVE imprimir a mensagem de instalação e encerrar com código 1

### Requirement: Presets de embedding

O sistema DEVE fornecer presets para os provedores de embedding suportados: `fastembed` (local, default, `BAAI/bge-small-pt-v1.5`), OpenAI (`text-embedding-3-small`), Gemini (`text-embedding-004`) e Custom.

#### Scenario: Preset OpenAI
- **WHEN** o preset "OpenAI" é selecionado para embedding
- **THEN** o modelo DEVE ser `text-embedding-3-small`

#### Scenario: Preset local
- **WHEN** nenhum preset de embedding é configurado
- **THEN** o provedor DEVE ser `fastembed` com o modelo `BAAI/bge-small-pt-v1.5`
