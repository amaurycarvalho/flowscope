## Context

Ver `proposal.md` — Why, e o contrato em
`openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md`.
Estado atual relevante:

- `presentation/gui/charts/price_range_helpers.py` mistura três
  responsabilidades: classificação (`classify_trend`, `classify_session` e o
  auxiliar `median_value`), normalização/dimensionamento (`normalize`,
  `efficiency_color`, `as_dict`, `size_mapper`, `_constant_size`) e desenho
  (`_scatter_marker`, `render_last_day_markers`, `draw_main_chart`,
  `draw_clv_gauge`, `tooltip_lines`, entre outros).
- `classify_session(daily, range_pct_dict, eff_dict)` lê a última data de
  `daily`, extrai a amplitude e a eficiência correntes e delega a
  `classify_trend`, que aplica os limiares de 0,30 de eficiência e compara a
  amplitude à mediana das amplitudes.
- `price_range_panel.py` apenas orquestra o desenho e usa `as_dict`,
  `draw_clv_gauge`, `draw_main_chart` e `tooltip_lines`.
- `domain/strategies/price.py` já contém as estratégias de indicadores
  (`RangeStrategy`, `TypicalPriceStrategy`, `MedianPriceStrategy`); a
  classificação de pregão é a única regra ainda na UI.
- Não há testes dedicados aos helpers: a apresentação é omitida da cobertura
  (`tool.coverage` omite `presentation/gui/*`).
- A allowlist de fronteira tem 3 entradas legadas sem relação com esta fatia.

## Goals / Non-Goals

**Goals:**

- Colocar a classificação de pregão (`classify_trend`/`classify_session`) em
  `domain`.
- Manter normalização (`normalize`) e dimensionamento (`size_mapper`) em
  `presentation`, junto do desenho.
- Cobrir a classificação movida com testes puros em `tests/test_domain`, sem
  `DISPLAY`.

**Non-Goals:**

- Não mover normalização, cores de eficiência nem o dimensionamento dos
  marcadores (permanecem em `presentation`, conforme o enunciado).
- Não mover o desenho (marcadores, barras, conectores, medidor de CLV, tooltips).
- Não mover as estratégias de indicadores já em `domain`.
- Não alterar a allowlist (a fatia não tem violação `presentation -> infrastructure`).
- Não redesenhar limiares, categorias, cores, rótulos ou textos.

## Decisions

### D1 — Classificação de pregão em `domain`

`classify_trend`, `classify_session` e o auxiliar `median_value` saem de
`price_range_helpers.py` para `domain/strategies/classifiers/session.py`, com
exportação no pacote de classificadores. Alternativa: manter `median_value` em
`presentation` e duplicá-lo. Rejeitada porque `classify_session` depende dele e
`domain` não pode importar `presentation`.

### D2 — `classify_session` opera sobre a data e os mapas de indicadores

Para não acoplar o domínio ao formato do registro diário, a assinatura passa a
ser `classify_session(last_date, range_pct_dict, eff_dict)`; a apresentação
(`draw_classification_text`) extrai `last_date = daily[-1]["date"]` antes de
chamar. O retorno (`None`/categoria) preserva os mesmos casos de indisponibilidade.
Alternativa: manter `daily` na assinatura. Rejeitada por fazer o domínio depender
da estrutura de apresentação.

### D3 — Normalização e dimensionamento permanecem na apresentação

`normalize`, `efficiency_color`, `as_dict`, `size_mapper` e `_constant_size`
ficam em `price_range_helpers.py`, assim como todo o desenho. Alternativa: mover
para `application`. Rejeitada: são formatação/dimensionamento de exibição, não
regra de negócio.

### D4 — Testes puros criados, não migrados

Como não há testes dedicados, cria-se `tests/test_domain/test_session_classification.py`
cobrindo `classify_trend` (as quatro categorias e os limites de 0,30),
`median_value` (ímpar/par) e `classify_session` (ausências, validade e uso da
última data), sem `DISPLAY`. Alternativa: não testar e deixar a cobertura cair.
Rejeitada por violar o orçamento de testes e a meta de cobertura
(`fail_under = 85`).

## Risks / Trade-offs

- [Limites de 0,30] → preservar as comparações `<= 0.30`; cobrir igualdade nos
  testes.
- [Mudança da assinatura de `classify_session`] → atualizar
  `draw_classification_text` e validar paridade com fakes.
- [Código movido sem cobertura] → criar os testes puros na mesma fatia e rodar
  `make test`/`make quality-gate`.
- [Mediana com entradas vazias] → manter o comportamento atual (função só é
  chamada quando há ao menos um percentual).

## Migration Plan

1. Criar a classificação de pregão em `domain` e exportá-la no pacote de
   classificadores.
2. Atualizar `price_range_helpers.py` para importar a classificação de `domain`
   e ajustar `draw_classification_text` (cálculo da última data).
3. Criar os testes puros em `tests/test_domain`.
4. Rodar `make test` e `make quality-gate` (guardrail de fronteira incluso).

Rollback: reverter o change restaura as funções no helper; comportamento
idêntico.

## Open Questions

- Localização da classificação (`domain/strategies/classifiers/session.py` vs
  `domain/price_range.py`) e se `median_value` é exportado publicamente:
  decidir na implementação, sem impacto no contrato.
