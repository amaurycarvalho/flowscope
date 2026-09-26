## Context

Ver `proposal.md` — Why, e o contrato em
`openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md`.
Estado atual relevante:

- `presentation/gui/charts/quadrant_data.py` é puro (sem I/O): classifica o
  quadrante de um ponto (`classify_quadrant(point)`), monta as trajetórias
  (`build_trajectories`), os pontos de dispersão (`compute_scatter_data`,
  `max_trajectory_qty`, `point_size`) e o resumo textual
  (`count_quadrants`, `pick_interpretation`, `generate_summary`).
- `presentation/gui/charts/vwap_data.py` é puro: normaliza preços pelo VWAP
  (`to_pct`), extrai as séries por ativo (`collect_ticker_data`, 6-tupla),
  estima o bucket (`estimate_bucket_size`) e acumula as formas dos violinos
  (`compute_violin_shapes`).
- `quadrant_chart.py` e `vwap_hist.py` desenham dispersão/arrow/violinos e
  consomem os módulos acima por acesso a `dict`; não importam `infrastructure`.
- `domain/strategies/vwap_distance.py` já calcula o indicador `vwap_distance`;
  a classificação de quadrante é a única regra ainda na UI.
- Não há testes dedicados a esses módulos: a apresentação é omitida da cobertura
  (`tool.coverage` omite `presentation/gui/*`); `test_domain/test_vwap_distance.py`
  cobre a estratégia de indicador, não os helpers.
- A allowlist de fronteira tem 3 entradas legadas sem relação com esta fatia.

## Goals / Non-Goals

**Goals:**

- Colocar a classificação de quadrante em `domain`, operando sobre primitivos.
- Colocar a preparação das trajetórias/dispersão e o resumo do quadrante em
  `application`, como view-models/read-model prontos.
- Colocar a preparação dos dados do VWAP (violinos) em `application`.
- Cobrir as funções movidas com testes puros em `tests/test_domain` e
  `tests/test_application`, sem `DISPLAY`.

**Non-Goals:**

- Não mover a `VWAPDistanceStrategy` nem o cálculo dos indicadores (já em `domain`).
- Não mover o desenho (dispersão, violinos, anotações, toolbar) nem os widgets.
- Não alterar a allowlist (a fatia não tem violação `presentation -> infrastructure`).
- Não redesenhar quadrantes, limites, cores, buckets, rótulos ou textos do resumo.

## Decisions

### D1 — Classificação de quadrante em `domain`

`classify_quadrant` sai de `quadrant_data.py` para `domain`, operando sobre
primitivos (`classify_quadrant(clv: float, vwap_dist: float) -> str | None`) e
expondo a constante dos quadrantes. Alternativa: manter a classificação em
`application`. Rejeitada por ser regra de domínio pura, citada explicitamente no
contrato (D4 do chapéu).

### D2 — View-models do quadrante e resumo em `application`

`application/quadrant` recebe `PontoQuadrante(ticker, date, clv, vwap_dist,
fin_instr_qty)`, `build_trajectories`, `max_trajectory_qty`, `point_size` e
`compute_scatter_data`, além de `count_quadrants`, `pick_interpretation` e
`generate_summary`. A aplicação devolve os pontos prontos e o resumo; os textos
do resumo permanecem idênticos. Alternativa: manter trajetórias e resumo em
`presentation`. Rejeitada por deixar a interpretação de mercado na UI e manter
os testes puros na apresentação.

### D3 — Read-model do VWAP em `application`

`application/vwap` recebe `to_pct`, `collect_ticker_data`, `estimate_bucket_size`
e `compute_violin_shapes`, devolvendo view-models imutáveis (`DadosVwap` com as
séries por ativo e os percentuais mínimo/máximo/último; `FormasViolino` com as
formas, o volume máximo e o bucket). Alternativa: manter a 6-tupla atual e mover
só as funções. Rejeitada por contrariar a convenção de view-model; a paridade de
valores é coberta por testes.

### D4 — Gráficos só desenham

`quadrant_chart.py` e `vwap_hist.py` passam a importar de `domain`/`application`
e mantêm apenas o desenho e o hover; `quadrant_data.py` e `vwap_data.py` saem da
apresentação. Alternativa: manter shims. Rejeitada por duplicar API.

### D5 — Testes puros criados, não migrados

Como não há testes dedicados, cria-se `tests/test_domain/test_quadrant.py`
(classificação) e `tests/test_application/test_quadrant_data.py` +
`test_vwap_data.py` (view-models/read-model), sem `DISPLAY`. Alternativa: não
testar e deixar a cobertura cair. Rejeitada por violar o orçamento de testes e a
meta de cobertura (`fail_under = 85`).

## Risks / Trade-offs

- [Mudança de assinatura de `classify_quadrant`] → atualizar `count_quadrants` e
  os chamadores, mantendo o retorno `Q1..Q4`/`None`.
- [Migração `dict` → dataclass toca o hover] → atualizar os acessos em
  `quadrant_chart`/`vwap_hist`, preservando nomes e valores.
- [Textos do resumo] → mover as strings sem reescrevê-las; cobrir com testes.
- [Código movido sem cobertura] → criar os testes puros na mesma fatia e rodar
  `make test`/`make quality-gate`.

## Migration Plan

1. Criar a classificação de quadrante em `domain`.
2. Criar `application/quadrant` (view-models + resumo) e `application/vwap`
   (read-model dos violinos).
3. Atualizar `quadrant_chart.py`/`vwap_hist.py` para consumir `domain`/
   `application`; remover `quadrant_data.py`/`vwap_data.py`.
4. Criar os testes puros em `tests/test_domain`/`tests/test_application`; rodar
   `make test` e `make quality-gate` (guardrail de fronteira incluso).

Rollback: reverter o change restaura os módulos e o import; comportamento
idêntico.

## Open Questions

- Nome do pacote (`application/quadrant/` vs `application/quadrante/`) e a
  localização do domínio (`domain/quadrant.py` vs
  `domain/strategies/classifiers/quadrant.py`): decidir na implementação, sem
  impacto no contrato.
