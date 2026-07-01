## Why

A atual aba "Amplitude de Preço" exibe apenas texto cru dos indicadores (Range, Typical Price, etc.) sem contexto visual. O usuário não consegue responder rapidamente à pergunta "O preço apenas oscilou ou houve um movimento direcional convincente?". A reformulação transforma dados em percepção visual, seguindo a filosofia do FlowScope de explicar o mercado, não apenas exibir indicadores.

## What Changes

- Substituir o painel textual de "Amplitude de Preço" por um painel visual com quatro componentes gráficos
- Criar o **Price Range Timeline Chart**: gráfico horizontal que posiciona cada pregão em uma linha do eixo Y, normaliza o range [Min, Max] no eixo X (0-100%), e mostra marcadores de referência (Median, Typical, VWAP, Weighted Close) apenas no dia atual, com a trajetória do fechamento (●) conectada por setas entre dias consecutivos
- Adicionar gráfico de linha do **Range % histórico** (30 pregões) para contextualizar a amplitude do dia
- Adicionar **gauge horizontal de Eficiência** (0 a 1) indicando quanto do range virou deslocamento
- Adicionar **gauge horizontal de CLV** (-1 a +1) indicando onde o preço fechou dentro do range
- Incluir **classificação qualitativa** como annotation no gráfico (ex: "Movimento Direcional Forte")
- Atualizar o texto de orientação para guiar a interpretação visual

## Capabilities

### New Capabilities
- `price-range-panel`: Painel visual de amplitude de preço com Price Range Timeline Chart, range% histórico, gauges de eficiência e CLV, e classificação qualitativa

### Modified Capabilities
<!-- Nenhuma — os indicadores (Range, Range%, CLV, Daily Efficiency) já existem e não têm requisitos alterados -->

## Impact

- **Novo arquivo:** `src/flowscope/presentation/gui/charts/price_range_panel.py` (nova classe de chart matplotlib com subplots)
- **Arquivo modificado:** `src/flowscope/presentation/gui/app.py` (habilitar aba, substituir texto por chart, atualizar orientação)
- **Arquivo modificado:** `panels.md` (documentação atualizada)
- Nenhuma dependência nova — todos os indicadores necessários já existem no domain layer
