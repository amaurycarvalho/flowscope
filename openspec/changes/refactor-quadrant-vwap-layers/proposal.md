## Why

A fatia de Quadrantes/VWAP mantém em `presentation` a classificação de
quadrante (`quadrant_data.classify_quadrant`), a preparação das trajetórias e do
resumo textual (`quadrant_data`) e a preparação dos dados do VWAP
(`vwap_data`). Como consequência, uma regra de domínio (quadrante) reside na UI e
as funções puras de mapeamento ficam sem testes fora da apresentação. Esta fatia
move a classificação de quadrante para `domain` e os dados do quadrante e do
VWAP para `application`, deixando os gráficos apenas desenhar.

## What Changes

- A classificação `classify_quadrant` (e a constante dos quadrantes) sai de
  `presentation/gui/charts/quadrant_data.py` para `domain`, passando a operar
  sobre primitivos (`clv`, `vwap_dist`).
- A preparação das trajetórias e dos pontos de dispersão do quadrante
  (`build_trajectories`, `max_trajectory_qty`, `point_size`,
  `compute_scatter_data`) vai para `application`, como view-models prontos
  (`PontoQuadrante`).
- As contagens/interpretação/resumo (`count_quadrants`, `pick_interpretation`,
  `generate_summary`) saem para `application`, preservando os mesmos textos.
- A preparação dos dados de VWAP (`to_pct`, `collect_ticker_data`,
  `estimate_bucket_size`, `compute_violin_shapes`) sai de
  `presentation/gui/charts/vwap_data.py` para `application`, como read-model
  pronto (`DadosVwap`/formas de violino).
- `quadrant_chart.py` e `vwap_hist.py` consomem `domain`/`application` e mantêm
  apenas o desenho (dispersão, violinos, hastes, tooltips, toolbar).
- Criação de testes puros em `tests/test_domain` e `tests/test_application`
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
  fronteira), da `VWAPDistanceStrategy` já em `domain` e do padrão de view-model
  aplicado em `refactor-documentos-layers`/`refactor-noticias-layers`.
- **Código movido**: `presentation/gui/charts/quadrant_data.py` e
  `presentation/gui/charts/vwap_data.py` (total); consumo atualizado em
  `quadrant_chart.py` e `vwap_hist.py`.
- **Novos tipos**: `domain` (classificação de quadrante) e `application/*`
  (view-models do quadrante e do VWAP).
- **Testes**: criação de testes puros para as funções movidas; os testes de
  integração/wiring existentes permanecem.
- **Sem alteração de comportamento**: quadrantes, resumo, buckets/violinos,
  tamanhos, cores, rótulos e tooltips permanecem idênticos.
