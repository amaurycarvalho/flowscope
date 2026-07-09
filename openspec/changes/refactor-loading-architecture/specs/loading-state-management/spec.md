## Purpose

Define the behavior and architecture for disabling all buttons during portfolio download and data processing, with automatic restoration of previous states on completion.

## ADDED Requirements

### Requirement: Botões desabilitados durante processamento de índice

O sistema DEVE desabilitar todos os botões da aplicação quando um botão de índice (IBOV, IDIV, IFIX) for pressionado, desde o início do download do portfólio até a finalização completa do processamento dos dados. Ao finalizar, os botões DEVEM retornar aos seus estados anteriores (habilitado ou desabilitado).

#### Scenario: Todos os botões desabilitados durante carregamento do IBOV

- **WHEN** o usuário clica no botão "IBOV"
- **THEN** todos os botões da aplicação DEVEM ser desabilitados imediatamente, incluindo botões de índice, carregar, hoje, salvar, editar, selecionar todos, desmarcar todos e copiar

#### Scenario: Botões restaurados ao estado anterior após processamento

- **WHEN** o processamento do IBOV finaliza com sucesso
- **THEN** os botões DEVEM retornar aos estados que tinham antes do clique: botões normalmente habilitados (índice, carregar, hoje) voltam a NORMAL, e o botão copiar mantém seu estado anterior (NORMAL se já havia dados carregados, DISABLED se não)

#### Scenario: Botões restaurados mesmo em caso de erro

- **WHEN** o processamento do IBOV falha (erro de rede, API, ou parsing)
- **THEN** os botões DEVEM ser restaurados aos seus estados anteriores, mesmo com a falha

#### Scenario: Cliques concorrentes ignorados durante processamento

- **WHEN** o usuário clica em "IBOV" e, enquanto o processamento ocorre, clica em "IFIX"
- **THEN** o segundo clique DEVE ser ignorado e o sistema DEVE continuar o processamento do IBOV sem interrupção

#### Scenario: Botão Carregar também dispara loading state

- **WHEN** o usuário clica no botão "Carregar" (ou pressiona Enter/F5)
- **THEN** todos os botões DEVEM ser desabilitados durante o processamento, com o mesmo comportamento dos botões de índice

#### Scenario: Botão Hoje também dispara loading state

- **WHEN** o usuário clica no botão "Hoje"
- **THEN** todos os botões DEVEM ser desabilitados durante o processamento e restaurados ao finalizar

### Requirement: Cursor de espera durante processamento

O sistema DEVE exibir o cursor "watch" durante todo o período em que os botões estiverem desabilitados, e restaurar o cursor padrão ao finalizar.

#### Scenario: Cursor watch ao clicar em índice

- **WHEN** o usuário clica em "IBOV"
- **THEN** o cursor DEVE mudar para "watch" imediatamente e retornar ao padrão quando o processamento finalizar
