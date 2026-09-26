## Why

Os gráficos de dominância do pregão mantêm em `presentation` a construção pura
do ranking (`ranking_data.build_rows`/`stem_lengths`) e da linha do tempo
(`timeline_data.build_rows`/`direction_balance`), além das hastes
compartilhadas de `dominance_data`. Como consequência, os painéis
recalculam os view-models a partir de `all_indicators`/`money_flow_volume`
brutos e essas regras puras ficam sem testes fora da UI. Esta fatia move a
construção de ranking/timeline e a geometria das hastes para `application`,
deixando a apresentação apenas desenhar.

## What Changes

- A construção pura do ranking (`build_rows`, `stem_lengths`) sai de
  `presentation/gui/charts/ranking_data.py` para `application/dominance/`, como
  view-model pronto (`RankingRow`).
- A construção pura da linha do tempo (`build_rows`, `direction_balance`) sai de
  `presentation/gui/charts/timeline_data.py` para `application/dominance/`, como
  view-model pronto (`TimelineRow`).
- A geometria/cor das hastes e a localização da linha sob o cursor
  (`stem_length`, `_compute_stems`, `bar_colors`, `bar_hit`, `find_closest_row`)
  saem de `presentation/gui/charts/dominance_data.py` para `application/dominance/`;
  o desenho (`draw_stems`, `draw_ticker_labels`) permanece na apresentação e
  consome a geometria pronta.
- `dominance_ranking.py` e `dominance_timeline.py` passam a consumir
  `application` e mantêm apenas o desenho (barras, hastes, tooltips, toolbar).
- Criação de testes puros em `tests/test_application` para as funções movidas
  (não havia testes dedicados), sem `DISPLAY`.
- Sem alteração da allowlist de fronteira: a fatia não importa `infrastructure`.

## Capabilities

### New Capabilities

### Modified Capabilities

Opta por não alterar specs (`skip_specs: true`): refatoração que preserva o
comportamento observável, implementando o contrato `layer-boundaries` do change
`clean-architecture-layering`.

## Impact

- **Depende de**: `add-layer-architecture-guardrails` (allowlist e teste de
  fronteira) e do padrão de view-model já aplicado em
  `refactor-documentos-layers`/`refactor-noticias-layers`.
- **Código movido**: `presentation/gui/charts/ranking_data.py`,
  `timeline_data.py` (total) e as funções puras de `dominance_data.py`; consumo
  atualizado em `dominance_ranking.py` e `dominance_timeline.py`.
- **Novos tipos**: `application/dominance/*` (view-models de ranking/timeline e
  geometria das hastes).
- **Testes**: criação de testes puros para as funções movidas; os testes de
  integração/wiring existentes permanecem.
- **Sem alteração de comportamento**: ordenação, percentuais, cores, rótulos,
  tooltips e eixos permanecem idênticos.
