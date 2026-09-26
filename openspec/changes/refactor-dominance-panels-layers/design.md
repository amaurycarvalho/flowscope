## Context

Ver `proposal.md` — Why, e o contrato em
`openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md`.
Estado atual relevante:

- `presentation/gui/charts/ranking_data.py` é puro: `build_rows(data)` extrai o
  último CLV e o `money_flow_volume` de cada ativo (`all_indicators.clv`) e
  `stem_lengths` deriva o comprimento das hastes; `draw_ticker_labels` desenha.
- `presentation/gui/charts/timeline_data.py` é puro: `build_rows(info)` monta as
  linhas cronológicas (CLV, eficiência, fluxo diário) e `direction_balance`
  conta dias compradores/vendedores.
- `presentation/gui/charts/dominance_data.py` mistura puro e desenho:
  `stem_length`, `_compute_stems`, `bar_colors`, `bar_hit` e `find_closest_row`
  são puros; `draw_stems` desenha sobre os eixos.
- `dominance_ranking.py` e `dominance_timeline.py` chamam `build_rows`,
  `bar_colors`, `draw_stems`, `find_closest_row`, `direction_balance` e desenham
  barras/anotações; não importam `infrastructure` e não constam na allowlist.
- Não há testes dedicados a essas funções: a apresentação é omitida da cobertura
  (`tool.coverage` omite `presentation/gui/*`) e os testes existentes cobrem
  apenas wiring/integração das abas.

## Goals / Non-Goals

**Goals:**

- Colocar a construção das linhas de ranking e de linha do tempo em
  `application/dominance`, como view-models prontos.
- Colocar a geometria/cor das hastes (pura) em `application/dominance` e deixar
  o desenho na apresentação.
- Cobrir as funções movidas com testes puros em `tests/test_application`, sem
  `DISPLAY`.

**Non-Goals:**

- Não mover os classificadores de domínio
  (`classify_dominance`/`classify_conviction`) nem o núcleo de estratégias.
- Não mover o desenho (barras, anotações de hover, toolbar, layout) nem os
  widgets.
- Não alterar a allowlist (a fatia não tem violação `presentation -> infrastructure`).
- Não redesenhar cores, limiares, ordenação, rótulos ou textos de tooltip.

## Decisions

### D1 — View-models de ranking e timeline em `application/dominance`

`build_rows` e a chave de ordenação por CLV viram view-models imutáveis em
`application/dominance`: `RankingRow(ticker, clv, mfv, date)` e
`TimelineRow(date, clv, efficiency, daily_mfv)`, com `build_rows(data)`/
`build_rows(info)`, `stem_lengths(...)` e `direction_balance(rows)`. Alternativa:
manter os `dict` e mover só `build_rows`. Rejeitada por contrariar a convenção de
view-model (D2 do chapéu) e deixar a interpretação de `all_indicators` na UI.

### D2 — Geometria das hastes em `application/dominance`, desenho na apresentação

`stem_length`, `_compute_stems` (renomeado `compute_stems`) e `bar_colors` vão
para `application/dominance/hastes.py`; `draw_stems` permanece em
`presentation/gui/charts/dominance_data.py` e apenas consome a geometria pronta
para chamar `axes.hlines`. Alternativa: mover `draw_stems` junto. Rejeitada por
ser desenho (matplotlib) e não regra de aplicação.

### D3 — Hit-testing de hover permanece na apresentação

`bar_hit` e `find_closest_row` são interação de mouse (desenho/hover) e ficam em
`presentation/gui/charts/dominance_data.py`, consumindo os view-models de
`application` (campo `clv`). Alternativa: mover para `application`. Rejeitada por
não ser regra de negócio e depender da geometria de exibição.

### D4 — Migração direta sem reexportação

`timeline_data.py` sai de `presentation` (todo puro); `ranking_data.py` fica
apenas com `draw_ticker_labels` (desenho) e `dominance_data.py` apenas com
`draw_stems`/hit-testing. Os painéis passam a importar os view-models de
`application`. Alternativa: manter módulos espelho. Rejeitada por duplicar API.

### D5 — Testes puros criados, não migrados

Como não existem testes dedicados, `tests/test_application/test_dominance_data.py`
passa a cobrir `build_rows` (ranking e timeline), `stem_lengths`,
`direction_balance`, `stem_length`, `compute_stems` e `bar_colors`, sem
`DISPLAY`. Alternativa: não testar e deixar a cobertura cair. Rejeitada por
violar o orçamento de testes e a meta de cobertura (`fail_under = 85`).

## Risks / Trade-offs

- [Mudança de `dict` para dataclass toca o hover] → atualizar
  `dominance_ranking.py`/`dominance_timeline.py` para acesso por atributo,
  mantendo nomes e valores idênticos.
- [Código movido sem cobertura] → criar os testes puros na mesma fatia e rodar
  `make test`/`make quality-gate`.
- [`dominance_data.py` misto] → separar com rigor: só permanece o que usa
  `axes`/interação de mouse; o restante vai para `application`.
- [Cobertura de apresentação omitida] → o código movido passa a ser medido em
  `application`; os testes novos mantêm a cobertura global acima do limite.

## Migration Plan

1. Criar `application/dominance` com os view-models de ranking/timeline e a
   geometria das hastes.
2. Atualizar `dominance_ranking.py`/`dominance_timeline.py` para consumir
   `application`; enxugar `ranking_data.py`/`dominance_data.py`; remover
   `timeline_data.py`.
3. Criar os testes puros em `tests/test_application`.
4. Rodar `make test` e `make quality-gate` (guardrail de fronteira incluso).

Rollback: reverter o change restaura os módulos e o import; comportamento
idêntico.

## Open Questions

- Nome do pacote (`application/dominance/`) e a divisão entre `ranking.py`,
  `timeline.py` e `hastes.py`: decidir na implementação, sem impacto no contrato.
