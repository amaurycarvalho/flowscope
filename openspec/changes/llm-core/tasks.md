## 1. Setup e Dependências

- [x] 1.1 Adicionar o grupo opcional `[llm]` com `litellm>=1.50` ao `pyproject.toml` e verificar com `pip install -e ".[llm]"` que a instalação conclui
- [x] 1.2 Adicionar o marcador `llm` em `[tool.pytest.ini_options].markers` e verificar que `pytest --markers` o lista
- [x] 1.3 Criar a estrutura de pacotes `domain/llm/`, `infrastructure/llm/` e `presentation/gui/llm/` com `__init__.py` e verificar que os pacotes importam

## 2. Domínio — Exceções e Porta

- [x] 2.1 Implementar `domain/llm/exceptions.py` com `LLMError`, `LLMUnavailableError`, `LLMConfigurationError`, `LLMCommunicationError`, `LLMProviderError` e `LLMRateLimitError`, verificando com testes unitários a hierarquia de herança
- [x] 2.2 Implementar `domain/llm/ports.py` com o protocolo `LLMPort.complete(messages, system_prompt=None) -> str` e verificar a assinatura com um teste de protocolo/mock
- [x] 2.3 Exportar a porta e as exceções em `domain/llm/__init__.py` e verificar o import público

## 3. Infraestrutura — Presets e Configuração

- [x] 3.1 Implementar `infrastructure/llm/presets.py` com `PROVIDER_PRESETS` (`none`, `openai`, `gemini`, `copilot`, `claude`, `deepseek`, `ollama`, `custom`) e a resolução de `api_url`/`model`, verificando com testes os defaults de cada preset e a rejeição de provedor desconhecido
- [x] 3.2 Implementar `infrastructure/llm/config.py` com `load_llm_config`, `save_llm_config`, `get_presets` e `check_llm_deps`, verificando com testes o default `provider: "none"`, a leitura parcial e a preservação de outras chaves do `config.json` no read-modify-write
- [x] 3.3 Implementar `check_llm_deps` usando detecção de importação e verificar com mock que retorna falso quando `litellm` está ausente

## 4. Infraestrutura — Rate Limiter e Adaptador

- [x] 4.1 Implementar `infrastructure/llm/rate_limiter.py` com `RateLimiter(rpm)` de janela deslizante, thread-safe e com relógio injetável, verificando com testes que o excedente aguarda e que o RPM padrão é 5
- [x] 4.2 Implementar `infrastructure/llm/adapter.py` (`LiteLLMChatAdapter`) usando `litellm.completion` com `api_base`, `custom_llm_provider="openai"` e `api_key`, verificando com mock que os argumentos corretos são enviados
- [x] 4.3 Mapear as exceções do liteLLM para a hierarquia de domínio no adaptador e verificar com testes os casos de timeout, cota (429), autenticação/erro de API e ImportError
- [x] 4.4 Integrar o `RateLimiter` ao adaptador de forma que toda chamada de completion passe pelo throttle e verificar com teste de relógio falso que as chamadas são desaceleradas
- [x] 4.5 Implementar `infrastructure/llm/factory.py` com `create_llm_provider(config)` e verificar com testes os casos: provider configurado, `none` → `LLMUnavailableError`, deps ausentes → `LLMUnavailableError` e `custom` incompleto → `LLMConfigurationError`

## 5. GUI — Diálogo de Configuração

- [x] 5.1 Implementar `presentation/gui/llm/config_dialog.py` (`LLMConfigDialog`) com seletor de presets, `api_url`, `model`, chave mascarada, RPM e botões Salvar/Cancelar, verificando com testes de GUI a carga da configuração salva e a persistência ao salvar
- [x] 5.2 Implementar o botão "Testar" executando a completion `hello` em thread de trabalho com publicação por fila e verificar com mock os desfechos: sucesso, indisponível, comunicação, provedor e configuração inválida
- [x] 5.3 Desabilitar o botão "Testar" durante a execução e verificar que um segundo acionamento não inicia novo teste
- [x] 5.4 Tratar dependências `[llm]` ausentes no diálogo, exibindo a mensagem `pip install flowscope[llm]` e desabilitando configuração/teste, verificado por teste de GUI

## 6. GUI — Botão "I.A." na Sub-aba Documentos

- [x] 6.1 Adicionar o botão "I.A." ao `DocumentTreePanel` imediatamente após "Abrir documento", com callback opcional, e verificar com testes que ele aparece na ordem correta e permanece habilitado sem documentos
- [x] 6.2 Injetar o callback de abertura do diálogo em `app_tab_layout.py` e verificar com teste que o acionamento abre o `LLMConfigDialog`

## 7. Documentação

- [x] 7.1 Adicionar ao `README.md` a seção de LLM com `pip install flowscope[llm]` e a menção ao botão "I.A." na sub-aba Documentos, verificando a presença do comando no texto

## 8. Quality Gate

- [x] 8.1 Executar `make lint` e garantir que não há erros de linting no código novo
- [x] 8.2 Executar `pytest -m "not llm"` e garantir que a suíte base passa sem regressão
- [x] 8.3 Executar `pytest -m "llm"` e garantir que os testes marcados passam
- [x] 8.4 Executar `openspec validate llm-core` e garantir que a change permanece válida
