## Purpose

Define the graphical user interface for FlowScope, including the Tkinter main window, chart widgets (VWAP histogram, CVD histogram, scatter plot with temporal arrows), ticker list management, and clipboard export.

## Requirements

### Requirement: Gráfico de dispersão VWAP × CVD
O sistema DEVE exibir um scatter plot com VWAP no eixo X e CVD no eixo Y, onde cada ponto representa um ticker. O tamanho dos marcadores DEVE variar conforme o volume financeiro (NtlFinVol) e a cor por quadrante. O checkbox "Exibir setas temporais" DEVE desenhar setas conectando a posição de cada ticker no dia anterior (d-1) à sua posição no dia atual (d), indicando a trajetória temporal.

#### Scenario: Checkbox quiver temporal marcado
- **WHEN** o usuário marca o checkbox "Exibir setas temporais"
- **THEN** setas DEVEM ser desenhadas no scatter plot conectando a posição (VWAP, CVD) de cada ticker em d-1 à sua posição em d, com setas indicando a direção

### Requirement: Campo multilinha de seleção de tickers
O sistema DEVE fornecer um campo de texto multilinha onde o usuário pode editar a lista de tickers (um por linha). Alterações no campo DEVE automaticamente atualizar os gráficos. O botão "Carregar Tickers" também DEVE atualizar os gráficos após carregar a lista.

#### Scenario: Edição manual da lista atualiza gráficos
- **WHEN** o usuário digita ou apaga tickers no campo texto
- **THEN** os gráficos DEVEM ser atualizados automaticamente para refletir apenas os tickers presentes no campo

#### Scenario: Carregar tickers de arquivo atualiza gráficos
- **WHEN** o usuário clica em "Carregar Tickers" e seleciona um arquivo
- **THEN** os gráficos DEVEM ser atualizados automaticamente para refletir os tickers carregados
