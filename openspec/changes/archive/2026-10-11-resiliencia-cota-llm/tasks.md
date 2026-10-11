## 1. Interrupção do lote por cota esgotada

- [x] 1.1 Fazer `_resumir` abortar em `LLMRateLimitError` (publicar o erro e retornar) independentemente de `continuar_em_erro`; verificar com teste headless em `tests/test_presentation/test_resumos_job.py` (lote contínuo para de processar os itens seguintes).
- [x] 1.2 Marcar a interrupção por cota no host e emitir um desfecho único, suprimindo a mensagem normal; verificar com testes em `tests/test_presentation/test_app_resumos_actions.py`.

## 2. Registro conciso e mensagem

- [x] 2.1 Registrar a cota uma única vez (warning, sem traceback) em `_interromper_resumos`; verificar com `caplog` que não há registro de exceção por item.
- [x] 2.2 Ajustar `mensagem_erro_llm` para `LLMRateLimitError`, mencionando aguardar a renovação ou reconfigurar o provedor; verificar com testes de mensagens.

## 3. Verificação integrada

- [x] 3.1 Rodar `pytest` (marker padrão) e confirmar que a suíte passa.
- [x] 3.2 Rodar a verificação das specs: `openspec validate resiliencia-cota-llm`.
- [x] 3.3 Rodar `make complexity` e o lint para confirmar os gates.
