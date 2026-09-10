## MODIFIED Requirements

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

## ADDED Requirements

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

