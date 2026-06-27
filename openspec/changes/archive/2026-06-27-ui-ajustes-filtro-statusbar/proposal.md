## Why

A barra de status estava posicionada acima dos botões de ação, e o campo de texto dos tickers aplicava filtro automaticamente a cada tecla pressionada, causando recálculos desnecessários e travamento da interface durante a digitação.

## What Changes

- Mover a barra de status para abaixo dos botões "Copiar Dados" e "Copiar Gráfico"
- Adicionar botão "Filtrar" ao lado de "Salvar Tickers" e "Carregar Tickers"
- Remover o filtro automático ao digitar (evento KeyRelease) e ao carregar arquivo
- O filtro só é aplicado quando o botão "Filtrar" é pressionado manualmente

## Capabilities

### Modified Capabilities

- `gui-interface`: comportamento do filtro de tickers alterado — de automático para manual via botão "Filtrar"

## Impact

- `src/flowscope/presentation/gui/app.py`: ordem da barra de status e ação do filtro
- `src/flowscope/presentation/gui/widgets/ticker_list.py`: remoção do evento KeyRelease, remoção do auto-filtro no carregamento, adição do botão "Filtrar"
