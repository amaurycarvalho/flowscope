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

#### Scenario: OrientationPanel da sub-aba Fluxo Financeiro contém a pergunta atualizada
- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _O movimento de hoje foi sustentado por fluxo financeiro?_"

#### Scenario: OrientationPanel da sub-aba Fluxo Financeiro contém indicadores atualizados
- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o texto do OrientationPanel DEVE conter "Daily Money Flow (DMF)" e "Money Flow Volume acumulado"

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

O sistema DEVE exibir três botões — "IBOV", "IDIV" e "IFIX" — na barra superior do TickerList, após um separador vertical do grupo de seleção (Editar, Selecionar Todos, Desmarcar Todos). Cada botão, quando pressionado, DEVE baixar a carteira teórica diária do respectivo índice via API B3 e **substituir** o conteúdo do Listbox pelos tickers obtidos. Durante todo o processo de download e análise, todos os botões da aplicação DEVEM ser desabilitados e restaurados ao estado anterior ao finalizar (conforme especificado em `loading-state-management`).

#### Scenario: Botão IBOV carrega carteira do IBOV com loading state
- **WHEN** o usuário clica no botão "IBOV"
- **THEN** o sistema DEVE desabilitar todos os botões, baixar a carteira do IBOV, preencher o campo de tickers com os tickers obtidos, processar os dados, e restaurar os botões ao estado anterior

#### Scenario: Botão IFIX carrega carteira do IFIX com loading state
- **WHEN** o usuário clica no botão "IFIX"
- **THEN** o sistema DEVE desabilitar todos os botões, baixar a carteira do IFIX, preencher o campo de tickers com os tickers obtidos, processar os dados, e restaurar os botões ao estado anterior

#### Scenario: Falha no download de um índice
- **WHEN** o usuário clica em um botão de índice, o download falha, e a lista de tickers NÃO é alterada
- **THEN** o sistema DEVE exibir uma mensagem de erro na barra de status e restaurar os botões ao estado anterior

### Requirement: Preenchimento automático com IDIV quando lista vazia

O sistema DEVE, quando a lista de tickers estiver vazia e o usuário pressionar "Carregar", buscar automaticamente a carteira do **IDIV** e preencher o Listbox com os tickers do índice. Durante esta operação, todos os botões DEVEM ser desabilitados.

#### Scenario: Carregar com lista vazia desabilita botões
- **WHEN** a lista de tickers está vazia e o usuário clica em "Carregar"
- **THEN** o sistema DEVE desabilitar todos os botões, buscar a carteira IDIV, preencher o Listbox com os tickers obtidos, selecionar todos, carregar os dados, e restaurar os botões

#### Scenario: Erro na busca IDIV com lista vazia restaura botões
- **WHEN** a lista de tickers está vazia, o sistema tenta buscar IDIV, a busca falha, e NÃO carrega dados
- **THEN** o sistema DEVE exibir uma mensagem de erro e restaurar os botões ao estado anterior

#### Scenario: Lista já preenchida mantém loading state
- **WHEN** a lista de tickers contém tickers e o usuário clica em "Carregar"
- **THEN** o sistema DEVE desabilitar todos os botões, carregar os dados para todos os tickers existentes no Listbox, e restaurar os botões ao finalizar

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

### Requirement: Sub-aba Fluxo Financeiro ativa com painel visual

O sistema DEVE ativar a sub-aba "Fluxo Financeiro" (removendo-a do conjunto de abas desabilitadas) e exibir o `FinancialFlowPanel` no lugar do placeholder `tk.Text`.

#### Scenario: Fluxo Financeiro selecionável
- **WHEN** o usuário navega para a aba "Análise do Ticker"
- **THEN** a sub-aba "Fluxo Financeiro" DEVE estar ativa e selecionável

#### Scenario: FinancialFlowPanel exibido na sub-aba
- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o sistema DEVE exibir o `FinancialFlowPanel` com gauge, barra empilhada e classificação

### Requirement: Summary callback atualiza OrientationPanel dinamicamente

O sistema DEVE conectar o `summary_callback` do `FinancialFlowPanel` para atualizar dinamicamente o OrientationPanel com um resumo textual do fluxo financeiro, seguindo o mesmo padrão do gráfico de Quadrantes.

#### Scenario: OrientationPanel atualizado com resumo do fluxo
- **WHEN** o `FinancialFlowPanel` invoca `summary_callback(summary_text)`
- **THEN** o texto do OrientationPanel DEVE ser atualizado para incluir "---" seguido do summary_text, sem perder o conteúdo explicativo base

### Requirement: Indicators tab config atualizada

O sistema DEVE atualizar a configuração de indicadores da tab "Fluxo Financeiro" em `tab_configs` para refletir corretamente os indicadores utilizados pelo painel visual.

#### Scenario: Indicadores corretos na tab_config
- **WHEN** a sub-aba "Fluxo Financeiro" é selecionada
- **THEN** o sistema DEVE usar apenas os indicadores relevantes para o painel (daily_money_flow, money_flow_volume, clv, buying_pressure, selling_pressure, range_percentual)

### Requirement: Carga de dados usa todos os tickers da lista
O método `_ensure_tickers()` DEVE usar `get_all_listbox_tickers()` para obter a lista completa de tickers, independentemente de quais estão marcados. A marcação no Listbox só afeta a exibição nos painéis, não a carga de dados.

#### Scenario: Carga com tickers desmarcados
- **WHEN** o usuário tem 30 tickers no Listbox, desmarca 10, e clica em "Carregar"
- **THEN** os dados DEVEM ser carregados para todos os 30 tickers (não apenas os 20 marcados)

### Requirement: Combobox de seleção de período

O sistema DEVE exibir um combobox do tipo `ttk.Combobox` em modo read-only na barra superior, posicionado entre o botão "Carregar" e o combobox de amostragem, com as opções: "Últimos 30 dias", "Últimos 60 dias (cache)", "Últimos 90 dias (cache)". O valor padrão DEVE ser "Últimos 30 dias".

#### Scenario: Posicionamento do combobox de período
- **WHEN** o usuário visualiza a barra superior
- **THEN** o combobox de período DEVE estar posicionado entre o botão "Carregar" e o combobox de amostragem

#### Scenario: Combobox de período é readonly
- **WHEN** o usuário tenta digitar no combobox de período
- **THEN** o sistema DEVE impedir a digitação (apenas seleção dos itens pré-definidos)

### Requirement: Combobox de seleção de amostragem

O sistema DEVE exibir um combobox do tipo `ttk.Combobox` em modo read-only na barra superior, posicionado entre o combobox de período e o botão "Copiar dados CSV", com as opções: "Fibonacci", "Fibonacci reverso", "Fibonacci duplo", "Monte Carlo", "Monte Carlo duplo", "Todos os dias". O valor padrão DEVE ser "Fibonacci".

#### Scenario: Posicionamento do combobox de amostragem
- **WHEN** o usuário visualiza a barra superior
- **THEN** o combobox de amostragem DEVE estar posicionado entre o combobox de período e o botão "Copiar dados CSV"

### Requirement: Tooltips nos comboboxes

Cada combobox DEVE ter um tooltip fixo (usando a classe `ToolTip` existente) que explique a função do controle.

#### Scenario: Tooltip do período
- **WHEN** o usuário passa o mouse sobre o combobox de período
- **THEN** DEVE exibir o tooltip "Seleciona a janela de tempo para análise dos dados históricos"

#### Scenario: Tooltip da amostragem
- **WHEN** o usuário passa o mouse sobre o combobox de amostragem
- **THEN** DEVE exibir o tooltip "Define o método de seleção das datas dentro do período"

### Requirement: Texto explicativo dinâmico do método de amostragem

A mensagem explicativa do método de amostragem DEVE ser exibida em um `tk.Label` (`_sampling_label`) posicionado ao lado do `_date_label` na barra superior, com cor `fg="gray"`. O label DEVE ser atualizado no evento `<<ComboboxSelected>>` do combobox de amostragem. O texto explicativo do período permanece na barra de status.

#### Scenario: Label de amostragem mostra texto conciso ao selecionar
- **WHEN** o usuário seleciona "Fibonacci" no combobox de amostragem
- **THEN** o `_sampling_label` DEVE exibir "Amostra concentrada nas datas mais recentes."

### Requirement: Texto explicativo do período na barra de status

Ao selecionar um item no combobox de período, a barra de status DEVE exibir o texto explicativo do período selecionado. Apenas quando o usuário finaliza a seleção (evento `<<ComboboxSelected>>`) é que a ação de recarga (se aplicável) DEVE ser disparada.

#### Scenario: Texto explicativo ao selecionar período 60 dias
- **WHEN** o usuário seleciona "Últimos 60 dias (cache)" no combobox de período
- **THEN** a barra de status DEVE exibir "Janela de 60 dias corridos. Apenas dados já em cache serão utilizados — sem download da B3."

### Requirement: Recarga automática ao mudar seleção com dados carregados

O sistema DEVE monitorar o evento `<<ComboboxSelected>>` de ambos os comboboxes. Se houver dados previamente carregados (`self._current_data` não vazio), DEVE iniciar automaticamente uma nova carga de dados usando a nova configuração de período e amostragem, respeitando o OperationGuard.

#### Scenario: Mudança de período com dados carregados
- **WHEN** o usuário tem dados carregados e seleciona "Últimos 60 dias (cache)" no combobox de período
- **THEN** o sistema DEVE desabilitar os controles, iniciar nova carga com período=60, e restaurar os controles ao finalizar

#### Scenario: Mudança de amostragem sem dados carregados
- **WHEN** o usuário abre a aplicação (sem dados carregados) e seleciona "Monte Carlo duplo"
- **THEN** o sistema NÃO DEVE executar nenhuma ação além de atualizar o valor selecionado

### Requirement: Comboboxes desabilitados durante operações

Os comboboxes de período e amostragem DEVEM ser desabilitados (state=DISABLED) durante qualquer operação de carga ou processamento, juntamente com os demais botões da interface.

#### Scenario: Combos desabilitados durante carga
- **WHEN** o usuário clica em "Carregar"
- **THEN** os comboboxes de período e amostragem DEVEM ser desabilitados, impedindo qualquer alteração durante o processamento

#### Scenario: Combos restaurados após carga
- **WHEN** o processamento finaliza (com sucesso ou erro)
- **THEN** os comboboxes DEVEM retornar ao estado "readonly"

### Requirement: Sub-aba Fundamentos exibe a análise fundamentalista real

A sub-aba "Fundamentos" da aba "Análise Geral" DEVE ser populada com a análise fundamentalista dos tickers carregados, exibindo, por ticker, a identidade (ticker, nome, tipo, sub-tipo), os dados de dividendo (última data-com, último dividendo e tendência) e as métricas disponíveis. Colunas cuja fonte ainda não está disponível DEVEM ser exibidas como `N/A`, sem impedir a exibição das demais.

#### Scenario: Tickers carregados populam a tabela
- **WHEN** o usuário carrega dados para uma watchlist e navega para a sub-aba "Fundamentos"
- **THEN** a tabela DEVE exibir uma linha por ticker com nome, tipo/sub-tipo e dados de dividendo preenchidos, e `N/A` nas métricas ainda indisponíveis

#### Scenario: Ticker sem dados fundamentalistas
- **WHEN** um ticker não resolve para identidade/proventos na B3
- **THEN** a tabela DEVE exibir a linha com os campos disponíveis e `N/A` nos demais, sem remover o ticker

### Requirement: Análise fundamentalista executada em background com progresso

A análise fundamentalista DEVE ser executada fora da thread da interface, de modo que a janela permaneça responsiva durante a aquisição, e DEVE reportar progresso por ticker/etapa na barra de status. O progresso DEVE ser exibido na barra de progresso da barra de status, informando o número de tickers processados sobre o total, iniciando em `0/N` e avançando a cada ticker concluído. A thread de trabalho NÃO DEVE acessar widgets do Tk diretamente; os resultados e o progresso DEVEM ser entregues à thread da interface por meio de uma fila consumida periodicamente.

#### Scenario: Interface responsiva durante a aquisição
- **WHEN** a análise fundamentalista está em andamento
- **THEN** a interface DEVE continuar respondendo a eventos e exibir progresso da operação

#### Scenario: Resultado entregue na thread da interface
- **WHEN** a thread de trabalho conclui a análise
- **THEN** os resultados DEVEM ser publicados na thread do Tk antes de atualizar a tabela

#### Scenario: Barra de progresso inicia em zero
- **WHEN** a análise fundamentalista é iniciada
- **THEN** a barra de progresso DEVE ser exibida com `0/N` tickers processados

#### Scenario: Barra de progresso avança por ticker
- **WHEN** um ticker é concluído
- **THEN** a barra de progresso DEVE avançar para o número de tickers processados sobre o total

### Requirement: Glifos consistentes na barra de status

A barra de status DEVE usar glifos que renderizam de forma consistente nas plataformas suportadas. Mensagens de progresso DEVEM ser prefixadas por um marcador consistente (ex.: `•`) em vez do glifo de informação `ℹ`, mantendo os ícones de desfecho já existentes (ex.: `✓` e `⚠`).

#### Scenario: Progresso usa marcador consistente
- **WHEN** o progresso da análise fundamentalista é exibido
- **THEN** a mensagem DEVE usar um marcador que renderiza de forma consistente, e não o glifo `ℹ`

#### Scenario: Desfecho mantém os ícones existentes
- **WHEN** a carga conclui com sucesso ou com falha
- **THEN** os ícones de desfecho (`✓` e `⚠`) DEVEM ser mantidos

### Requirement: Descarte de resultados obsoletos

Quando uma nova carga de dados é iniciada antes da conclusão de uma análise fundamentalista anterior, o sistema DEVE descartar os resultados da execução obsoleta e exibir apenas os da carga mais recente.

#### Scenario: Nova carga invalida execução anterior
- **WHEN** o usuário inicia uma nova carga enquanto uma análise anterior ainda está em andamento
- **THEN** os resultados da execução anterior NÃO DEVEM ser exibidos na tabela

### Requirement: Atualização da tabela ao trocar de sub-aba

Os resultados da análise fundamentalista DEVEM ser armazenados por ticker e aplicados à tabela quando a sub-aba "Fundamentos" for selecionada, sem reexecutar a aquisição a cada troca de sub-aba.

#### Scenario: Troca para Fundamentos reutiliza resultados
- **WHEN** a análise já foi concluída e o usuário seleciona a sub-aba "Fundamentos"
- **THEN** a tabela DEVE ser atualizada com os resultados armazenados sem nova requisição à B3

### Requirement: Sub-aba Fundamentos na Análise Geral
O sistema DEVE adicionar uma sub-aba "Fundamentos" como a **primeira** sub-aba do sub-notebook da aba "Análise Geral", exibindo uma tabela fundamentalista para os tickers selecionados no Listbox. A sub-aba "Fundamentos" DEVE preceder "VWAP", "Quadrantes" e "Dominância do Pregão".

#### Scenario: Sub-aba Fundamentos é a primeira
- **WHEN** o usuário navega para a aba "Análise Geral"
- **THEN** a primeira sub-aba do sub-notebook DEVE ser "Fundamentos"

#### Scenario: Sub-aba Fundamentos exibe tabela
- **WHEN** o usuário navega para a aba "Análise Geral" e seleciona a sub-aba "Fundamentos"
- **THEN** o sistema DEVE exibir uma tabela com uma linha por ticker selecionado no Listbox

#### Scenario: Tabela usa os tickers do Listbox
- **WHEN** o usuário seleciona 5 tickers no Listbox e navega para a sub-aba "Fundamentos"
- **THEN** a tabela DEVE exibir os dados fundamentalistas para os 5 tickers selecionados

### Requirement: Colunas da tabela fundamentalista

A tabela fundamentalista DEVE exibir, nesta ordem, as colunas: Ticker, Nome, Tipo (`Papel`/`FII`), Sub-tipo, P (Cotação), Preço Típico, P / PT, VP (VP/Cota), P/VP, P/L, Dividend Yield, Última data-com, Último dividendo, Dividendo anterior, Tendência do dividendo, Shorts%, Volume de Shorts, Fechamento Shorts, Risco Fechamento, FFO/Receita (12m), FFO/Receita (3m), FFO Trend, Dividendos/Receita (12m), Dividendos/Receita (3m), Dividendos/FFO (12m), Dividendos/FFO (3m), Nº de cotas, Nº de cotistas, Classe de cotistas, Patrimônio, Classe de patrimônio, Data de referência, Informações adicionais e Dados fiscais. A coluna `Nº de cotas` DEVE ser exibida imediatamente antes de `Nº de cotistas`, com a quantidade de cotas/ações emitidas formatada como inteiro com separador de milhar. As colunas `Shorts%`, `Volume de Shorts`, `Fechamento Shorts` e `Risco Fechamento` DEVEM ser exibidas imediatamente após `Tendência do dividendo` e imediatamente antes de `FFO/Receita (12m)`. As colunas `FFO Yield`, `P/FFO` e `Dividend Payout (DY/FFOY)` NÃO DEVEM mais ser exibidas.

#### Scenario: Colunas de identidade preenchidas
- **WHEN** a tabela é renderizada para um ticker conhecido
- **THEN** as colunas Ticker, Nome, Tipo e Sub-tipo DEVEM estar preenchidas

#### Scenario: Coluna Nº de cotas posicionada antes de Nº de cotistas
- **WHEN** a tabela é renderizada
- **THEN** a coluna `Nº de cotas` DEVE ser exibida imediatamente antes da coluna `Nº de cotistas`

#### Scenario: Nº de cotas formatado como inteiro com milhar
- **WHEN** a quantidade de cotas/ações emitidas do ticker está disponível
- **THEN** a coluna `Nº de cotas` DEVE exibir o valor como inteiro com separador de milhar, ou `N/A` quando ausente

#### Scenario: Coluna de dividendo anterior
- **WHEN** o ticker possui dividendo anterior consolidado
- **THEN** a coluna `Dividendo anterior` DEVE exibir o valor do dividendo imediatamente anterior ao último

#### Scenario: Dividend Payout (DY/FFOY)
- **WHEN** a tabela é renderizada
- **THEN** a coluna `Dividend Payout (DY/FFOY)` NÃO DEVE mais ser exibida, sendo substituída por `Dividendos/FFO (12m)` e `Dividendos/FFO (3m)`

#### Scenario: Preço e VP/Cota
- **WHEN** a fonte fornece a cotação e o VP/Cota do ticker
- **THEN** as colunas `P (Cotação)` e `VP (VP/Cota)` DEVEM exibir esses valores

#### Scenario: Coluna P/L
- **WHEN** a tabela é renderizada
- **THEN** a coluna `P/L` DEVE ser exibida imediatamente após a coluna `P/VP`

#### Scenario: FFO Trend posicionado após a margem de 3 meses
- **WHEN** a tabela é renderizada
- **THEN** a coluna `FFO Trend` DEVE ser exibida imediatamente após a coluna `FFO/Receita (3m)`

#### Scenario: Razões exibidas em percentual com uma casa decimal
- **WHEN** as razões de um FII estão disponíveis
- **THEN** `FFO/Receita`, `Dividendos/Receita` e `Dividendos/FFO` (12m e 3m) DEVEM ser exibidos em notação percentual com uma casa decimal

#### Scenario: Insumo negativo exibe texto
- **WHEN** a Receita ou o FFO de um período é negativo
- **THEN** a célula da razão correspondente DEVE exibir `Receita negativa`, `FFO negativo` ou `Receita e FFO negativos`

#### Scenario: Colunas FFO vazias para não elegível
- **WHEN** o ticker é do tipo `Papel` ou a fonte não fornece os insumos das razões
- **THEN** as colunas `FFO/Receita`, `Dividendos/Receita` e `Dividendos/FFO` DEVEM exibir `N/A`

#### Scenario: Métricas preenchidas quando disponíveis
- **WHEN** a fonte fornece Receita, FFO e Rend. Distribuído do ticker
- **THEN** as razões `FFO/Receita`, `Dividendos/Receita` e `Dividendos/FFO` e o `FFO Trend` DEVEM ser exibidos

#### Scenario: Novas colunas de cotistas e patrimônio
- **WHEN** a tabela é renderizada
- **THEN** as colunas de cotistas, classificação de cotistas, tamanho patrimonial, classificação patrimonial e data de referência DEVEM ser exibidas

#### Scenario: Colunas de short interest posicionadas após Tendência do dividendo
- **WHEN** a tabela é renderizada
- **THEN** as colunas `Shorts%`, `Volume de Shorts`, `Fechamento Shorts` e `Risco Fechamento` DEVEM ser exibidas imediatamente após `Tendência do dividendo` e imediatamente antes de `FFO/Receita (12m)`

#### Scenario: Shorts% e Fechamento Shorts exibidos como numéricos
- **WHEN** o `Shorts%` e o `SIR` de um ticker estão disponíveis
- **THEN** `Shorts%` DEVE ser exibido em notação percentual com uma casa decimal e `Fechamento Shorts` em dias, como razão com uma casa decimal e sufixo `d`

#### Scenario: Volume de Shorts e Risco Fechamento exibem rótulos
- **WHEN** o `Shorts%` e o `SIR` de um ticker estão disponíveis
- **THEN** `Volume de Shorts` e `Risco Fechamento` DEVEM exibir um dos rótulos `Inexistente`, `Muito Baixo`, `Baixo`, `Alto` ou `Muito Alto`

#### Scenario: Colunas de short interest vazias sem dado
- **WHEN** o ticker não possui estoque de empréstimos ou denominador aplicável
- **THEN** `Shorts%` e `Fechamento Shorts` DEVEM exibir `N/A` e `Volume de Shorts` e `Risco Fechamento` DEVEM exibir `Inexistente`, sem impedir a exibição das demais colunas

### Requirement: Alinhamento das colunas numéricas

A tabela fundamentalista DEVE alinhar à direita o conteúdo das colunas Último dividendo, Dividendo anterior, Dividend Yield, Shorts%, Fechamento Shorts, FFO/Receita (12m), FFO/Receita (3m), Dividendos/Receita (12m), Dividendos/Receita (3m), Dividendos/FFO (12m), Dividendos/FFO (3m), P (Cotação), Preço Típico, P / PT, VP (VP/Cota), P/L, P/VP, Nº de cotas, Nº de cotistas e Patrimônio, mantendo as demais colunas alinhadas à esquerda.

#### Scenario: Colunas numéricas alinhadas à direita
- **WHEN** a tabela é renderizada
- **THEN** as colunas Último dividendo, Dividendo anterior, Dividend Yield, Shorts%, Fechamento Shorts, FFO/Receita (12m), FFO/Receita (3m), Dividendos/Receita (12m), Dividendos/Receita (3m), Dividendos/FFO (12m), Dividendos/FFO (3m), P (Cotação), Preço Típico, P / PT, VP (VP/Cota), P/L, P/VP, Nº de cotas, Nº de cotistas e Patrimônio DEVEM ter o conteúdo alinhado à direita

#### Scenario: Colunas textuais alinhadas à esquerda
- **WHEN** a tabela é renderizada
- **THEN** as colunas Ticker, Nome, Tipo, Sub-tipo, Última data-com, Tendência do dividendo, Volume de Shorts, Risco Fechamento, FFO Trend, Classe de cotistas, Classe de patrimônio, Data de referência, Informações adicionais e Dados fiscais DEVEM ter o conteúdo alinhado à esquerda

### Requirement: OrientationPanel para a sub-aba Fundamentos

O sistema DEVE exibir no OrientationPanel o conteúdo explicativo da sub-aba "Fundamentos", seguindo o padrão existente (objetivo, pergunta respondida, indicadores envolvidos e como interpretar). O campo **Indicadores envolvidos** DEVE descrever todas as colunas exibidas na tabela, incluindo Preço Típico, P / PT, as razões `FFO/Receita`, `Dividendos/Receita` e `Dividendos/FFO` (12m e 3m), as colunas de *short interest* (`Shorts%`, `Volume de Shorts`, `Fechamento Shorts` e `Risco Fechamento`), a quantidade de cotas/ações emitidas, Informações adicionais e Dados fiscais. O campo **Como interpretar** DEVE conter orientações sucintas de leitura para essas colunas: `FFO/Receita` como quanto da receita vira caixa operacional; `Dividendos/Receita` como quanto da receita é destinado a dividendos; `Dividendos/FFO` como quanto do caixa operacional é consumido pelos dividendos, abaixo de 100% o FFO cobre os dividendos, acima de 100% os dividendos superam o FFO e negativo o FFO foi negativo no período; `Shorts%` como a magnitude relativa da aposta baixista sobre o *free float*; e `Fechamento Shorts` como a dificuldade operacional de fechamento, com valores acima de 5 considerados altos.

#### Scenario: OrientationPanel da sub-aba Fundamentos
- **WHEN** o usuário seleciona a sub-aba "Fundamentos"
- **THEN** o OrientationPanel DEVE exibir texto explicativo sobre as métricas fundamentalistas e de dividendo exibidas na tabela

#### Scenario: Indicadores envolvidos descrevem as colunas exibidas
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Indicadores envolvidos" DEVE mencionar Preço Típico, P / PT, as razões `FFO/Receita`, `Dividendos/Receita` e `Dividendos/FFO`, as colunas `Shorts%`, `Volume de Shorts`, `Fechamento Shorts` e `Risco Fechamento`, a quantidade de cotas/ações emitidas, Informações adicionais e Dados fiscais, além de identidade, cotação, VP/Cota, P/VP, P/L, Dividend Yield, dividendos, tendências, cotistas/acionistas e patrimônio

#### Scenario: Identidade descreve o Tipo e o Sub-tipo implementados
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Indicadores envolvidos" DEVE descrever o Tipo como `Papel` (ações, ETFs e BDRs) ou `FII`, e o Sub-tipo como o prefixo `Tijolo:`/`Papel:` seguido de segmento e gestão para FIIs, ou espécie, setor e subsetor para Papéis, em vez dos rótulos genéricos ação/FII/ETF/BDR e tijolo/papel/híbrido/fiagro/fiinfra

#### Scenario: Como interpretar orienta o Preço Típico e o P / PT
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar que o Preço Típico é a referência de preço médio de 52 semanas e que o P / PT expressa desconto (negativo) ou prêmio (positivo) da cotação frente a esse preço típico

#### Scenario: Como interpretar orienta a quantidade de cotas emitidas
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar que a quantidade de cotas/ações emitidas dimensiona o fundo/companhia e que, para FIIs, vem da B3/CVM com fallback do Fundamentus, enquanto para Papéis vem do Fundamentus

#### Scenario: Como interpretar orienta o Dividend Payout
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar que `Dividendos/FFO` abaixo de 100% indica que o FFO cobre os dividendos, acima de 100% que os dividendos superam o FFO e negativo que o FFO foi negativo no período, em substituição ao antigo Dividend Payout

#### Scenario: Como interpretar orienta Informações adicionais e Dados fiscais
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar que Informações adicionais reúnem indicadores do ativo (LPA, ROE e ROIC para ações; imóveis, Cap Rate, Vacância Média e indexadores para FIIs) e que Dados fiscais reúnem o CNPJ e, para FIIs, o administrador e o gestor, omitindo itens sem dado

#### Scenario: Orientação de leitura das razões
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar `FFO/Receita` como quanto da receita vira caixa operacional e `Dividendos/Receita` como quanto da receita é destinado a dividendos

#### Scenario: Como interpretar orienta as colunas de short interest
- **WHEN** o OrientationPanel da sub-aba "Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE explicar `Shorts%` como a magnitude relativa da aposta baixista sobre o *free float* e `Fechamento Shorts` como a dificuldade operacional de fechamento, mencionando que valores acima de 5 são considerados altos

### Requirement: Congelamento das colunas Ticker e Nome na tabela de Fundamentos

A sub-aba "Fundamentos" DEVE manter as colunas `Ticker` e `Nome` fixas à esquerda enquanto as demais colunas rolam horizontalmente. A tabela DEVE ser composta por dois Treeviews sincronizados, lado a lado, com a fronteira definida pela borda direita da última coluna congelada: o Treeview congelado exibe apenas `Ticker` e `Nome` e NÃO possui rolagem horizontal; o Treeview rolável exibe as demais colunas e mantém a rolagem horizontal. Os dois Treeviews DEVEM compartilhar a mesma barra de rolagem vertical, de modo que uma única rolagem mantenha as linhas alinhadas.

#### Scenario: Colunas congeladas permanecem visíveis
- **WHEN** o usuário rola a tabela horizontalmente para a direita
- **THEN** as colunas Ticker e Nome DEVEM permanecer visíveis à esquerda, sem rolar

#### Scenario: Rolagem vertical sincronizada
- **WHEN** o usuário rola a tabela verticalmente por qualquer um dos Treeviews ou pela barra de rolagem vertical
- **THEN** as mesmas linhas DEVEM permanecer alinhadas nos dois Treeviews

#### Scenario: Rolagem horizontal apenas nas colunas roláveis
- **WHEN** o usuário rola a tabela horizontalmente
- **THEN** apenas o Treeview rolável DEVE se deslocar, mantendo o painel congelado imóvel

### Requirement: Largura do painel congelado definida pelas colunas

A largura do painel congelado DEVE ser a soma das larguras das colunas `Ticker` e `Nome`, de modo que a fronteira entre os painéis seja a borda direita de `Nome`, reforçada por uma linha divisória vertical fixa e não arrastável. Redimensionar uma coluna congelada DEVE redimensionar o painel congelado, sem deixar espaço vazio (gap) nem cortar o conteúdo (clipping). As larguras persistidas das colunas DEVEM determinar a largura inicial do painel congelado. O painel rolável DEVE manter uma largura mínima, limitando o painel congelado quando as colunas congeladas crescerem além do espaço disponível.

#### Scenario: Redimensionar coluna congelada redimensiona o painel
- **WHEN** o usuário redimensiona a coluna `Ticker` ou `Nome`
- **THEN** a largura do painel congelado DEVE acompanhar a soma das duas colunas, sem gap nem clipping, e o painel rolável DEVE ocupar o restante do espaço

#### Scenario: Largura inicial derivada das colunas
- **WHEN** a tabela é montada com larguras persistidas para `Ticker` e `Nome`
- **THEN** o painel congelado DEVE iniciar com a soma dessas larguras

#### Scenario: Limite do painel rolável
- **WHEN** a soma das larguras das colunas congeladas excede o espaço disponível menos a largura mínima do painel rolável
- **THEN** o painel congelado DEVE ser limitado para preservar a largura mínima do painel rolável

### Requirement: Seleção de linha espelhada e única na tabela de Fundamentos

A seleção DEVE ser de uma única linha por vez e DEVE ser espelhada entre os dois Treeviews: ao selecionar uma linha em qualquer um dos painéis, a mesma linha DEVE ser selecionada no outro.

#### Scenario: Seleção espelhada
- **WHEN** o usuário seleciona uma linha no painel congelado ou no painel rolável
- **THEN** a linha correspondente DEVE ser marcada como selecionada no outro painel

#### Scenario: Seleção única
- **WHEN** o usuário tenta selecionar mais de uma linha com Ctrl ou Shift
- **THEN** apenas uma linha DEVE permanecer selecionada

### Requirement: Cópia CSV da tabela completa independente do congelamento

O comando "Copiar dados CSV" da sub-aba Fundamentos DEVE continuar copiando todas as colunas da tabela fundamentalista, na mesma ordem e com a mesma formatação, independentemente de as colunas Ticker e Nome estarem congeladas.

#### Scenario: CSV com todas as colunas
- **WHEN** o usuário aciona "Copiar dados CSV" na sub-aba Fundamentos
- **THEN** o conteúdo copiado DEVE conter o cabeçalho e as linhas com todas as colunas da tabela, incluindo Ticker e Nome

### Requirement: Persistência da largura das colunas da tabela fundamentalista
O sistema DEVE armazenar no arquivo de configuração (`config.json`) a largura de cada coluna da tabela fundamentalista — tanto das colunas congeladas `Ticker` e `Nome` quanto das colunas roláveis — quando o usuário a ajusta e DEVE restaurá-las na próxima execução, associando cada largura ao identificador estável da coluna. As larguras DEVEM ser agregadas dos dois Treeviews que compõem a tabela e DEVEM determinar a largura do painel congelado.

#### Scenario: Largura restaurada na próxima execução
- **WHEN** o usuário redimensiona uma coluna e reabre a aplicação
- **THEN** a coluna DEVE reaparecer com a largura ajustada

#### Scenario: Largura de coluna congelada restaurada
- **WHEN** o usuário redimensiona a coluna `Ticker` ou `Nome` no painel congelado e reabre a aplicação
- **THEN** a coluna congelada DEVE reaparecer com a largura ajustada e o painel congelado DEVE usar a soma das larguras restauradas

#### Scenario: Sem preferência salva
- **WHEN** não há larguras salvas para a tabela fundamentalista
- **THEN** o sistema DEVE usar as larguras padrão

### Requirement: Mensagens de status da análise fundamentalista
O sistema DEVE exibir, na barra de status, o sufixo `" - cached"` no progresso de um ticker cujo dado veio do cache (`HIT` ou `REVALIDATED`) e, ao final da carga, DEVE exibir uma mensagem de desfecho: `"Dados atualizados com sucesso."` sem falhas, `"Dados atualizados com mitigação de falhas."` quando houver falha recuperável, e `"Falha ao atualizar dados"` em falha catastrófica.

#### Scenario: Dado vindo do cache
- **WHEN** o dado de um ticker é servido do cache durante a análise
- **THEN** o progresso do ticker DEVE exibir o sufixo `" - cached"`

#### Scenario: Carga concluída sem falhas
- **WHEN** a análise fundamentalista termina sem falha na captura
- **THEN** a barra de status DEVE exibir `"Dados atualizados com sucesso."`

#### Scenario: Carga concluída com falha recuperável
- **WHEN** a análise fundamentalista termina com ao menos uma falha recuperável
- **THEN** a barra de status DEVE exibir `"Dados atualizados com mitigação de falhas."`

#### Scenario: Falha catastrófica
- **WHEN** a análise fundamentalista não consegue concluir
- **THEN** a barra de status DEVE exibir `"Falha ao atualizar dados"`

### Requirement: Rótulos descritivos das tendências

A tabela fundamentalista DEVE exibir rótulos descritivos em português para as colunas `FFO Trend` e `Tendência do dividendo`, em vez dos identificadores técnicos: `Forte Alta` para a faixa superior, `Leve Alta` para alta moderada, `Estável` para estabilidade, `Leve Queda` para queda moderada e `Forte Queda` para a faixa inferior, exibindo `N/A` quando a tendência não estiver disponível.

#### Scenario: Rótulos do FFO Trend
- **WHEN** a classificação do FFO Momentum é `FORTE_ALTA`, `ALTA`, `ESTAVEL`, `QUEDA` ou `FORTE_QUEDA`
- **THEN** a coluna `FFO Trend` DEVE exibir, respectivamente, `Forte Alta`, `Leve Alta`, `Estável`, `Leve Queda` ou `Forte Queda`

#### Scenario: Rótulos da Tendência do dividendo
- **WHEN** a classificação da tendência do dividendo é `FORTE_ALTA`, `ALTA`, `ESTAVEL`, `QUEDA` ou `FORTE_QUEDA`
- **THEN** a coluna `Tendência do dividendo` DEVE exibir, respectivamente, `Forte Alta`, `Leve Alta`, `Estável`, `Leve Queda` ou `Forte Queda`

#### Scenario: Tendência indisponível
- **WHEN** a tendência não está disponível
- **THEN** a coluna correspondente DEVE exibir `N/A`

### Requirement: Formatação numérica das colunas da tabela fundamentalista
A tabela fundamentalista DEVE formatar as colunas "Último dividendo", "Dividendo anterior", "Dividend Payout (DY/FFOY)", "P (Cotação)" e "VP (VP/Cota)" com exatamente duas casas decimais, usando vírgula como separador decimal. A coluna "Dividend Payout (DY/FFOY)" DEVE incluir o sufixo `%`; as demais DEVEM manter seus formatos (valor monetário curto e valor por cota). Quando não houver valor, a coluna DEVE exibir `N/A`.

#### Scenario: Valores com 2 casas decimais
- **WHEN** um ticker possui último dividendo `0,7`, dividendo anterior `0,5`, cotação `15,5` e VP/Cota `10`
- **THEN** a tabela DEVE exibir `0,70`, `0,50`, `15,50` e `10,00` nas respectivas colunas

#### Scenario: Dividend Payout com 2 casas decimais
- **WHEN** Dividend Yield e FFO Yield estão disponíveis e a razão entre eles é `0,894`
- **THEN** a coluna "Dividend Payout (DY/FFOY)" DEVE exibir `89,40%`

#### Scenario: Sem valor
- **WHEN** o valor de uma dessas colunas é ausente para o ticker
- **THEN** a coluna DEVE exibir `N/A`

#### Scenario: Exportação CSV consistente com a tabela
- **WHEN** o usuário copia a tabela de Fundamentos como CSV
- **THEN** os valores DEVEM usar a mesma formatação de duas casas decimais exibida na tabela

### Requirement: Colunas Preço Típico, P / PT, Informações adicionais e Dados fiscais

A tabela fundamentalista DEVE exibir as colunas `Preço Típico` e `P / PT` logo após `P (Cotação)`, alinhadas à direita. `Preço Típico` DEVE exibir `(Max 52 sem + Min 52 sem + Cotação) / 3` e `P / PT` DEVE exibir `(Cotação − Preço Típico) / Preço Típico` como percentual; ambos DEVEM exibir `N/A` quando faltar qualquer insumo.

A tabela DEVE exibir, ao final, as colunas `Informações adicionais` e `Dados fiscais`, cujos itens são concatenados separados por ` | ` e precedidos de labels curtos. Itens sem valor em nenhuma fonte DEVEM ser omitidos; quando a coluna não tiver nenhum item, DEVE exibir `N/A`.

Para ativos do tipo Papel, `Informações adicionais` DEVE conter `LPA`, `ROE` e `ROIC`. Para FIIs, DEVE conter `Qtd Imóveis`, `Cap Rate`, `Vacância Média` e os percentuais por indexador; quando `Qtd imóveis` for zero ou desconhecido, `Qtd Imóveis`, `Cap Rate` e `Vacância Média` DEVEM ser omitidos. Para FIIs, `Informações adicionais` DEVE conter também, quando houver guidance no cache do FII, um item com label `Guidance`, o valor ou a faixa por cota e o período de validade, seguido do mês e ano do relatório que apontou o guidance, no formato `Guidance R$ 0,74 a R$ 0,78/cota (restante do ano de 2026, ago/26)`. A exibição DEVE ler apenas o cache de guidance: NÃO DEVE calcular nem disparar extração de guidance na carga de dados nem na renderização da tabela. Quando não houver guidance em cache, o item DEVE ser omitido, sem impedir os demais itens.

Em `Dados fiscais`, FIIs DEVEM exibir `CNPJ`, `Administrador <nome> (<CNPJ>)` e `Gestor <nome> (<CNPJ>)`; Papel DEVE exibir apenas `CNPJ`. CNPJs DEVEM ser exibidos no formato `99.999.999/9999-99`.

#### Scenario: Preço Típico e P / PT calculados
- **WHEN** o ativo possui cotação, mínima e máxima de 52 semanas
- **THEN** as colunas `Preço Típico` e `P / PT` DEVEM exibir o preço típico e o desvio percentual da cotação, alinhados à direita

#### Scenario: Insumo ausente para o Preço Típico
- **WHEN** falta a cotação, a mínima ou a máxima de 52 semanas
- **THEN** as colunas `Preço Típico` e `P / PT` DEVEM exibir `N/A`

#### Scenario: Informações adicionais de Papel
- **WHEN** um ativo do tipo Papel possui LPA, ROE e ROIC
- **THEN** a coluna DEVE exibir `LPA`, `ROE` e `ROIC`, separados por ` | `

#### Scenario: Informações adicionais de FII de tijolo
- **WHEN** um FII possui `Qtd imóveis` maior que zero e demais dados disponíveis
- **THEN** a coluna DEVE exibir `Qtd Imóveis`, `Cap Rate`, `Vacância Média` e os percentuais por indexador

#### Scenario: FII sem imóveis
- **WHEN** um FII possui `Qtd imóveis` igual a zero ou desconhecido
- **THEN** a coluna NÃO DEVE exibir `Qtd Imóveis`, `Cap Rate` nem `Vacância Média`, mantendo os demais itens disponíveis

#### Scenario: Informações adicionais com guidance
- **WHEN** o cache de um FII contém guidance
- **THEN** a coluna DEVE exibir um item `Guidance` com o valor ou faixa por cota, o período de validade e o mês/ano do relatório, separado dos demais por ` | `

#### Scenario: FII sem guidance
- **WHEN** o cache de um FII não contém guidance
- **THEN** o item de guidance NÃO DEVE aparecer, mantendo os demais itens da coluna

#### Scenario: Exibição não calcula guidance
- **WHEN** a tabela de Fundamentos é carregada ou renderizada
- **THEN** a coluna NÃO DEVE disparar extração de guidance, exibindo apenas o que estiver no cache

#### Scenario: Dados fiscais de FII
- **WHEN** o FII possui CNPJ, administrador e gestor com seus nomes e CNPJs
- **THEN** a coluna DEVE exibir `CNPJ`, `Administrador <nome> (<CNPJ>)` e `Gestor <nome> (<CNPJ>)`, separados por ` | `

#### Scenario: Dados fiscais de Papel
- **WHEN** o ativo é do tipo Papel e a CVM resolve o CNPJ
- **THEN** a coluna DEVE exibir apenas o `CNPJ`

#### Scenario: Item indisponível
- **WHEN** um item não está disponível em nenhuma fonte
- **THEN** ele NÃO DEVE aparecer na concatenação, sem impedir os demais

#### Scenario: Coluna sem itens
- **WHEN** nenhum item de uma das colunas está disponível para o ticker
- **THEN** a coluna DEVE exibir `N/A`

#### Scenario: Exportação CSV consistente
- **WHEN** o usuário copia a tabela de Fundamentos como CSV
- **THEN** as colunas novas DEVEM conter os mesmos textos exibidos na tabela

### Requirement: Recarga da mesma data reutiliza o cache histórico

Ao carregar dados para uma watchlist, o sistema DEVE reutilizar o cache histórico de resultados fundamentalistas por `(ticker, data)`, de modo que tickers já analisados para a data solicitada sejam exibidos na sub-aba "Fundamentos" sem refazer a aquisição, e os resultados exibidos correspondam sempre à data da carga corrente.

#### Scenario: Recarga da mesma data é instantânea

- **WHEN** o usuário recarrega dados para uma data já analisada anteriormente
- **THEN** a sub-aba "Fundamentos" DEVE ser populada a partir do cache histórico, sem nova aquisição para os tickers já observados naquela data

#### Scenario: Resultados não vazam entre datas

- **WHEN** o usuário carrega dados para uma data diferente da carga anterior
- **THEN** a tabela DEVE exibir apenas observações da data corrente, não reaproveitando linhas de outra data

#### Scenario: Ticker novo na data completa o restante

- **WHEN** a watchlist inclui um ticker ainda não observado para a data solicitada
- **THEN** o sistema DEVE analisar apenas esse ticker e combinar o resultado com os demais servidos pelo cache

### Requirement: Bypass explícito do cache histórico na interface

A sub-aba "Fundamentos" DEVE oferecer uma ação explícita para ignorar o cache histórico e forçar a recomputação da data corrente, sobrescrevendo as observações do dia. A ação DEVE ser apresentada como um botão da barra da lista de tickers, DEVE ser exibida apenas enquanto a sub-aba "Fundamentos" estiver ativa e DEVE permanecer desabilitada enquanto houver uma carga de dados em andamento.

#### Scenario: Atualização forçada no mesmo dia

- **WHEN** o usuário aciona a ação de atualização forçada com uma data carregada
- **THEN** o sistema DEVE recomputar a análise dos tickers exibidos, substituindo as observações do dia, independentemente de já existirem

#### Scenario: Ação visível apenas na sub-aba Fundamentos

- **WHEN** a sub-aba ativa não é "Fundamentos"
- **THEN** a ação de atualização forçada NÃO DEVE ser exibida

#### Scenario: Ação desabilitada durante a carga

- **WHEN** uma carga de dados está em andamento
- **THEN** a ação de atualização forçada DEVE permanecer desabilitada

### Requirement: Tooltips descritivos dos botões de índice

Os botões de índice IBOV, IDIV e IFIX DEVEM exibir, ao passar o mouse, um tooltip curto com apenas a descrição do índice correspondente.

#### Scenario: Tooltip de cada índice

- **WHEN** o usuário posiciona o mouse sobre o botão de um índice
- **THEN** o sistema DEVE exibir a descrição correspondente — `IBOV`: "principais ações negociadas na B3"; `IDIV`: "ações com os maiores dividendos da B3"; `IFIX`: "principais fundos imobiliários (FIIs)"

### Requirement: Sub-aba Evolução dos Fundamentos

A aba "Análise do Ticker" DEVE conter a sub-aba "Evolução dos Fundamentos", ativa e selecionável, exibindo o painel de evolução dos fundamentos do ticker selecionado no lugar de um placeholder de texto.

#### Scenario: Sub-aba disponível na Análise do Ticker

- **WHEN** o usuário navega para a aba "Análise do Ticker"
- **THEN** a sub-aba "Evolução dos Fundamentos" DEVE estar ativa e selecionável

#### Scenario: Painel exibido na sub-aba

- **WHEN** o usuário seleciona a sub-aba "Evolução dos Fundamentos"
- **THEN** o sistema DEVE exibir o painel de evolução dos fundamentos, e não um placeholder de texto

### Requirement: Duplo clique na tabela de Fundamentos ativa a evolução

O sistema DEVE reagir ao duplo clique em uma linha da tabela da sub-aba "Fundamentos" (aba "Análise Geral"), usando o ticker da linha como o ticker da sub-aba "Evolução dos Fundamentos" e tornando essa sub-aba ativa.

#### Scenario: Duplo clique seleciona ticker e troca de sub-aba

- **WHEN** o usuário dá duplo clique em uma linha da tabela de "Fundamentos"
- **THEN** o sistema DEVE usar o ticker daquela linha na sub-aba "Evolução dos Fundamentos" e selecioná-la na aba "Análise do Ticker"

#### Scenario: Ticker do duplo clique prevalece

- **WHEN** o duplo clique é feito em uma linha cujo ticker difere do ticker selecionado na lista de tickers
- **THEN** o painel de evolução DEVE ser preenchido com o ticker da linha clicada

#### Scenario: Duplo clique sem histórico

- **WHEN** o ticker da linha clicada não possui observações no cache histórico
- **THEN** a sub-aba DEVE se tornar ativa exibindo o estado vazio, sem erro

### Requirement: Preenchimento preguiçoso e independente da carga B3

A sub-aba "Evolução dos Fundamentos" DEVE ser preenchida somente quando selecionada e DEVE funcionar apenas com o cache histórico, mesmo quando não houver dados da B3 carregados na sessão corrente.

#### Scenario: Preenchimento ao selecionar a sub-aba

- **WHEN** o usuário seleciona a sub-aba "Evolução dos Fundamentos"
- **THEN** o sistema DEVE montar e exibir a evolução naquele momento

#### Scenario: Sem dados B3 carregados

- **WHEN** não há dados da B3 carregados e o ticker possui observações no cache histórico
- **THEN** o sistema DEVE exibir a evolução normalmente, sem depender de dados da B3

#### Scenario: Sem preenchimento fora da sub-aba

- **WHEN** a sub-aba ativa não é "Evolução dos Fundamentos"
- **THEN** o sistema NÃO DEVE montar o painel de evolução

### Requirement: OrientationPanel da sub-aba Evolução dos Fundamentos

O OrientationPanel DEVE exibir conteúdo explicativo da sub-aba "Evolução dos Fundamentos", composto por objetivo, pergunta respondida, indicadores envolvidos e como interpretar, no mesmo padrão das demais sub-abas. O campo **Indicadores envolvidos** DEVE descrever os oito campos exibidos, incluindo `Shorts%`, e o campo **Como interpretar** DEVE mencionar que o painel mostra oito mini-gráficos (small multiples) e que o `Shorts%` representa a magnitude relativa da aposta baixista.

#### Scenario: Conteúdo explicativo ao selecionar a sub-aba

- **WHEN** o usuário seleciona a sub-aba "Evolução dos Fundamentos"
- **THEN** o OrientationPanel DEVE exibir o título e o texto explicativo da sub-aba, com as seções no padrão existente

#### Scenario: Indicadores envolvidos descrevem os oito campos

- **WHEN** o OrientationPanel da sub-aba "Evolução dos Fundamentos" é exibido
- **THEN** o campo "Indicadores envolvidos" DEVE mencionar Cotação, VP (VP/Cota), P/VP, Dividend Yield, Último dividendo, Nº de cotistas, Nº de cotas e `Shorts%`

#### Scenario: Como interpretar menciona os oito mini-gráficos

- **WHEN** o OrientationPanel da sub-aba "Evolução dos Fundamentos" é exibido
- **THEN** o campo "Como interpretar" DEVE mencionar que o painel exibe oito mini-gráficos e DEVE explicar o `Shorts%` como a magnitude relativa da aposta baixista
