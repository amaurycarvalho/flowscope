## Why

Os gráficos do FlowScope atualmente são estáticos — não há zoom, pan, reset ou qualquer forma de inspecionar coordenadas dos pontos. O usuário também não tem um atalho rápido para voltar à data atual no DateEntry. Isso limita a análise exploratória dos dados de fluxo de ordens, especialmente no scatter plot VWAP × CVD onde a visualização de coordenadas exatas é essencial para tomada de decisão.

## What Changes

- Adicionar botão "Hoje" na barra superior para resetar o DateEntry para a data atual
- Adicionar NavigationToolbar2TK (toolbox) em cada chart com zoom, pan, reset, e save — com labels em português
- Adicionar hover tooltip no scatter plot mostrando ticker, VWAP, CVD e volume ao passar o mouse
- Adicionar hover tooltip no CVD histogram mostrando valor exato do CVD por barra
- Adicionar hover tooltip no VWAP histogram mostrando faixa de preço e volume do bucket

## Capabilities

### New Capabilities
- `chart-interactivity`: Interactive chart controls (toolbox com zoom/pan/reset/save), hover tooltips com coordenadas X/Y nos gráficos, e botão de navegação rápida "Hoje" no DateEntry

### Modified Capabilities
<!-- Nenhuma — os requisitos existentes continuam válidos, estamos adicionando comportamentos novos -->

## Impact

- **Target**: Release 0.1.0
- `src/flowscope/presentation/gui/app.py`: Adicionar botão "Hoje" na top bar, lógica de retarget de toolbar ao trocar de chart
- `src/flowscope/presentation/gui/charts/scatter.py`: Adicionar NavigationToolbar2Tk e hover tooltip com coordenadas X/Y
- `src/flowscope/presentation/gui/charts/cvd_hist.py`: Adicionar NavigationToolbar2Tk e hover tooltip com valor do CVD
- `src/flowscope/presentation/gui/charts/vwap_hist.py`: Adicionar NavigationToolbar2Tk e hover tooltip com faixa de preço
- Nenhuma nova dependência externa (NavigationToolbar2Tk é parte do matplotlib, tooltips via matplotlib events)
