## Why

O painel de fluxo financeiro mantém em `presentation` a extração das métricas do
último pregão (`financial_flow_helpers.extract_session_metrics`), o cálculo dos
percentuais de pressão (`pressure_percentages`) e a geração do resumo textual
(`generate_summary` e seus trechos). Como consequência, a UI lê
`all_indicators`/`daily_data`/`money_flow_volume` brutos e reinterpreta regras de
domínio, e essas funções puras ficam sem testes fora da apresentação. Esta fatia
move a extração de métricas e o resumo para `application` e a normalização das
pressões para `domain`, deixando a apresentação apenas formatar e desenhar.

## What Changes

- `extract_session_metrics` sai de
  `presentation/gui/charts/financial_flow_helpers.py` para `application/flow/`,
  como view-model pronto (`SessionFlowMetrics` + `build_session_metrics`).
- `generate_summary` e os trechos `flow_intensity_part`, `close_position_part`,
  `dominance_part` e `conviction_part` saem do helper para `application/flow/`,
  gerando o resumo textual a partir das métricas já preparadas.
- `pressure_percentages` sai do helper para `domain` (regra pura de normalização
  das pressões de compra e venda sobre o total).
- `financial_flow_helpers.py` permanece com a formatação
  (`format_accumulated_mfv`, `format_dmf_value`, `format_dmf_text`), o desenho
  (`draw_card`, `draw_clv_bar`, `draw_pressure_labels`, `draw_bs_bar`) e o
  tooltip (`tooltip_lines`), consumindo `domain`/`application`.
- `financial_flow_panel.py` passa a consumir os view-models e o resumo de
  `application` e mantém apenas a orquestração/desenho.
- Criação de testes puros em `tests/test_application` e `tests/test_domain` para
  as funções movidas (não havia testes dedicados), sem `DISPLAY`.
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
  `refactor-dominance-panels-layers`/`refactor-quadrant-vwap-layers`.
- **Código movido**: funções puras de
  `presentation/gui/charts/financial_flow_helpers.py`; consumo atualizado em
  `financial_flow_panel.py`.
- **Novos módulos/tipos**: `application/flow/` (view-model de métricas do pregão
  e resumo textual) e `domain/strategies/pressure.py` (normalização das
  pressões).
- **Testes**: criação de testes puros para as funções movidas; os testes de
  integração/wiring existentes permanecem.
- **Sem alteração de comportamento**: métricas, percentuais, resumo textual,
  rótulos, cores e tooltips permanecem idênticos.
