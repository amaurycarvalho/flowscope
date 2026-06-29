## Why

O FlowScope já calcula todos os indicadores necessários para responder "quem venceu o pregão?" (CLV, Daily Efficiency, Money Flow Volume), mas não possui uma visualização dedicada que traduza esses números em uma resposta intuitiva. O painel "Dominância do Pregão" atual exibe apenas métricas de amplitude de preço (Range, Range%), não a dominância comprador/vendedor. Isso cria uma lacuna entre os dados disponíveis e a percepção do usuário sobre quem controlou o preço em cada sessão.

## What Changes

- **Criar painel "Dominância do Pregão" na aba Análise Geral**: ranking visual de todos os tickers usando CLV do último pregão, com barras horizontais divergentes, classificação qualitativa e círculo indicando Money Flow Volume acumulado.
- **Criar painel "Evolução da Dominância" na aba Análise do Ticker**: gráfico temporal de barras divergentes (um dia por barra) com overlay de Daily Efficiency e círculo indicando Money Flow diário.
- **Renomear aba atual "Dominância do Pregão" para "Amplitude de Preço"** no notebook de Análise do Ticker, pois seu conteúdo atual são indicadores de amplitude (Range, Range%, Typical/Median/Weighted Close).
- **Registrar duas novas strategies no engine**: `daily_money_flow` (MFV por dia, não acumulado) e `dominance_score` (CLV × Daily Efficiency).
- **Criar módulo de classificadores** (`domain/strategies/classifiers/`): `classify_dominance(clv)` e `classify_conviction(efficiency)` com tipagem forte e saída textual + score numérico.
- **Atualizar painel de orientação** com textos de ajuda para os novos painéis.
- **Atualizar `_format_all_indicators`** para incluir `dominance_score` na listagem exibida.

## Capabilities

### New Capabilities
- `dominance-ranking-panel`: Painel de ranking de dominância na aba Análise Geral (barras divergentes, CLV por ticker, último pregão)
- `dominance-timeline-panel`: Painel de evolução temporal da dominância na aba Análise do Ticker (barras divergentes por data, eficiência, MFV diário)
- `dominance-classifiers`: Módulo de classificação qualitativa de dominância e convicção, desacoplado dos cálculos quantitativos

### Modified Capabilities
- `flow-indicators`: Adicionar `daily_money_flow` (MFV por pregão) e `dominance_score` (CLV × Daily Efficiency) como novas strategies registráveis no engine

## Impact

- **`src/flowscope/domain/strategies/`**: 2 novas strategies (`daily_money_flow.py`, `dominance_score.py`), 1 novo subdiretório `classifiers/` com 2 módulos, atualização de `__init__.py` e `domain/indicators.py`
- **`src/flowscope/presentation/gui/charts/`**: 2 novos chart widgets (`dominance_ranking.py`, `dominance_timeline.py`)
- **`src/flowscope/presentation/gui/app.py`**: Adição dos novos sub-tabs, renomeação do tab antigo, atualização de `tab_configs`, `_tab_content`, `_build_main_area`, `_format_all_indicators`, e `_update_charts`
- **`src/flowscope/presentation/gui/widgets/orientation_panel.py`**: Novos textos de orientação
- Nenhuma dependência externa nova; reuso de matplotlib, tkinter, e a infraestrutura de chart widgets já existente (FigureCanvasTkAgg, ToolbarBR)
