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
O sistema DEVE exibir um OrientationPanel na barra lateral direita contendo título e texto explicativo fixo associado à sub-aba ativa. Cada sub-aba DEVE ter seu próprio conteúdo explicativo composto por (objetivo, pergunta respondida, indicadores envolvidos, como interpretá-lo), nesta ordem. O texto explicativo DEVE suportar formatação rica nativa: cabeçalhos de seção (Objetivo, Responde a pergunta, Indicadores envolvidos, Como interpretar) em **negrito** e perguntas em itálico. O método `set_content(title, body)` DEVE aceitar `body` como uma lista de tuplas `(str, str)` onde o segundo elemento é o nome da tag de formatação.

#### Scenario: OrientationPanel atualizado ao trocar sub-aba
- **WHEN** o usuário seleciona a sub-aba "VWAP"
- **THEN** o OrientationPanel DEVE exibir o título "VWAP — Volume Weighted Average Price" e o texto explicativo correspondente, contendo os campos Objetivo, Responde a pergunta, Indicadores envolvidos e Como interpretar, nesta ordem

#### Scenario: OrientationPanel da sub-aba VWAP contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "VWAP"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _Quem está acima do preço justo e quem está abaixo?_"

#### Scenario: OrientationPanel da sub-aba Quadrantes contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Quadrantes"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _Quem dominou o fechamento?_"

#### Scenario: OrientationPanel da sub-aba Dominância do Pregão contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Dominância do Pregão"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _Quem venceu a disputa diária pelo preço?_"

#### Scenario: OrientationPanel da sub-aba Evolução da Dominância contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Evolução da Dominância"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _Quem venceu a disputa diária pelo preço?_"

#### Scenario: OrientationPanel da sub-aba Amplitude de Preço contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Amplitude de Preço"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta" seguido da pergunta sobre movimento direcional e evolução do fechamento

#### Scenario: OrientationPanel da sub-aba Fluxo Financeiro contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _O movimento ocorreu com dinheiro ou apenas por falta de liquidez?_"

#### Scenario: OrientationPanel da sub-aba Participação Institucional contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Participação Institucional"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _Quem parece estar negociando? Grandes participantes ou varejo?_"

#### Scenario: OrientationPanel da sub-aba Eficiência do Movimento contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Eficiência do Movimento"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _O mercado caminhou com convicção ou apenas oscilou?_"

#### Scenario: OrientationPanel da sub-aba Resumo Geral contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Resumo Geral"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _O que realmente aconteceu neste ativo?_"

#### Scenario: OrientationPanel exibe texto com formatação
- **WHEN** o usuário seleciona a sub-aba "VWAP"
- **THEN** o OrientationPanel DEVE exibir "Objetivo:" em **negrito**, a pergunta em itálico, e os demais textos sem formatação especial

#### Scenario: set_content aceita lista de tuplas
- **WHEN** o sistema chama `set_content("Título", [("Objetivo: ", "bold"), ("texto plano", "")])`
- **THEN** o OrientationPanel DEVE exibir "Objetivo:" em negrito e "texto plano" sem formatação

### Requirement: Formatação via tags tk.Text
O OrientationPanel DEVE configurar duas tags no widget `tk.Text`: `"bold"` (fonte TkDefaultFont 9 bold) e `"italic"` (fonte TkDefaultFont 9 italic). Tags DEVEM ser aplicadas conforme o nome da tag em cada tupla do body.

#### Scenario: Tag bold aplicada a cabeçalhos
- **WHEN** o body contém `("Objetivo: ", "bold")`
- **THEN** o texto "Objetivo:" DEVE ser exibido em negrito

#### Scenario: Tag italic aplicada a perguntas
- **WHEN** o body contém `("pergunta", "italic")`
- **THEN** o texto "pergunta" DEVE ser exibido em itálico

#### Scenario: Tag vazia não aplica formatação
- **WHEN** o body contém `("texto plano", "")`
- **THEN** o texto DEVE ser exibido sem formatação especial

### Requirement: Gráfico de distribuição de preços VWAP
O sistema DEVE exibir um violin plot horizontal com o ticker no eixo X e o valor do desvio percentual do TradAvrgPric em relação ao VWAP no eixo Y, calculado como `(TradAvrgPric - VWAP) / VWAP × 100`. A largura do violino em cada faixa DEVE ser proporcional à soma de FinInstrmQty para aquele ticker em todo o período. Sobreposto ao violin plot, DEVE haver:
- Uma barra vertical (`vlines`) do menor MinPric ao maior MaxPric, normalizados pelo VWAP, com um marcador em 0% indicando o VWAP
- Um scatter plot destacando o LastPric de cada ticker normalizado pelo VWAP, referente à data mais recente do período
- Uma linha horizontal tracejada em Y = 0% representando o VWAP

O eixo Y DEVE exibir o rótulo "Diferença do VWAP (%)" e os limites DEVEM ser simétricos em torno de 0%.

#### Scenario: Exibição do violin plot com eixo normalizado
- **WHEN** dados de múltiplos tickers são carregados e a sub-aba VWAP está selecionada
- **THEN** o sistema DEVE exibir um violin plot horizontal com perfil de volume (largura ∝ Σ FinInstrMty por bucket), barra vertical vlines (MinPric–MaxPric normalizados, marcador VWAP em 0%), scatter (LastPric normalizado), e linha tracejada em Y = 0%

#### Scenario: Ticker com dados de um único dia
- **WHEN** um ticker possui dados em apenas 1 dia
- **THEN** o violin plot DEVE exibir uma forma estreita centrada em 0% (TradAvrgPric = VWAP), com barra vertical mostrando MinPric = MaxPric normalizados e VWAP = TradAvrgPric em 0%

#### Scenario: Sem dados para exibir
- **WHEN** não há dados carregados ou o filtro resulta em lista vazia
- **THEN** o sistema DEVE exibir uma mensagem "Nenhum ticker corresponde ao filtro."

### Requirement: Contagem de tickers
O sistema DEVE exibir um label ao lado do campo de tickers indicando a quantidade total ou selecionada, dependendo do modo atual:
- Modo visualização: "Tickers (N)" com N = total de tickers no Listbox; "Exibindo M de N ativos" quando M < N selecionados
- Modo edição: "Tickers (N)" com N = total de tickers no Text widget

#### Scenario: Label no modo visualização com todos marcados
- **WHEN** dados de 37 tickers são carregados e todos estão marcados no Listbox
- **THEN** o label DEVE mostrar "Tickers (37)"

#### Scenario: Label no modo visualização com seleção parcial
- **WHEN** o usuário desmarca 10 dos 37 tickers no Listbox
- **THEN** o label DEVE mostrar "Exibindo 27 de 37 ativos"

#### Scenario: Label no modo edição
- **WHEN** o usuário alterna para modo edição com 37 tickers carregados
- **THEN** o label DEVE mostrar "Tickers (37)"

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

### Requirement: OrientationPanel atualizado com novos indicadores

O OrientationPanel DEVE exibir conteúdo explicativo para cada novo indicador à medida que as sub-abas são implementadas, seguindo o mesmo padrão existente (título + texto explicativo + interpretação).

#### Scenario: OrientationPanel para Dominância do Pregão

- **WHEN** o usuário seleciona a sub-aba "Dominância do Pregão"
- **THEN** o OrientationPanel DEVE exibir título e texto explicativo sobre Range, Range%, Typical Price, Median Price e Weighted Close

#### Scenario: OrientationPanel para Fluxo Financeiro

- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o OrientationPanel DEVE exibir título e texto explicativo sobre CLV, Money Flow Volume, Buying Pressure e Selling Pressure

### Requirement: Exposição dos resultados do engine DAG para a GUI

O sistema DEVE expor os resultados completos do `IndicatorEngine.execute()` para que os widgets da GUI possam consumir qualquer indicador pelo seu `id`.

#### Scenario: Consumo de indicador pela GUI

- **WHEN** o engine retorna resultados com `results["clv"]["PETR4"]` contendo dados de CLV
- **THEN** o widget da sub-aba "Fluxo Financeiro" DEVE acessar `results["clv"]` para exibir o CLV do ticker selecionado

### Requirement: Botões de índice IBOV, IDIV e IFIX

O sistema DEVE exibir três botões — "IBOV", "IDIV" e "IFIX" — na barra superior do TickerList, após um separador vertical do grupo de seleção (Editar, Selecionar Todos, Desmarcar Todos). Cada botão, quando pressionado, DEVE baixar a carteira teórica diária do respectivo índice via API B3 e **substituir** o conteúdo do Listbox pelos tickers obtidos.

#### Scenario: Botão IBOV carrega carteira do IBOV
- **WHEN** o usuário clica no botão "IBOV"
- **THEN** o sistema DEVE baixar a carteira do IBOV e preencher o campo de tickers com os tickers obtidos

#### Scenario: Botão IFIX carrega carteira do IFIX
- **WHEN** o usuário clica no botão "IFIX"
- **THEN** o sistema DEVE baixar a carteira do IFIX e preencher o campo de tickers com os tickers obtidos

#### Scenario: Falha no download de um índice
- **WHEN** o usuário clica em um botão de índice e o download falha
- **THEN** o sistema DEVE exibir uma mensagem de erro na barra de status e NÃO DEVE alterar o campo de tickers

### Requirement: Preenchimento automático com IDIV quando lista vazia (modificado)

O sistema DEVE, quando a lista de tickers estiver vazia e o usuário pressionar "Carregar", buscar automaticamente a carteira do **IDIV** e preencher o Listbox com os tickers do índice. Esta lógica DEVE usar o mesmo mecanismo interno do botão "IDIV".

#### Scenario: Carregar com lista vazia
- **WHEN** a lista de tickers está vazia e o usuário clica em "Carregar"
- **THEN** o sistema DEVE buscar a carteira IDIV (via `_fill_with_index("IDIV")`), preencher o Listbox com os tickers obtidos, selecionar todos, e carregar os dados

#### Scenario: Erro na busca IDIV com lista vazia
- **WHEN** a lista de tickers está vazia, o sistema tenta buscar IDIV, e a busca falha
- **THEN** o sistema DEVE exibir uma mensagem de erro e NÃO DEVE carregar dados

#### Scenario: Lista já preenchida mantém comportamento atual
- **WHEN** a lista de tickers contém tickers e o usuário clica em "Carregar"
- **THEN** o sistema DEVE usar todos os tickers existentes no Listbox, sem buscar o IDIV

### Requirement: Comboboxes de ticker da Análise Geral removidos
Os comboboxes de seleção de ticker nas abas VWAP, Quadrantes e Dominância do Pregão foram removidos. A seleção de tickers é feita exclusivamente pelo Listbox no TickerList. Todos os gráficos da Análise Geral usam os tickers selecionados no Listbox.

A regra de exibição de setas (quiver) no gráfico de Quadrantes é mantida: setas são exibidas quando apenas 1 ticker está selecionado no Listbox.

#### Scenario: VWAP exibe todos os tickers selecionados
- **WHEN** o usuário seleciona 5 tickers no Listbox e navega para a aba VWAP
- **THEN** o histograma VWAP DEVE exibir dados para todos os 5 tickers

#### Scenario: Quadrantes com setas quando 1 ticker selecionado
- **WHEN** o usuário seleciona exatamente 1 ticker no Listbox e navega para a aba Quadrantes
- **THEN** o gráfico de quadrantes DEVE exibir setas (quiver) para o ticker selecionado

#### Scenario: Quadrantes sem setas quando múltiplos tickers
- **WHEN** o usuário seleciona 3 tickers no Listbox e navega para a aba Quadrantes
- **THEN** o gráfico de quadrantes DEVE exibir pontos sem setas

### Requirement: Carga de dados usa todos os tickers da lista
O método `_ensure_tickers()` DEVE usar `get_all_listbox_tickers()` para obter a lista completa de tickers, independentemente de quais estão marcados. A marcação no Listbox só afeta a exibição nos painéis, não a carga de dados.

#### Scenario: Carga com tickers desmarcados
- **WHEN** o usuário tem 30 tickers no Listbox, desmarca 10, e clica em "Carregar"
- **THEN** os dados DEVEM ser carregados para todos os 30 tickers (não apenas os 20 marcados)
