## Why

A fatia da Rede de Correlação mantém em `presentation` um módulo puro,
`presentation/gui/charts/network_data.py`, que interpreta estruturas brutas
(`_current_data`/`daily_data`) para extrair as séries `(data, last_price)` e
decidir rótulos e mensagens de estado vazio. Como consequência, os 129 testes
puros de mapeamento (`test_network_data.py`) ficam na apresentação, e o painel
recalcula o view-model a partir das estruturas de domínio. Esta fatia move a
extração de séries e o read-model de exibição para `application`, deixando o
painel apenas desenhar.

## What Changes

- O módulo puro `presentation/gui/charts/network_data.py` (`DadosRede`,
  `extrair_series`, as mensagens `MENSAGEM_SEM_TICKERS`/`MENSAGEM_POUCAS_OBS`/
  `AVISO_COINT_INDISPONIVEL` e os formatadores/rótulos `formatar_correlacao`,
  `formatar_half_life`, `formatar_modularidade`, `rotulo_diagnostico`,
  `mensagem_indisponivel`) sai de `presentation` para `application/network/`,
  como read-model pronto.
- `correlation_network_panel.py` consome o read-model de `application` e
  permanece apenas com o desenho (grafo, colorbar, legenda, estado vazio).
- Migração dos testes puros de `tests/test_presentation/test_network_data.py`
  para `tests/test_application`; o painel mantém apenas testes de UI
  (`needs_display`).
- Sem alteração da allowlist de fronteira: a fatia não importa
  `infrastructure`; o ganho é de convenção de view-model e do orçamento de
  testes de UI.

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
- **Código movido**: `presentation/gui/charts/network_data.py`; consumo
  atualizado em `presentation/gui/charts/correlation_network_panel.py`.
- **Novos tipos**: `application/network/*` (read-model de séries e rótulos).
- **Testes migrados**: os 129 testes puros de `test_network_data.py` vão para
  `tests/test_application`; o painel fica com o subconjunto de `needs_display`
  (desenho, estado vazio, colorbar, toolbar).
- **Sem alteração de comportamento**: séries, valores, rótulos, mensagens e
  ordem de exibição permanecem idênticos.
