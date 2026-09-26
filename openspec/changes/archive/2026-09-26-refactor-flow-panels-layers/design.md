## Context

Ver `proposal.md` — Why, e o contrato em
`openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md`.
Estado atual relevante:

- `presentation/gui/charts/financial_flow_helpers.py` mistura três
  responsabilidades: extração de métricas (`as_float`, `extract_session_metrics`),
  formatação/desenho (`format_accumulated_mfv`, `format_dmf_value`,
  `format_dmf_text`, `draw_card`, `draw_clv_bar`, `draw_pressure_labels`,
  `draw_bs_bar`, `tooltip_lines`) e geração do resumo (`pressure_percentages`,
  `flow_intensity_part`, `close_position_part`, `dominance_part`,
  `conviction_part`, `generate_summary`).
- `extract_session_metrics(daily_sorted, all_inds, info)` lê a última data, extrai
  CLV, DMF, pressões, range, volume financeiro e o MFV acumulado e devolve um
  `dict` com os valores e os derivados (`fin_vol_millions`).
- `generate_summary(dmf, classification, clv, bp, sp)` combina intensidade do
  fluxo, posição do fechamento, dominância no range e convicção em uma frase.
- `financial_flow_panel.py` chama `extract_session_metrics`, classifica com
  `classify_money_flow` (já em `domain`), formata o MFV, desenha e emite o
  resumo via `summary_callback`.
- `classify_money_flow`/`MoneyFlowClassification` já residem em `domain`; a
  allowlist de fronteira tem 3 entradas legadas sem relação com esta fatia.
- Não há testes dedicados a esses helpers: a apresentação é omitida da cobertura
  (`tool.coverage` omite `presentation/gui/*`).

## Goals / Non-Goals

**Goals:**

- Colocar a extração das métricas do pregão e a geração do resumo em
  `application/flow`, como view-model pronto e texto interpretado.
- Colocar a normalização das pressões de compra e venda em `domain`.
- Manter a formatação e todo o desenho (`draw_*`, tooltip) na apresentação.
- Cobrir as funções movidas com testes puros em `tests/test_application` e
  `tests/test_domain`, sem `DISPLAY`.

**Non-Goals:**

- Não mover o classificador de fluxo (`classify_money_flow`) nem as estratégias
  de indicadores, já em `domain`.
- Não mover o desenho (cartão, barras, rótulos, tooltip, toolbar) nem os
  formatadores de texto.
- Não alterar a allowlist (a fatia não tem violação `presentation -> infrastructure`).
- Não redesenhar limiares, cores, rótulos, textos ou o layout do painel.

## Decisions

### D1 — View-model de métricas em `application/flow`

`extract_session_metrics` vira `build_session_metrics(daily_sorted, all_inds,
info)` em `application/flow/metrics.py`, retornando a dataclass imutável
`SessionFlowMetrics(last_date, clv, dmf, bp, sp, rp, fin_vol, fin_vol_millions,
accumulated_mfv)`; `as_float` acompanha como helper interno. Alternativa:
manter o `dict` e mover só a extração. Rejeitada por contrariar a convenção de
view-model (D2 do chapéu) e deixar a UI interpretando `all_indicators`.

### D2 — Resumo textual em `application/flow`

`generate_summary` e os trechos `flow_intensity_part`, `close_position_part`,
`dominance_part` e `conviction_part` vão para `application/flow/summary.py`,
seguindo o precedente de `application/quadrant/resumo.py`. Alternativa: manter o
resumo na apresentação. Rejeitada por ser interpretação de domínio (limiares de
DMF/CLV/pressão/convicção) e não desenho.

### D3 — Normalização das pressões em `domain`

`pressure_percentages(bp, sp)` vai para `domain/strategies/pressure.py`: é uma
razão pura entre as pressões de compra/venda já calculadas por estratégias de
domínio, sem dependência de exibição. Alternativa: deixá-la em `application`.
Rejeitada por duplicar uma regra de negócio que não depende de dados de
aplicação.

### D4 — Formatação e desenho permanecem na apresentação

`format_accumulated_mfv`, `format_dmf_value`, `format_dmf_text`, `draw_card`,
`draw_clv_bar`, `draw_pressure_labels`, `draw_bs_bar` e `tooltip_lines` ficam em
`financial_flow_helpers.py`; `draw_bs_bar` importa `pressure_percentages` de
`domain`. Alternativa: mover os formatadores para `application`. Rejeitada por
serem formatação de exibição (texto, unidades, cores).

### D5 — Testes puros criados, não migrados

Como não existem testes dedicados, cria-se `tests/test_application/test_flow_data.py`
para `build_session_metrics` (extração, nulos, derivados) e os ramos de
`generate_summary`, e `tests/test_domain/test_pressure.py` para
`pressure_percentages` (proporções e ausência de pressão), sem `DISPLAY`.
Alternativa: não testar e deixar a cobertura cair. Rejeitada por violar o
orçamento de testes e a meta de cobertura (`fail_under = 85`).

## Risks / Trade-offs

- [Mudança de `dict` para dataclass toca o painel] → atualizar
  `financial_flow_panel.py` para acesso por atributo, mantendo nomes e valores
  idênticos no hover e no desenho.
- [Código movido sem cobertura] → criar os testes puros na mesma fatia e rodar
  `make test`/`make quality-gate`.
- [Resumo com strings sensíveis] → preservar exatamente os textos e a ordem de
  concatenação ao mover.
- [`draw_bs_bar` depende de percentual] → continuar recebendo `bp`/`sp` e usar
  `pressure_percentages` de `domain`, sem recalcular na UI.

## Migration Plan

1. Criar `domain/strategies/pressure.py` com `pressure_percentages`.
2. Criar `application/flow` com `SessionFlowMetrics`/`build_session_metrics` e
   `generate_summary`/trechos.
3. Atualizar `financial_flow_helpers.py` e `financial_flow_panel.py` para
   consumir `domain`/`application`, mantendo formatação/desenho/tooltip.
4. Criar os testes puros em `tests/test_application` e `tests/test_domain`.
5. Rodar `make test` e `make quality-gate` (guardrail de fronteira incluso).

Rollback: reverter o change restaura as funções no helper; comportamento
idêntico.

## Open Questions

- Nome do pacote de aplicação (`application/flow/`) e se `as_float` é exposto
  publicamente: decidir na implementação, sem impacto no contrato.
