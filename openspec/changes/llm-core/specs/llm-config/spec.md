## Purpose

Define como a configuração do LLM é persistida e lida a partir do `config.json` existente, como as dependências opcionais `[llm]` são detectadas e como os presets de provedores são expostos para a GUI e para os consumidores.

## ADDED Requirements

### Requirement: Persistência do bloco `llm.chat`

O sistema DEVE persistir a configuração de completion no bloco `llm.chat` de `~/.flowscope/config.json`, contendo `provider`, `api_url`, `model`, `api_key` e `rpm`. A gravação DEVE preservar as demais chaves do arquivo (preferências da GUI e outros sub-blocos de `llm`, como `embedding`). A leitura DEVE preencher os campos ausentes com os valores padrão.

#### Scenario: Config completa
- **WHEN** `config.json` contém `{"llm": {"chat": {"provider": "deepseek", "api_url": "https://api.deepseek.com/v1", "model": "deepseek-chat", "api_key": "sk-...", "rpm": 5}}}`
- **THEN** a leitura DEVE retornar o provedor, a API URL, o modelo, a chave e o RPM configurados

#### Scenario: Config ausente
- **WHEN** `config.json` não contém o bloco `llm.chat`
- **THEN** a leitura DEVE retornar os valores padrão, com `provider` igual a `none`

#### Scenario: Gravação preserva outras chaves
- **WHEN** o `config.json` contém preferências da GUI e o bloco `llm.embedding`, e a configuração de `llm.chat` é salva
- **THEN** as preferências da GUI e o bloco `llm.embedding` DEVEM permanecer intactos

### Requirement: Provedor padrão `none`

O sistema DEVE usar `none` como provedor padrão do LLM. Enquanto o provedor for `none`, nenhuma chamada de rede DEVE ser realizada e o LLM DEVE ser considerado indisponível.

#### Scenario: Primeira execução
- **WHEN** o FlowScope inicia sem configuração de LLM
- **THEN** o provedor DEVE ser `none` e nenhuma chamada LLM DEVE ser disparada

#### Scenario: Configuração explícita de none
- **WHEN** a configuração define `provider: "none"`
- **THEN** o LLM DEVE permanecer indisponível e nenhuma chamada de rede DEVE ocorrer

### Requirement: Detecção das dependências `[llm]`

O sistema DEVE detectar se as dependências opcionais `[llm]` (notadamente `litellm`) estão instaladas e oferecer uma verificação booleana reutilizável. Quando ausentes, a GUI DEVE exibir a mensagem `Instale flowscope[llm] para habilitar o LLM: pip install flowscope[llm]`.

#### Scenario: Dependências instaladas
- **WHEN** o `litellm` pode ser importado
- **THEN** a verificação DEVE retornar verdadeiro

#### Scenario: Dependências ausentes na GUI
- **WHEN** o `litellm` não pode ser importado e o diálogo de configuração é aberto
- **THEN** o diálogo DEVE exibir a mensagem de instalação com `pip install flowscope[llm]` e desabilitar a configuração e o teste

### Requirement: Presets de configuração de provedores

O sistema DEVE expor os presets de provedores suportados (`none`, `openai`, `gemini`, `copilot`, `claude`, `deepseek`, `ollama` e `custom`), cada um com seu modelo e API URL padrão, para uso pelo diálogo de configuração. Selecionar um preset DEVE preencher o modelo e a API URL correspondentes, que permanecem editáveis.

#### Scenario: Preset selecionado preenche modelo e URL
- **WHEN** o usuário seleciona o preset `deepseek`
- **THEN** o modelo DEVE ser preenchido com `deepseek-chat` e a API URL com `https://api.deepseek.com/v1`

#### Scenario: Preset custom
- **WHEN** o usuário seleciona o preset `custom`
- **THEN** o modelo e a API URL DEVEM ficar em branco para preenchimento manual
