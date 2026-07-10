## MODIFIED Requirements

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
