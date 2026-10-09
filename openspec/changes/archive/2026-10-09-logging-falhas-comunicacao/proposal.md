## Why

Falhas de comunicação previstas e já tratadas (timeout, erro de rede, HTTP) aparecem no `flowscope.log` com o call stack completo por causa de `exc_info=True` nos handlers de aquisição. Isso polui o log e dá a impressão de exceção não capturada, além de repetir dezenas de linhas para um evento tolerado. Hoje só alguns pontos isolados (ex.: `repository.py`, `noticias_vinculo.py`) registram a falha de forma concisa.

## What Changes

- Estabelecer a convenção: em falha de comunicação tolerada, registrar **uma linha de `WARNING`** com o tipo e a mensagem da exceção, **sem traceback**; exceções não relacionadas a comunicação continuam com traceback.
- Implementar a convenção de forma central no formatter de logging da aplicação, cobrindo todos os pontos de aquisição (diretos e futuros) sem alterar 60+ call sites.
- Preservar os registros em memória (`record.exc_info`) para testes e depuração; apenas a renderização passa a omitir o traceback de comunicação.
- Manter o tratamento explícito já existente em `noticias_vinculo.py` (mensagem de domínio).

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `logging`: nova regra de formatação para falhas de comunicação (sem traceback, com resumo rastreável).

## Impact

- `src/flowscope/presentation/main.py` (formatter da configuração de logging)
- `src/flowscope/infrastructure/b3/noticias_vinculo.py` (já ajustado nesta linha de trabalho)
- `tests/test_presentation/test_main.py` e `tests/test_presentation/test_remaining_extended.py`
