## MODIFIED Requirements

### Requirement: Cursor de espera durante processamento

O sistema DEVE exibir o cursor "watch" durante todo o período em que os botões estiverem desabilitados, incluindo a análise fundamentalista executada em background, e restaurar o cursor padrão somente após a conclusão dessa análise, mesmo quando os dados forem servidos do cache. O cursor "watch" DEVE ser aplicado a todos os widgets interativos da janela, inclusive os que definem cursor próprio (botões, lista de tickers, comboboxes e data entry), e cada widget DEVE ter o cursor anterior restaurado ao final da operação. Quando uma análise fundamentalista for substituída por outra antes de concluir, o sistema DEVE contabilizar o término do job substituído de forma que o cursor padrão seja restaurado assim que a última análise ativa concluir, sem deixar o cursor "watch" preso. Uma falha ao processar uma mensagem do job (por exemplo, um erro ao renderizar um painel com o resultado) NÃO DEVE impedir o encerramento do job nem a restauração do cursor e dos controles.

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
