## ADDED Requirements

### Requirement: Janela principal Tkinter
O sistema DEVE fornecer uma interface gráfica usando Tkinter acessível via `--gui`, com todos os widgets e gráficos especificados.

#### Scenario: Abertura da GUI
- **WHEN** o usuário executa `flowscope --gui`
- **THEN** uma janela Tkinter DEVE abrir com título "FlowScope" e dimensões adequadas para exibição dos gráficos (mínimo 1024x768)

### Requirement: Seleção de data de referência com calendário
O sistema DEVE fornecer um campo de seleção de data usando tkcalendar.DateEntry, com data padrão igual ao dia atual.

#### Scenario: Alteração da data de referência
- **WHEN** o usuário seleciona uma nova data no calendário
- **THEN** o sistema DEVE recalcular a janela Fibonacci, refazer download se necessário e atualizar todos os gráficos e indicadores

### Requirement: Gráfico histograma VWAP por ticker
O sistema DEVE exibir um gráfico de barras (histograma) com os valores de VWAP para cada ticker, usando matplotlib embutido em frame Tkinter.

#### Scenario: Exibição do histograma VWAP
- **WHEN** os dados são carregados e processados
- **THEN** um gráfico de barras DEVE mostrar o VWAP de cada ticker selecionado, com eixo Y representando preço e eixo X com os códigos dos tickers

### Requirement: Gráfico histograma CVD por ticker
O sistema DEVE exibir um gráfico de barras (histograma) com os valores de CVD para cada ticker, usando matplotlib embutido em frame Tkinter.

#### Scenario: Exibição do histograma CVD
- **WHEN** os dados são carregados e processados
- **THEN** um gráfico de barras DEVE mostrar o CVD de cada ticker selecionado, com barras positivas em verde e negativas em vermelho

### Requirement: Gráfico de dispersão VWAP × CVD
O sistema DEVE exibir um scatter plot com VWAP no eixo X e CVD no eixo Y, onde cada ponto representa um ticker. O tamanho e/ou cor dos marcadores DEVE variar conforme uma terceira variável (ex: volume financeiro).

#### Scenario: Scatter plot com marcadores proporcionais ao volume
- **WHEN** os dados são carregados
- **THEN** cada ticker DEVE aparecer como um ponto no gráfico com tamanho proporcional ao NtlFinVol e cor variando conforme o quadrante

#### Scenario: Checkbox quiver temporal
- **WHEN** o usuário marca o checkbox "Exibir setas temporais"
- **THEN** setas quiver DEVEM ser adicionadas ao scatter plot conectando cada ticker à sua posição no dia anterior (d-1), indicando a trajetória temporal

#### Scenario: Checkbox quiver desmarcado
- **WHEN** o usuário desmarca o checkbox "Exibir setas temporais"
- **THEN** as setas quiver DEVEM ser removidas do gráfico, mantendo apenas os pontos do scatter

### Requirement: Campo multilinha de seleção de tickers
O sistema DEVE fornecer um campo de texto multilinha onde o usuário pode editar a lista de tickers (um por linha), com padrão sendo os 15 de maior volume.

#### Scenario: Edição manual da lista
- **WHEN** o usuário digita tickers no campo texto (um por linha)
- **THEN** o sistema DEVE atualizar os gráficos para refletir apenas os tickers listados

### Requirement: Botão salvar lista de tickers
O sistema DEVE fornecer um botão para salvar a lista atual de tickers do campo texto em um arquivo `.txt`.

#### Scenario: Salvar lista de tickers
- **WHEN** o usuário clica no botão "Salvar Tickers"
- **THEN** um diálogo de salvamento DEVE abrir e o arquivo `.txt` DEVE ser salvo com um ticker por linha

### Requirement: Botão carregar lista de tickers
O sistema DEVE fornecer um botão para carregar uma lista de tickers de um arquivo `.txt` para o campo texto.

#### Scenario: Carregar lista de tickers
- **WHEN** o usuário clica no botão "Carregar Tickers" e seleciona um arquivo `.txt`
- **THEN** o campo de texto DEVE ser preenchido com os tickers do arquivo (um por linha) e os gráficos atualizados

### Requirement: Botão copiar dados CSV para clipboard
O sistema DEVE fornecer um botão que copia os dados dos indicadores (CVD e VWAP) em formato CSV para o clipboard do sistema.

#### Scenario: Copiar dados para clipboard
- **WHEN** o usuário clica no botão "Copiar Dados"
- **THEN** os dados DEVEM ser formatados como CSV e transferidos para o clipboard via pyxclip

### Requirement: Botão copiar gráfico para clipboard
O sistema DEVE fornecer um botão que copia o gráfico atualmente visível como imagem PNG para o clipboard do sistema.

#### Scenario: Copiar gráfico como imagem
- **WHEN** o usuário clica no botão "Copiar Gráfico"
- **THEN** a figura matplotlib ativa DEVE ser renderizada como PNG e transferida para o clipboard usando comandos nativos da plataforma

### Requirement: Campo readonly para análise automática
O sistema DEVE fornecer um campo de texto readonly que servirá como placeholder para o futuro motor de inferência. Inicialmente DEVE exibir uma mensagem como "Análise automática será implementada em versão futura."

#### Scenario: Exibição do placeholder de análise
- **WHEN** a GUI é aberta
- **THEN** o campo de análise DEVE estar visível, readonly, com o texto placeholder informando que o motor de inferência ainda não está disponível
