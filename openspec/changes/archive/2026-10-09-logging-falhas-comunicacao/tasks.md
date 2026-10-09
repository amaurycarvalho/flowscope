## 1. Formatter de logging

- [x] 1.1 Adicionar `_CommunicationAwareFormatter` e o auxiliar de detecção de causa de comunicação em `presentation/main.py`, com docstrings e anotações, e usá-lo em `_configure_logging`
- [x] 1.2 Anexar `[Tipo: mensagem]` à linha e omitir o traceback apenas para `requests.RequestException` direta ou encadeada

## 2. Testes

- [x] 2.1 Testar que `ReadTimeout` com `exc_info` é renderizado em uma linha, contendo `ReadTimeout` e a mensagem, sem `Traceback`
- [x] 2.2 Testar que exceção de domínio encadeada a `requests.RequestException` também perde o traceback
- [x] 2.3 Testar que exceção inesperada (ex.: `ValueError`) mantém o traceback
- [x] 2.4 Testar que `_configure_logging` grava a linha concisa no arquivo de log para falha de comunicação
- [x] 2.5 Confirmar que `test_fundamental_fallback` (assertivas sobre `record.exc_info`) continua verde

## 3. Verificação final

- [x] 3.1 Rodar `pytest tests/test_presentation/test_main.py tests/test_presentation/test_remaining_extended.py tests/test_application/test_fundamental_fallback.py tests/test_infrastructure/test_regulacao/test_noticias_vinculo.py` com sucesso
- [x] 3.2 Rodar `ruff check src/` e `flake8 --max-complexity=10 --select=B,A,D --extend-exclude=tests ./src/` sem erros
- [x] 3.3 Validar a change com `openspec validate logging-falhas-comunicacao`
