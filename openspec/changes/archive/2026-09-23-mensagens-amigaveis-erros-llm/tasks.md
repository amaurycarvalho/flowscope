## 1. Domínio e adaptador

- [x] 1.1 Adicionar `LLMServiceUnavailableError(LLMError)` em `src/flowscope/domain/llm/exceptions.py` e exportá-la em `src/flowscope/domain/llm/__init__.py`; verificar com `pytest tests/test_domain/test_llm/test_exceptions.py`
- [x] 1.2 Mapear `ServiceUnavailableError` e `InternalServerError` do liteLLM para `LLMServiceUnavailableError` em `_MAPEAMENTO_EXCECOES`, antes de `APIError`, sem alterar `str(exc)`; verificar com casos novos em `tests/test_infrastructure/test_llm/test_adapter.py` (503->novo tipo; autenticação e requisição inválida seguem `LLMProviderError`)

## 2. Helper de apresentação

- [x] 2.1 Criar `src/flowscope/presentation/gui/llm/mensagens.py` com `mensagem_erro_llm(exc: BaseException) -> str`, mapeando por subtipo de `LLMError` conforme a tabela do `design.md` e preservando `str(exc)` para `LLMUnavailableError` e exceções não-LLM; verificar com testes unitários dos cinco casos de LLM e do fallback
- [x] 2.2 Criar `tests/test_presentation/test_llm_mensagens.py` cobrindo cada mensagem da tabela e o fallback não-LLM; verificar com `pytest tests/test_presentation/test_llm_mensagens.py`

## 3. Aplicação nas telas

- [x] 3.1 Usar `mensagem_erro_llm` em `_interromper_resumos()` (`app_resumos_actions.py`) mantendo `logger.error(..., exc, exc_info=exc)` inalterado; verificar que a barra de status exibe `{arquivo.nome}: <mensagem amigável>` em teste de apresentação
- [x] 3.2 Usar `mensagem_erro_llm` no desfecho do teste (`config_dialog.py::_verificar_teste`) mantendo `_registrar_falha` inalterado; atualizar `tests/test_presentation/test_llm_config_dialog.py::test_falhas_exibem_motivo` para o texto amigável e manter `test_falha_registra_log_sem_chave`; verificar com `pytest tests/test_presentation/test_llm_config_dialog.py`

## 4. Verificação final

- [x] 4.1 Rodar a suíte completa com `make test` (cobertura mínima de 85%) e corrigir regressões
- [x] 4.2 Rodar `make lint` e corrigir apontamentos de ruff/flake8

## 5. Silenciar o banner de depuração do liteLLM

- [x] 5.1 Ligar `litellm.suppress_debug_info = True` em `_import_litellm()` (`adapter.py`) e verificar com teste que o módulo retorna com o flag ligado e que a saída padrão não contém `Give Feedback` nem `LiteLLM.Info`
- [x] 5.2 Rodar `make test` e `make lint` após a mudança e corrigir regressões
