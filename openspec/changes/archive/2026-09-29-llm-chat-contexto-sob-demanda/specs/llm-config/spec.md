## MODIFIED Requirements

### Requirement: Persistência do bloco `llm.chat`

O sistema DEVE persistir a configuração de completion no bloco `llm.chat` de `~/.flowscope/config.json`, contendo `provider` (a seleção ativa) e um mapa `providers` com uma entrada por provedor já configurado, cada uma com `api_url`, `model`, `api_key`, `rpm` e `input_limitado`. O campo `input_limitado` é booleano e indica que o modelo tem janela de entrada limitada, com valor padrão `false`. A gravação DEVE preservar as demais chaves do arquivo (preferências da GUI e outros sub-blocos de `llm`, como `embedding` e `guidance`). A leitura DEVE preencher os campos ausentes com os valores padrão.

#### Scenario: Config completa
- **WHEN** `config.json` contém `{"llm": {"chat": {"provider": "deepseek", "providers": {"deepseek": {"api_url": "https://api.deepseek.com/v1", "model": "deepseek-chat", "api_key": "sk-...", "rpm": 5, "input_limitado": true}}}}}`
- **THEN** a leitura DEVE retornar o provedor ativo `deepseek` com a API URL, o modelo, a chave, o RPM e `input_limitado` da entrada `providers.deepseek`

#### Scenario: Config ausente
- **WHEN** `config.json` não contém o bloco `llm.chat`
- **THEN** a leitura DEVE retornar os valores padrão, com `provider` igual a `none`, `providers` vazio e `input_limitado` igual a `false`

#### Scenario: Config sem input_limitado usa default false
- **WHEN** uma entrada de provedor não contém `input_limitado`
- **THEN** a leitura DEVE assumir `false` para esse provedor

#### Scenario: Gravação preserva outras chaves
- **WHEN** o `config.json` contém preferências da GUI, o bloco `llm.embedding` e o bloco `llm.guidance`, e a configuração de `llm.chat` é salva
- **THEN** as preferências da GUI, o bloco `llm.embedding` e o bloco `llm.guidance` DEVEM permanecer intactos

### Requirement: Memória de configuração por provedor

O sistema DEVE manter a configuração de cada provedor de forma independente no mapa `llm.chat.providers`. Trocar a seleção ativa NÃO DEVE alterar nem remover as entradas dos demais provedores. Ao selecionar um provedor com configuração salva, o sistema DEVE restaurar a `api_url`, o `model`, a `api_key`, o `rpm` e o `input_limitado` salvos para ele. Ao selecionar um provedor sem configuração salva, o sistema DEVE usar o `model` e a `api_url` do preset, DEVE iniciar com `api_key` vazia e `input_limitado` desligado, sem herdar a chave de outro provedor. O provedor `none` DEVE limpar os campos ativos sem remover as entradas de `providers`.

#### Scenario: Troca restaura a configuração salva
- **WHEN** `providers` contém entradas para `deepseek` e `openai` e o provedor ativo passa de `openai` para `deepseek`
- **THEN** a `api_url`, o `model`, a `api_key`, o `rpm` e o `input_limitado` salvos de `deepseek` DEVEM ser restaurados

#### Scenario: Provedor sem configuração salva
- **WHEN** o provedor ativo passa para um provedor sem entrada em `providers`
- **THEN** o `model` e a `api_url` DEVEM ser os defaults do preset, a `api_key` DEVE ser vazia e o `input_limitado` DEVE ficar desligado

#### Scenario: Seleção de none preserva os demais provedores
- **WHEN** o provedor ativo passa para `none`
- **THEN** os campos ativos DEVEM ser limpos e as entradas de `providers` DEVEM permanecer inalteradas

#### Scenario: Retorno a um provedor configurado anteriormente
- **WHEN** o provedor ativo foi definido como `none` e depois volta para um provedor presente em `providers`
- **THEN** a configuração salva desse provedor, incluindo `input_limitado`, DEVE ser restaurada automaticamente
