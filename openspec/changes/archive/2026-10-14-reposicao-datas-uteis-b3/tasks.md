## 1. Domínio: predicado de dia útil

- [x] 1.1 Criar `src/flowscope/domain/b3/calendario.py` com `FERIADOS_NACIONAIS` (movido de `infrastructure/b3/holidays.py`) e `is_business_day(d)` (`weekday() < 5 and d not in FERIADOS_NACIONAIS`); verificar com `.venv/bin/python -c "from flowscope.domain.b3.calendario import is_business_day, FERIADOS_NACIONAIS; assert not is_business_day(__import__('datetime').date(2026,10,12)); assert is_business_day(__import__('datetime').date(2026,10,13))"`
- [x] 1.2 Exportar `is_business_day`/`FERIADOS_NACIONAIS` em `src/flowscope/domain/b3/__init__.py`; verificar que `from flowscope.domain.b3 import is_business_day` importa sem erro

## 2. Infraestrutura: consumir o domínio

- [x] 2.1 Converter `src/flowscope/infrastructure/b3/holidays.py` em shim de reexportação (`FERIADOS_NACIONAIS` do domínio); verificar que `from flowscope.infrastructure.b3.holidays import FERIADOS_NACIONAIS` continua funcionando e tem o mesmo conteúdo
- [x] 2.2 Atualizar `src/flowscope/infrastructure/b3/calendar.py` para usar `is_business_day` do domínio (mantendo `_is_business_day` como alias ou removendo o wrapper); verificar que `tests/test_infrastructure/test_b3_calendar.py` e `tests/test_infrastructure/test_sampling_calendar.py` passam

## 3. Aplicação: corrigir a busca de data substituta

- [x] 3.1 Em `src/flowscope/application/use_cases.py`, importar `is_business_day` de `flowscope.domain.b3.calendario` e trocar `candidate.weekday() >= 5` por `not is_business_day(candidate)` em `_find_replacement_date`; verificar que a aplicação não importa `flowscope.infrastructure` (teste de fronteira `layer-boundaries` verde)

## 4. Testes

- [x] 4.1 Adicionar em `tests/test_application/test_use_cases_extended.py` cenário de feriado nacional (ex.: `2026-10-12`) pulado como candidata, com a busca prosseguindo até o próximo dia útil; verificar com `.venv/bin/python -m pytest tests/test_application/test_use_cases_extended.py -q`
- [x] 4.2 Adicionar em `tests/test_infrastructure/test_b3_calendar.py` teste garantindo que o ajuste de datas continua excluindo feriados após mover a lista para o domínio; verificar com `.venv/bin/python -m pytest tests/test_infrastructure/test_b3_calendar.py -q`

## 5. Verificação da change

- [x] 5.1 Executar `make lint` e `make complexity` e confirmar ausência de erros
- [x] 5.2 Executar os testes relacionados (`tests/test_application/test_use_cases_extended.py`, `tests/test_application/test_use_cases.py`, `tests/test_infrastructure/test_b3_calendar.py`, `tests/test_infrastructure/test_sampling_calendar.py`, `tests/test_infrastructure/test_b3_repository.py`) e confirmar que passam
- [x] 5.3 (Manual, usuário) Executar a suíte completa/quality gate apenas se autorizado; não é executada pelo agente sem autorização explícita
