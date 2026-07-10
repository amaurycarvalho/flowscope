## Context

O sistema atualmente usa `fibonacci_dates(ref_date)` que retorna 7 datas fixas com offsets [1,2,3,5,8,13,21] a partir da data de referência, com ajuste para o próximo dia útil. A interface de repositório (`DataRepository.get_available_dates()`) não aceita parâmetros de configuração. O `B3Client.fetch_file()` sempre tenta download da B3 em caso de cache miss. A barra superior contém apenas DateEntry + botões (Hoje, Carregar, Copiar CSV).

O usuário precisa de controle sobre:
- Período da janela (30, 60, 90 dias)
- Estratégia de amostragem dentro da janela
- Períodos > 30 dias devem usar exclusivamente cache

## Goals / Non-Goals

**Goals:**
- Adicionar dois `ttk.Combobox` readonly na barra superior (período + amostragem)
- Implementar 6 estratégias de amostragem para 3 períodos no `calendar.py`
- Modificar `DataRepository.get_available_dates()` para receber config de sampling
- Adicionar modo `cache_only` no `B3Client.fetch_file()` para períodos > 30
- Implementar busca de data mais próxima no cache (±7 dias) com deduplicação
- Recarga automática quando dados já carregados e combo muda
- Incluir combos no OperationGuard (desabilitar durante carga)
- Tooltip fixo em cada combo + texto explicativo do período na statusbar + label inline para amostragem
- Não recarregar se não houver dados carregados (combos inertes)

**Non-Goals:**
- Não alterar o cálculo dos indicadores ou do engine DAG
- Não adicionar novas fontes de dados além da B3 e cache
- Não modificar o cache manager existente (apenas adicionar método auxiliar)
- Não persistir a seleção dos combos nas preferências (cada sessão começa com defaults)
- Não implementar amostragem com semente fixa (MC gera números diferentes a cada execução)

## Decisions

### 1. Arquitetura: Config object em vez de parâmetros posicionais

Criar um `SamplingConfig` dataclass imutável que encapsula período + amostragem:

```python
@dataclass(frozen=True)
class SamplingConfig:
    period_days: int = 30       # 30, 60, 90
    method: str = "fibonacci"   # fibonacci, fibonacci_reverse, fibonacci_double,
                                # monte_carlo, monte_carlo_double, all_days
```

Propagado do controller → use case → repository → calendar. Isso evisa mudanças de assinatura em cascata quando novos parâmetros forem adicionados.

**Alternativa considerada:** parâmetros posicionais `(ref_date, period, method)`. Rejeitado porque qualquer novo parâmetro exigiria alterar toda a cadeia de chamadas.

### 2. Calendar: Novas funções de geração de datas

```
generate_dates(ref_date, config) → list[date]
    │
    ├── _fibonacci(ref_date, period_days)
    ├── _fibonacci_reverse(ref_date, period_days)
    ├── _fibonacci_double(ref_date, period_days)
    ├── _monte_carlo(ref_date, period_days, count)
    ├── _monte_carlo_double(ref_date, period_days, count)
    └── _all_days(ref_date, period_days)
```

Todas retornam datas brutas (sem ajuste de dia útil). O ajuste é feito em duas etapas:
1. `_next_business_day(d)` — aproximação local para cada data
2. `_nearest_cached_date(d, cache, max_deviation=7)` — se cache_only, busca no cache

A deduplicação ocorre no final: `sorted(set(adjusted_dates))`.

**Tabela de geração:**

| Método | 30 dias | 60 dias | 90 dias |
|--------|---------|---------|---------|
| Fibonacci | fibs 1,2,3,5,8,13,21 | fibs 1,2,3,5,8,13,21,34,55 | fibs 1,2,3,5,8,13,21,34,55,89 |
| Fib reverso | `ref-22+d`, d∈fibs | `ref-56+d`, d∈fibs até 55 | `ref-90+d`, d∈fibs até 89 |
| Fib duplo | `ref-22+d`, d∈{1,2,3,13,19,20,21} | `ref-56+d`, d∈fibs + complementos até 7 datas | `ref-90+d`, d∈fibs + complementos até 7 datas |
| MC | ref-1, ref-30, +5 aleatórios | ref-1, ref-60, +5 aleatórios | ref-1, ref-90, +5 aleatórios |
| MC duplo | ref-1, ref-30, +12 aleatórios | ref-1, ref-60, +12 aleatórios | ref-1, ref-90, +12 aleatórios |
| Todos os dias | ref-30 .. ref-1 | ref-60 .. ref-1 | ref-90 .. ref-1 |

**Monte Carlo:** `random.sample(range(primeira_data + 1, ultima_data), k)` — exclui primeira e última do sorteio.

**Fibonacci duplo para 60/90 dias:** usar os offsets de Fibonacci + complementos até completar 7 datas, priorizando datas próximas ao início e fim do período.

### 3. Cache-only mode

`B3Client.fetch_file()` ganha parâmetro opcional `cache_only: bool = False`:
- `False` (padrão, período=30): comportamento atual — tenta cache, se miss faz download
- `True` (período>30): se cache miss, retorna None (data é pulada)

`CacheManager` ganha método `find_nearest(date, max_deviation_days=7) → date | None`:
- Varre `max_deviation_days` para cima e para baixo
- Retorna a primeira data encontrada no cache
- Usa `os.path.exists(cache_dir / f"{d}.csv")` para verificação

### 4. Ajuste de dia útil com fallback para cache

Algoritmo de resolução de data:

```python
def resolve_date(d, ref_date, period_days, cache, cache_only):
    # Passo 1: ajuste local para próximo dia útil
    d = _next_business_day(d)
    # Passo 2: se cache_only, busca data alternativa no cache
    if cache_only:
        nearest = cache.find_nearest(d, max_deviation=7)
        if nearest is None:
            return None   # pula esta data
        return nearest
    return d
```

### 5. Integração na GUI

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ Data: [2026-07-10 ▼] [📅] [🔄] [30 dias ▼] [Fibonacci ▼] [📋]  Dados...  Fib: ... │
│        DateEntry     Today  Load   Período     Amostragem    Copy        date_label │
```

Eventos:
- `<<ComboboxSelected>>` no combo período ou amostragem:
  - Se `self._current_data` vazio → sem ação
  - Se `self._current_data` populado → `self._controller.on_load_data()`
- Mouse percorrendo itens (navegação por setas ou hover no dropdown):
  - Atualiza `self._status_var` com texto explicativo do item selecionado
  - A carga só acontece quando o usuário de fato seleciona (fecha o dropdown)

### 6. Tooltips, label de amostragem e statusbar

Tooltip fixo em cada combobox:

| Combo | Tooltip |
|-------|---------|
| Período | "Seleciona a janela de tempo para análise dos dados históricos" |
| Amostragem | "Define o método de seleção das datas dentro do período" |

A mensagem explicativa do método de amostragem é exibida em um `tk.Label` (`_sampling_label`, fg="gray") posicionado ao lado do `_date_label` na barra superior. O label é atualizado no evento `<<ComboboxSelected>>`. Já a explicação do período permanece na barra de status (por ser informação sobre cache/download).

Textos no label de amostragem:

| Método | Texto no label |
|--------|----------------|
| Fibonacci | "Amostra concentrada nas datas mais recentes." |
| Fibonacci reverso | "Amostra concentrada nas datas mais distantes." |
| Fibonacci duplo | "Amostra concentrada nas margens do período." |
| Monte Carlos | "Amostra das margens do período com centro aleatório disperso." |
| Monte Carlos duplo | "Amostra das margens com centro aleatório concentrado." |
| Todos os dias | "Amostra contendo todos os dias." |

Textos na statusbar (apenas período):

| Combo | Item | Texto na statusbar |
|-------|------|-------------------|
| Período | 30 dias | "Janela de 30 dias corridos. Os dados serão baixados da B3 e armazenados em cache." |
| Período | 60 dias | "Janela de 60 dias corridos. Apenas dados já em cache serão utilizados — sem download da B3." |
| Período | 90 dias | "Janela de 90 dias corridos. Apenas dados já em cache serão utilizados — sem download da B3." |

### 7. OperationGuard

Os combos usam `state="readonly"` como padrão. Em `_disable_all_buttons`:

```python
self._period_combo.config(state=tk.DISABLED)
self._sampling_combo.config(state=tk.DISABLED)
```

Em `_restore_all_buttons`, retornam para `"readonly"`. O código atual que salva/restaura estados via dict de widgets funciona porque `ttk.Combobox` aceita `config(state=tk.DISABLED)` e `config(state="readonly")`.

### 8. Propagação no controller

```python
# controller.py
def on_load_data(self, ref_date=None):
    with self._guard.acquire() as ok:
        if not ok:
            return
        config = self._presenter.get_sampling_config()
        # ...
        result = self._analyze.execute(ref_date, tickers, config=config, ...)
```

`presenter.get_sampling_config()` lê os valores atuais dos combos e monta o `SamplingConfig`.

## Risks / Trade-offs

- **Monte Carlo não-determinístico**: cada execução gera datas diferentes → Mitigação: é um comportamento esperado e documentado na interface e nos textos explicativos. O usuário entende que é uma amostragem aleatória.
- **Período 60/90 dias pode ter poucas datas de cache**: se o cache estiver vazio, pode resultar em zero datas → Mitigação: o sistema deve carregar pelo menos algumas datas de 30 dias primeiro. A ordem natural de uso (começar com 30, depois expandir) mitiga isso. Se não houver cache, a carga resulta em zero trades e o painel mostra "Sem dados".
- **Cache scan para buscar data próxima**: pode ser lento se o cache tiver muitas datas → Mitigação: o cache_manager já organiza por data; `find_nearest` varre no máximo 7+7=14 arquivos. Operação O(1) em termos práticos.
- **Ajuste de data "local" pode produzir duplicatas**: se duas datas de Fibonacci diferentes calibrarem no mesmo dia útil → Mitigação: `sorted(set(adjusted_dates))` elimina duplicatas no final.
- **Combos readonly não disparam evento de hover para statusbar**: o dropdown nativo do ttk.Combobox não expõe evento de navegação entre itens → Mitigação: usar bind `<Key-Up>` e `<Key-Down>` no combobox para atualizar statusbar quando o valor `current` muda via teclado. Para navegação com mouse no dropdown, a solução nativa do Tk não expõe isso facilmente; o texto na statusbar será atualizado apenas `<<ComboboxSelected>>`. Textos de preview durante navegação por teclado são um extra não-crítico.
