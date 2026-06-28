## Context

O `QuadrantChart` (em `quadrant_chart.py`) recebe um `dict` de tickers e plota setas de trajetória para **todos os tickers presentes**. O controle de "Todos" vs ticker específico é feito em `app.py:_update_charts()` que já filtra os dados antes de passar ao chart. O combobox da Análise do Ticker (`_ticker_combo`) é independente — não há comunicação entre os dois combos.

```
Estado atual:

  _quadrant_ticker_combo ──► _update_charts() ──► QuadrantChart.update(data)
                                                       │
                                                       └── setas p/ todos no dict

  _ticker_combo ──► _update_ticker_indicator_tabs()
         (independente)
```

## Goals / Non-Goals

**Goals:**
- Ocultar setas (quiver) quando "Todos" estiver selecionado no combobox do Quadrantes
- Exibir setas apenas para o ticker selecionado (já acontece devido ao filtro em `_update_charts`, mas garantir controle explícito)
- Sincronizar bidirecionalmente `_quadrant_ticker_combo` e `_ticker_combo`
- Limpar `_ticker_combo` quando "Todos" for selecionado no Quadrantes
- Atualização de conteúdo da Análise do Ticker ocorre apenas quando o usuário navega até a aba (comportamento existente)

**Non-Goals:**
- Não alterar a renderização de bolhas, cores, tamanhos ou labels do scatter
- Não forçar navegação de aba ao sincronizar comboboxes
- Não sincronizar o combobox do VWAP (`_vwap_ticker_combo`)
- Não alterar o `TickerList` widget ou sua lógica de filtro

## Decisions

### Decisão 1: Parâmetro explícito `show_arrows` no `QuadrantChart.update()`

**Opções consideradas:**
- *Implícito*: chart decide se mostra setas baseado no número de tickers no dict (1 → mostra, >1 → oculta). Mais simples, mas frágil — qualquer outro caller que passe 1 ticker sem querer setas seria afetado.
- *Explícito* (escolhido): `update(data, show_arrows=True)`. O caller (`app.py`) decide com base no valor do combobox. Mais previsível, mais testável.

**Decisão:** Adotar parâmetro explícito `show_arrows: bool = False` no `QuadrantChart.update()`.

### Decisão 2: Sincronização via bindings `<<ComboboxSelected>>`

**Opções consideradas:**
- *Proxy/observador centralizado*: um objeto mediator gerencia os combos. Robusto para N combos, mas overengineering para 2.
- *Bindings diretos* (escolhido): cada combo registra um handler que atualiza o outro. Simples, direto, com guarda para evitar loop infinito.

**Decisão:** Usar bindings `<<ComboboxSelected>>` nos dois combos com uma flag de supressão (`_syncing_in_progress`) para evitar reentrância infinita.

### Decisão 3: Sincronizar valor sem disparar `_update_charts` duplicado

Quando o Quadrantes seleciona um ticker, `_update_charts()` já é chamado. O binding de sincronia apenas define o valor do outro combo, sem chamar `_update_charts` novamente.

Quando a Análise do Ticker seleciona um ticker, o binding sincroniza o Quadrantes e dispara `_update_charts()` (refletindo a seleção no gráfico). A atualização do conteúdo textual da Análise do Ticker continua sendo feita apenas quando o usuário navega para aquela aba.

**Decisão:** A sincronização de `_ticker_combo → _quadrant_ticker_combo` também chama `_update_charts()`. A direção contrária apenas seta o valor.

## Risco / Trade-offs

- **Loop de reentrância**: risco ao sincronizar bidirecionalmente via `<<ComboboxSelected>>`. Mitigado com flag `_syncing_in_progress`.
- **Sincronização parcial**: se o ticker selecionado no Quadrantes não existir mais no filter (após `_on_ticker_edit`), o combo da Análise do Ticker pode ficar com valor inválido. Mitigado: `_update_ticker_selectors` já valida valores existentes e reseta para "Todos"/vazio se necessário.
- **Performance**: `_update_charts()` é chamado ao selecionar ticker na Análise do Ticker, mesmo que o usuário não esteja na aba Quadrantes. Isso é aceitável — a operação é leve (filtra dict) e o chart só atualiza se estiver visível.
