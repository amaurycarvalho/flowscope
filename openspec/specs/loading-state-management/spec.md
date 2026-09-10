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

O sistema DEVE exibir o cursor "watch" durante todo o período em que os botões estiverem desabilitados, incluindo a análise fundamentalista executada em background, e restaurar o cursor padrão somente após a conclusão dessa análise, mesmo quando os dados forem servidos do cache. O cursor "watch" DEVE ser aplicado a todos os widgets interativos da janela, inclusive os que definem cursor próprio (botões, lista de tickers, comboboxes e data entry), e cada widget DEVE ter o cursor anterior restaurado ao final da operação.

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

### Requirement: Controles desabilitados durante a análise fundamentalista

O sistema DEVE manter todos os botões, comboboxes, data entry e a lista de tickers desabilitados durante toda a análise fundamentalista em background, da mesma forma que ocorre durante a carga histórica, restaurando-os aos estados anteriores somente quando a análise concluir.

#### Scenario: Controles permanecem desabilitados após a carga histórica
- **WHEN** a carga histórica termina e a análise fundamentalista em background é iniciada
- **THEN** os controles DEVEM permanecer desabilitados durante a análise

#### Scenario: Controles restaurados ao final da análise
- **WHEN** a análise fundamentalista conclui
- **THEN** os controles DEVEM ser restaurados aos estados anteriores

#### Scenario: Estados originais preservados em operações sobrepostas
- **WHEN** uma nova operação é iniciada enquanto os controles já estão desabilitados
- **THEN** os estados originais dos controles DEVEM ser preservados e restaurados ao final
