## Why

A busca por data substituta quando uma data de amostragem não tem negociações (`_find_replacement_date`, em `application/use_cases.py`) descarta apenas fins de semana (`candidate.weekday() >= 5`) e ignora os feriados nacionais da B3. Assim, em recargas próximas de um feriado, o sistema consulta datas sem arquivo publicado e a B3 responde HTTP 400 — ruído de erro recorrente e violação do requisito "Substituição de datas sem trades" do spec `data-ingestion`, que exige candidatas em **dias úteis**. O mesmo conceito de dia útil já é aplicado corretamente no resolvedor do calendário (`infrastructure/b3/calendar.py`), mas por um predicado privado não reaproveitado pela aplicação.

## What Changes

- **Centralizar o predicado de dia útil da B3 em `domain`** (novo módulo `domain/b3/calendario.py` com a lista de feriados nacionais e `is_business_day(data)`), de forma que a regra de negócio resida no domínio e não em infraestrutura (respeitando `layer-boundaries`: `application` não pode importar `infrastructure`).
- Fazer `infrastructure/b3/calendar.py` e `infrastructure/b3/holidays.py` consumirem/reexportarem a definição do domínio, eliminando a duplicação.
- **Corrigir `_find_replacement_date`** para usar `is_business_day` em vez de `candidate.weekday() >= 5`, de modo que feriados nacionais nunca sejam consultados como data substituta.
- Cobrir com testes unitários: candidata em feriado é pulada; continuidade da busca após pular o feriado; e que o resolvedor do calendário segue usando a mesma definição.

Fora de escopo (não contemplado nesta change): limitar a busca à véspera da data de referência e traduzir o HTTP 400 de `requestname` em "data indisponível" com log rebaixado.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `data-ingestion`: o requisito "Substituição de datas sem trades (pós-resolução ticker-aware)" passa a explicitar que as candidatas são **dias úteis da B3** (segunda a sexta, excluindo feriados nacionais definidos pelo calendário do projeto), com cenário cobrindo o feriado.

## Impact

- **Domínio**: novo `src/flowscope/domain/b3/calendario.py` (lista de feriados + `is_business_day`).
- **Infraestrutura**: `src/flowscope/infrastructure/b3/holidays.py` (passa a reexportar do domínio) e `src/flowscope/infrastructure/b3/calendar.py` (usa o predicado do domínio).
- **Aplicação**: `src/flowscope/application/use_cases.py` (`_find_replacement_date` passa a validar dia útil via domínio).
- **Testes**: `tests/test_application/test_use_cases_extended.py` (novos cenários de feriado), `tests/test_infrastructure/test_b3_calendar.py` e `tests/test_infrastructure/test_sampling_calendar.py` (garantia de regressão).
- **Compatibilidade**: sem mudança de API pública; `FERIADOS_NACIONAIS` continua importável de `infrastructure/b3/holidays.py`; nenhuma dependência nova.
