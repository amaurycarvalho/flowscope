## Purpose

Define the behavior and architecture for disabling all buttons during portfolio download and data processing, with automatic restoration of previous states on completion.

## Requirements

### Requirement: Botões desabilitados durante processamento de índice

O sistema DEVE desabilitar todos os botões da aplicação **e os comboboxes de período e amostragem** quando um botão de índice (IBOV, IDIV, IFIX) for pressionado, desde o início do download do portfólio até a finalização completa do processamento dos dados. Ao finalizar, os botões e comboboxes DEVEM retornar aos seus estados anteriores (habilitado/readonly ou desabilitado).

#### Scenario: Comboboxes desabilitados durante carregamento do IBOV
- **WHEN** o usuário clica no botão "IBOV"
- **THEN** todos os botões da aplicação E os comboboxes de período e amostragem DEVEM ser desabilitados imediatamente

#### Scenario: Comboboxes restaurados após processamento do IBOV
- **WHEN** o processamento do IBOV finaliza com sucesso
- **THEN** os comboboxes DEVEM retornar ao estado "readonly"

#### Scenario: Comboboxes restaurados mesmo em caso de erro
- **WHEN** o processamento do IBOV falha (erro de rede, API, ou parsing)
- **THEN** os comboboxes DEVEM ser restaurados ao estado "readonly", mesmo com a falha

#### Scenario: Concorrência ignorada
- **WHEN** o usuário clica em "IBOV" e, enquanto o processamento ocorre, clica em "IFIX"
- **THEN** o segundo clique DEVE ser ignorado e o sistema DEVE continuar o processamento do IBOV sem interrupção

### Requirement: Botão Carregar também dispara loading state

O sistema DEVE desabilitar todos os botões da aplicação **e os comboboxes de período e amostragem** quando o botão "Carregar" (ou Enter/F5) for pressionado, com o mesmo comportamento dos botões de índice.

#### Scenario: Combos desabilitados ao pressionar Carregar
- **WHEN** o usuário clica no botão "Carregar" (ou pressiona Enter/F5)
- **THEN** os comboboxes de período e amostragem DEVEM ser desabilitados durante o processamento e restaurados ao finalizar

### Requirement: Recarga por mudança de combo também dispara loading state

Quando a mudança de seleção em um combobox disparar uma recarga automática (dados já carregados), o sistema DEVE desabilitar todos os controles (incluindo os próprios comboboxes) durante o processamento, com o mesmo comportamento de uma carga manual.

#### Scenario: Mudança de combo com dados carregados desabilita controles
- **WHEN** o usuário tem dados carregados e seleciona um novo período/amostragem
- **THEN** os comboboxes DEVEM ser desabilitados durante a recarga e restaurados ao finalizar

### Requirement: Cursor de espera durante processamento

O sistema DEVE exibir o cursor "watch" durante todo o período em que os botões estiverem desabilitados, incluindo a análise fundamentalista executada em background, e restaurar o cursor padrão somente após a conclusão dessa análise, mesmo quando os dados forem servidos do cache. O cursor "watch" DEVE ser aplicado a todos os widgets interativos da janela, inclusive os que definem cursor próprio (botões, lista de tickers, comboboxes e data entry), e cada widget DEVE ter o cursor anterior restaurado ao final da operação. Quando uma análise fundamentalista for substituída por outra antes de concluir, o sistema DEVE contabilizar o término do job substituído de forma que o cursor padrão seja restaurado assim que a última análise ativa concluir, sem deixar o cursor "watch" preso. Uma falha ao processar uma mensagem do job (por exemplo, um erro ao renderizar um painel com o resultado) NÃO DEVE impedir o encerramento do job nem a restauração do cursor e dos controles.

O estado ocupado DEVE ter uma única autoridade, que contabiliza referências de operações concorrentes: cada início de operação incrementa a contagem e cada término a decrementa, e o cursor só é alterado na transição de zero para uma operação ativa e restaurado na transição de volta a zero. Nenhum caminho de operação DEVE alterar o cursor fora dessa autoridade, de modo que operações que começam e terminam sobrepostas não apaguem nem deixem preso o cursor "watch" de outra operação ainda ativa. Cada widget DEVE ser restaurado ao cursor que tinha antes da primeira operação da contagem, e não ao valor capturado por uma operação aninhada.

O cursor padrão DEVE ser restaurado mesmo quando uma operação falha ao iniciar ou publicar seu job após já ter sido contabilizada, e quando a aquisição de documentos em background trava ou morre sem publicar o término, aplicando o mesmo watchdog de inatividade/liveness usado pela análise fundamentalista. O cursor exibido DEVE ser reafirmado enquanto a contagem estiver ativa, de modo que cursores transitórios geridos pelo toolkit (como o cursor de redimensionamento sobre separadores de coluna de tabelas e sobre sashes de painéis divididos) não sobreponham nem ressuscitem o cursor "watch" em um widget isolado. Os dois grids da tabela de Fundamentos (colunas congeladas e campos roláveis) DEVEM apresentar sempre o mesmo cursor entre si.

Ao capturar o cursor de repouso de cada widget para o estado ocupado, o sistema DEVE ignorar os cursores transitórios geridos pelo toolkit para redimensionamento — o cursor de separador de coluna de tabelas e os cursores de sash de painéis divididos — mesmo quando o Tk os devolva como lista Tcl em vez de string; esses valores NUNCA DEVEM ser usados como baseline da restauração nem reaplicados ao final da operação. Se a restauração do cursor de repouso de um widget falhar, o sistema DEVE aplicar o cursor padrão, de modo que o widget não permaneça com o cursor de espera "watch".

#### Scenario: Cursor watch ao clicar em índice

- **WHEN** o usuário clica em "IBOV"
- **THEN** o cursor DEVE mudar para "watch" imediatamente e retornar ao padrão quando o processamento finalizar

#### Scenario: Cursor watch durante a análise fundamentalista
- **WHEN** a análise fundamentalista em background é iniciada após a carga principal
- **THEN** o cursor DEVE permanecer "watch" até a análise fundamentalista concluir

#### Scenario: Cursor watch com dados em cache
- **WHEN** todos os dados fundamentalistas são servidos do cache
- **THEN** o cursor DEVE permanecer "watch" enquanto a carga ocorre

#### Scenario: Cursor watch sobrepõe cursores próprios
- **WHEN** uma operação longa está em andamento e o ponteiro está sobre um botão ou sobre a lista de tickers
- **THEN** o cursor exibido DEVE ser "watch", e não o cursor próprio do widget

#### Scenario: Cursores próprios restaurados
- **WHEN** a operação longa finaliza
- **THEN** cada widget DEVE recuperar o cursor que tinha antes da operação

#### Scenario: Cursor restaurado após análise fundamentalista substituída
- **WHEN** uma nova análise fundamentalista é iniciada enquanto uma anterior ainda está em andamento e a nova análise conclui
- **THEN** o cursor DEVE retornar ao padrão assim que a última análise ativa concluir

#### Scenario: Cursor não fica preso sobre a tabela de Fundamentos
- **WHEN** o usuário reinicia a análise fundamentalista (duplo clique em "Atualizar fundamentos" ou F5) e a análise seguinte termina
- **THEN** o cursor exibido sobre a tabela da sub-aba "Fundamentos" DEVE voltar ao cursor original, não permanecendo "watch"

#### Scenario: Cursor restaurado mesmo com falha ao processar o resultado
- **WHEN** ocorre um erro ao processar o resultado da análise fundamentalista (por exemplo, ao renderizar a tabela de Fundamentos)
- **THEN** o job DEVE ser encerrado e o cursor DEVE retornar ao padrão, sem permanecer "watch"

#### Scenario: Cursor restaurado quando a análise trava
- **WHEN** a análise fundamentalista fica sem progresso por tempo prolongado ou a thread termina sem publicar o resultado
- **THEN** o sistema DEVE encerrar a análise e restaurar o cursor e os controles, registrando um aviso no log

#### Scenario: Cursor restaurado quando a aquisição de documentos trava
- **WHEN** a aquisição de documentos fica sem progresso por tempo prolongado ou a thread termina sem publicar o término
- **THEN** o sistema DEVE encerrar o job, restaurar o cursor e os controles, e registrar um aviso no log

#### Scenario: Cursor restaurado quando uma operação falha ao iniciar o job
- **WHEN** uma operação é contabilizada e falha ao iniciar ou publicar seu job em background
- **THEN** o término da operação DEVE ser contabilizado e o cursor DEVE retornar ao padrão

#### Scenario: Operações sobrepostas não apagam o cursor uma da outra
- **WHEN** duas operações começam e terminam sobrepostas
- **THEN** o cursor DEVE permanecer "watch" até a última operação ativa terminar e então ser restaurado ao valor anterior à primeira operação

#### Scenario: Cursor de redimensionamento não sobrepõe o cursor watch
- **WHEN** uma operação está em andamento e o ponteiro passa sobre o separador de coluna de uma tabela ou sobre o sash de um painel dividido
- **THEN** o cursor exibido DEVE permanecer "watch"
#### Scenario: Grids congelado e rolável da tabela de Fundamentos sincronizados

- **WHEN** uma operação está em andamento ou termina com o ponteiro sobre a tabela da sub-aba "Fundamentos"
- **THEN** os dois grids da tabela DEVEM exibir o mesmo cursor, voltando ambos ao cursor original ao final

#### Scenario: Baseline do cursor ignora o separador de coluna ao iniciar a operação

- **WHEN** uma operação entra no estado ocupado com o ponteiro sobre o separador de uma coluna do grid rolável da tabela de Fundamentos
- **THEN** o baseline capturado para esse grid DEVE ser o cursor de repouso (não o cursor transitório de redimensionamento) e, ao final da operação, o cursor DEVE voltar ao cursor original, sem permanecer "watch"

#### Scenario: Baseline em forma de lista do Tk

- **WHEN** o Tk devolve o cursor de repouso de um widget como uma lista (por exemplo `('sb_h_double_arrow',)`)
- **THEN** o sistema DEVE normalizá-la para o nome do cursor e tratar os cursores transitórios como repouso, nunca os usando como baseline

#### Scenario: Falha ao restaurar o cursor de repouso

- **WHEN** a restauração do baseline de um widget falha durante a saída do estado ocupado
- **THEN** o widget DEVE voltar ao cursor padrão, não permanecendo com o cursor "watch"

### Requirement: Controles desabilitados durante a análise fundamentalista

O sistema DEVE manter todos os botões, comboboxes, data entry e a lista de tickers desabilitados durante toda a análise fundamentalista em background, da mesma forma que ocorre durante a carga histórica, restaurando-os aos estados anteriores somente quando a análise concluir. Isso inclui a análise disparada manualmente pelo botão "Atualizar fundamentos", que DEVE desabilitar os controles ao iniciar e restaurá-los ao concluir. Enquanto houver uma análise fundamentalista ativa, o sistema DEVE impedir o início de uma nova análise a partir do mesmo controle, de modo que os estados originais dos controles nunca fiquem presos.

#### Scenario: Controles permanecem desabilitados após a carga histórica
- **WHEN** a carga histórica termina e a análise fundamentalista em background é iniciada
- **THEN** os controles DEVEM permanecer desabilitados durante a análise

#### Scenario: Controles restaurados ao final da análise
- **WHEN** a análise fundamentalista conclui
- **THEN** os controles DEVEM ser restaurados aos estados anteriores

#### Scenario: Estados originais preservados em operações sobrepostas
- **WHEN** uma nova operação é iniciada enquanto os controles já estão desabilitados
- **THEN** os estados originais dos controles DEVEM ser preservados e restaurados ao final

#### Scenario: Controles desabilitados no disparo manual
- **WHEN** o usuário clica em "Atualizar fundamentos"
- **THEN** os controles DEVEM ser desabilitados durante a análise e restaurados quando ela concluir

#### Scenario: Reinício da análise não deixa controles presos
- **WHEN** o usuário reinicia a análise fundamentalista antes de a anterior concluir
- **THEN** os controles DEVEM ser restaurados aos estados originais quando a última análise ativa concluir
