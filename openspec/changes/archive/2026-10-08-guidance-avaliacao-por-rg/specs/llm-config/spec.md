## MODIFIED Requirements

### Requirement: Persistência do bloco `llm.chat` sem `input_limitado`

O sistema DEVE persistir a configuração de completion no bloco `llm.chat` de `~/.flowscope/config.json`, contendo `provider` (a seleção ativa) e um mapa `providers` com uma entrada por provedor já configurado, cada uma com `api_url`, `model`, `api_key` e `rpm`. O campo `input_limitado` NÃO DEVE mais existir. A leitura DEVE ignorar silenciosamente o campo antigo `input_limitado`, sem falhar, e DEVE preencher os campos ausentes com os valores padrão. A gravação DEVE preservar as demais chaves do arquivo (preferências da GUI e outros sub-blocos de `llm`, como `embedding`). O bloco `llm.guidance` NÃO DEVE mais existir: um bloco legado DEVE ser ignorado silenciosamente e NÃO DEVE ser persistido na próxima gravação.

#### Scenario: Config completa
- **WHEN** `config.json` contém `{"llm": {"chat": {"provider": "deepseek", "providers": {"deepseek": {"api_url": "https://api.deepseek.com/v1", "model": "deepseek-chat", "api_key": "sk-...", "rpm": 5}}}}}`
- **THEN** a leitura DEVE retornar o provedor ativo `deepseek` com a API URL, o modelo, a chave e o RPM da entrada `providers.deepseek`

#### Scenario: Config ausente
- **WHEN** `config.json` não contém o bloco `llm.chat`
- **THEN** a leitura DEVE retornar os valores padrão, com `provider` igual a `none` e `providers` vazio

#### Scenario: Chave antiga ignorada
- **WHEN** uma entrada de provedor ainda contém `input_limitado`
- **THEN** a leitura DEVE ignorá-lo silenciosamente e a próxima gravação NÃO DEVE persisti-lo

#### Scenario: Gravação preserva outras chaves
- **WHEN** o `config.json` contém preferências da GUI e o bloco `llm.embedding`, e a configuração de `llm.chat` é salva
- **THEN** as preferências da GUI e o bloco `llm.embedding` DEVEM permanecer intactos

#### Scenario: Bloco legado `llm.guidance` ignorado
- **WHEN** o `config.json` ainda contém o bloco `llm.guidance` de versões anteriores
- **THEN** a leitura DEVE ignorá-lo silenciosamente e a próxima gravação NÃO DEVE persisti-lo
