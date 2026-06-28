## Purpose

Define the graphical user interface for FlowScope, including the Tkinter main window, notebook-based navigation (Análise Geral / Análise do Ticker), VWAP chart widget, ticker list management, OrientationPanel for explanatory content, and clipboard export.

## Requirements

### Requirement: Navegação por notebook de abas
O sistema DEVE substituir o seletor de visualização por RadioButtons por um ttk.Notebook principal com duas abas: "Análise Geral" e "Análise do Ticker". A aba "Análise Geral" DEVE conter um sub-notebook com as abas "VWAP" (exibe o gráfico de distribuição de preços) e "Quadrantes" (placeholder). A aba "Análise do Ticker" DEVE conter um combobox para seleção de ticker e um sub-notebook com 5 abas placeholder: "Dominância do Pregão", "Fluxo Financeiro", "Participação Institucional", "Eficiência do Movimento" e "Resumo Geral".

#### Scenario: Navegação entre abas principais
- **WHEN** o usuário clica na aba "Análise Geral"
- **THEN** o sistema DEVE exibir o sub-notebook com as abas "VWAP" e "Quadrantes"

#### Scenario: Navegação para análise de ticker
- **WHEN** o usuário clica na aba "Análise do Ticker"
- **THEN** o sistema DEVE exibir o combobox de seleção de ticker e o sub-notebook com as 5 sub-abas placeholder

### Requirement: OrientationPanel para conteúdo explicativo
O sistema DEVE exibir um OrientationPanel na barra lateral direita contendo título e texto explicativo fixo associado à sub-aba ativa. Cada sub-aba DEVE ter seu próprio conteúdo explicativo (objetivo, indicadores envolvidos, como interpretá-lo).

#### Scenario: OrientationPanel atualizado ao trocar sub-aba
- **WHEN** o usuário seleciona a sub-aba "VWAP"
- **THEN** o OrientationPanel DEVE exibir o título "VWAP — Volume Weighted Average Price" e o texto explicativo correspondente

### Requirement: Gráfico de distribuição de preços VWAP
O sistema DEVE exibir um violin plot horizontal com o ticker no eixo X e o valor do TradAvrgPric no eixo Y. A largura do violino em cada faixa de preço DEVE ser proporcional à soma de FinInstrmQty para aquele ticker em todo o período. Sobreposto ao violin plot, DEVE haver:
- Um errorbar exibindo o VWAP geral como ponto central, o menor MinPric do período como limite inferior e o maior MaxPric como limite superior
- Um scatter plot destacando o LastPric de cada ticker referente à data mais recente do período

#### Scenario: Exibição do violin plot com errorbar e scatter
- **WHEN** dados de múltiplos tickers são carregados e a sub-aba VWAP está selecionada
- **THEN** o sistema DEVE exibir um violin plot horizontal com perfil de volume (largura ∝ Σ FinInstrMty por bucket de preço), errorbar (VWAP, MinPric, MaxPric) e scatter (LastPric da data mais recente)

#### Scenario: Ticker com dados de um único dia
- **WHEN** um ticker possui dados em apenas 1 dia
- **THEN** o violin plot DEVE exibir uma forma estreita centrada no TradAvrgPric, com errorbar mostrando VWAP = TradAvrgPric e MinPric = MaxPric

#### Scenario: Sem dados para exibir
- **WHEN** não há dados carregados ou o filtro resulta em lista vazia
- **THEN** o sistema DEVE exibir uma mensagem "Nenhum ticker corresponde ao filtro."

### Requirement: Contagem de tickers
O sistema DEVE exibir um label ao lado do campo de tickers indicando a quantidade total carregada "Tickers (N)" e, quando filtrado, "Exibindo M de N ativos".

#### Scenario: Label atualizado após carregamento
- **WHEN** dados de 37 tickers são carregados
- **THEN** o label DEVE mostrar "Tickers (37)"

#### Scenario: Label atualizado após filtro
- **WHEN** o usuário filtra para 15 de 37 tickers
- **THEN** o label DEVE mostrar "Exibindo 15 de 37 ativos"

### Requirement: Ícone da aplicação na janela
O sistema DEVE carregar e exibir o ícone da aplicação na barra de título e barra de tarefas.

#### Scenario: Ícone carregado no Linux
- **WHEN** o aplicativo inicia no Linux e `flowscope.png` existe em `src/flowscope/icons/`
- **THEN** a janela DEVE usar `self.wm_iconphoto(True, tk.PhotoImage(file=path))`

#### Scenario: Ícone carregado no Windows
- **WHEN** o aplicativo inicia no Windows e `flowscope.ico` existe em `src/flowscope/icons/`
- **THEN** a janela DEVE usar `self.iconbitmap(path)`

### Requirement: Botão "Hoje" carrega dados automaticamente

O sistema DEVE, ao clicar no botão "Hoje", atualizar o DateEntry para a data atual E executar imediatamente o carregamento de dados (mesma ação do botão "Carregar"), como se o usuário tivesse clicado em "Carregar" em sequência.

#### Scenario: Clique no botão Hoje carrega dados do dia
- **WHEN** o usuário clica no botão "Hoje"
- **THEN** o DateEntry DEVE ser atualizado para a data atual E os dados DEVEM ser carregados para essa data, com o mesmo comportamento (loading state, statusbar, gráficos) do botão "Carregar"

### Requirement: Preenchimento automático com IDIV quando filtro vazio

O sistema DEVE, quando o campo de filtro de tickers estiver vazio e o usuário pressionar "Carregar", buscar automaticamente a carteira do IDIV e preencher o campo com os tickers do índice. O carregamento de dados DEVE então prosseguir usando essa lista como filtro.

#### Scenario: Carregar com filtro vazio
- **WHEN** o campo de tickers está vazio e o usuário clica em "Carregar"
- **THEN** o sistema DEVE buscar a carteira IDIV, preencher o campo de tickers com os tickers obtidos, e carregar os dados filtrando apenas por esses tickers

#### Scenario: Erro na busca IDIV com filtro vazio
- **WHEN** o campo de tickers está vazio, o usuário clica em "Carregar", e a busca do IDIV falha
- **THEN** o sistema DEVE exibir uma mensagem de erro e NÃO DEVE carregar dados

#### Scenario: Filtro já preenchido mantém comportamento atual
- **WHEN** o campo de tickers contém tickers e o usuário clica em "Carregar"
- **THEN** o sistema DEVE usar os tickers existentes no campo, sem buscar o IDIV
