## Why

A fatia de Amplitude de Preço mantém em `presentation` a classificação de
pregão (`price_range_helpers.classify_trend`/`classify_session`), uma regra de
domínio que combina amplitude relativa e eficiência diária. Como consequência, a
decisão de classificação reside na UI e as funções puras ficam sem testes fora da
apresentação. Esta fatia move a classificação de pregão para `domain`, deixando a
normalização e o dimensionamento dos marcadores na apresentação.

## What Changes

- A classificação `classify_trend` e `classify_session` (com o auxiliar
  `median_value` usado pela segunda) sai de
  `presentation/gui/charts/price_range_helpers.py` para `domain`, preservando as
  mesmas categorias (`Pregão Lateral`, `Volatilidade sem Direção`,
  `Movimento Consistente`, `Movimento Direcional Forte`).
- `normalize`, `efficiency_color`, `size_mapper`/`_constant_size` e o desenho
  (`draw_*`, `render_last_day_markers`, `tooltip_lines`) permanecem em
  `presentation`.
- `price_range_helpers.py` passa a importar `classify_session` do `domain` em
  `draw_classification_text`, sem duplicar a regra.
- Criação de testes puros em `tests/test_domain` para a classificação movida
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
  fronteira) e do padrão de classificação já aplicado em
  `refactor-quadrant-vwap-layers`/`refactor-noticias-layers`.
- **Código movido**: `classify_trend`/`classify_session`/`median_value` de
  `presentation/gui/charts/price_range_helpers.py` para `domain`.
- **Testes**: criação de testes puros para a classificação movida; os testes de
  integração/wiring existentes permanecem.
- **Sem alteração de comportamento**: categorias, limiares (0,30), mediana,
  normalização, tamanhos, cores, rótulos e tooltips permanecem idênticos.
