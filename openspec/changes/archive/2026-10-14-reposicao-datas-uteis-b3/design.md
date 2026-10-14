## Context

Ver `proposal.md` — Why. A regra de "dia útil" já existe (feriados nacionais + segunda a sexta), mas está presa em `infrastructure/b3/calendar.py` como `_is_business_day` e `infrastructure/b3/holidays.py` como `FERIADOS_NACIONAIS`. A aplicação (`application/use_cases.py`) não pode importar `infrastructure` — o spec `layer-boundaries` proíbe e há teste de fronteira com allowlist que só encolhe. Por isso a correção não pode ser apenas "importar o predicado do calendário"; é preciso mover a regra para o domínio.

Restrição adicional: `infrastructure/b3/holidays.py` é o único consumidor atual de `FERIADOS_NACIONAIS` (além de `calendar.py`), mas o caminho de importação deve permanecer estável para evitar quebra desnecessária.

## Goals / Non-Goals

**Goals:**
- Uma única definição de "dia útil da B3" (feriados + fim de semana), no domínio.
- A busca de data substituta usar essa definição, nunca consultando feriados.
- Manter os imports existentes funcionando.

**Non-Goals:**
- Limitar a busca à véspera da data de referência (hoje) — fora de escopo nesta change.
- Rebaixar/tratar o HTTP 400 de `requestname` como "data indisponível" — fora de escopo.
- Qualquer alteração no conjunto de feriados ou na geração/ajuste das datas de amostragem.

## Decisions

### Predicado e feriados no domínio: `domain/b3/calendario.py`

Criar `src/flowscope/domain/b3/calendario.py` com:

```python
from datetime import date

FERIADOS_NACIONAIS = frozenset({...})  # movido de infrastructure/b3/holidays.py

def is_business_day(d: date) -> bool:
    return d.weekday() < 5 and d not in FERIADOS_NACIONAIS
```

Módulo puro, sem I/O — compatível com `layer-boundaries` (domínio sem dependências externas).

**Alternativa descartada:** expor `is_business_day` público em `infrastructure/b3/calendar.py` e importá-lo em `application/use_cases.py`. Rejeitada porque `application → infrastructure` viola o spec `layer-boundaries` e estouraria o teste de fronteira/allowlist.

### `infrastructure/b3/holidays.py` vira shim de reexportação

`holidays.py` passa a reexportar `FERIADOS_NACIONAIS` do domínio, preservando o caminho de importação histórico sem duplicar a lista:

```python
from flowscope.domain.b3.calendario import FERIADOS_NACIONAIS

__all__ = ["FERIADOS_NACIONAIS"]
```

**Alternativa descartada:** deletar `holidays.py` e atualizar `calendar.py`. Funciona, mas quebra o caminho público sem ganho; o shim custa três linhas e evita surpresa para consumidores externos ao repositório.

### `infrastructure/b3/calendar.py` consome o domínio

`calendar.py` importa `is_business_day` do domínio e mantém `_is_business_day` apenas como alias fino (ou remove o wrapper e usa o nome do domínio diretamente). As chamadas internas (`_next_business_day`, `_is_valid_candidate`) seguem inalteradas em comportamento.

### `_find_replacement_date` passa a validar dia útil

Em `application/use_cases.py`, a condição:

```python
if candidate > ref_date or candidate in seen or candidate.weekday() >= 5:
```

passa a:

```python
from flowscope.domain.b3.calendario import is_business_day
...
if candidate > ref_date or candidate in seen or not is_business_day(candidate):
```

`candidate > ref_date` (limite superior) e o restante do algoritmo (ordem `-1` antes de `+1`, margem de 7 dias, retorno de `(data, trades)`) permanecem como estão.

### Estratégia de testes

- `tests/test_application/test_use_cases_extended.py`: novo cenário em que a candidata adjacente é um feriado conhecido (ex.: `2026-10-12`) e a busca só retorna a próxima dia útil; e cenário de feriado entre a data e o candidato válido.
- `tests/test_infrastructure/test_b3_calendar.py` e `test_sampling_calendar.py`: garantem que o ajuste de datas continua usando os feriados após a mudança de origem.
- Teste de fronteira existente (`layer-boundaries`) deve continuar verde, comprovando que a aplicação não importa infraestrutura.

## Risks / Trade-offs

- **Import de aplicação→domínio**: permitido pelo fluxo `application -> domain`; sem risco de fronteira.
- **Feriados desatualizados**: a lista é finita (2026–2027). Um feriado ausente continuaria gerando HTTP 400. Mitigação: a lista já é a fonte única usada pelo resto do sistema; mantê-la é responsabilidade existente, não introduzida aqui.
- **Feriados estaduais/municipais**: continuam fora do escopo (o calendário só modela feriados nacionais), como hoje.
