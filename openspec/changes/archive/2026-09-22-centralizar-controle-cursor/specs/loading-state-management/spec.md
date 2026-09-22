## MODIFIED Requirements

### Requirement: Cursor de espera durante processamento

O sistema DEVE exibir o cursor "watch" durante todo o período em que os botões estiverem desabilitados, incluindo a análise fundamentalista executada em background, e restaurar o cursor padrão somente após a conclusão dessa análise, mesmo quando os dados forem servidos do cache. O cursor "watch" DEVE ser aplicado a todos os widgets interativos da janela, inclusive os que definem cursor próprio (botões, lista de tickers, comboboxes e data entry), e cada widget DEVE ter o cursor anterior restaurado ao final da operação. Quando uma análise fundamentalista for substituída por outra antes de concluir, o sistema DEVE contabilizar o término do job substituído de forma que o cursor padrão seja restaurado assim que a última análise ativa concluir, sem deixar o cursor "watch" preso. Uma falha ao processar uma mensagem do job (por exemplo, um erro ao renderizar um painel com o resultado) NÃO DEVE impedir o encerramento do job nem a restauração do cursor e dos controles.

O estado ocupado DEVE ter uma única autoridade, que contabiliza referências de operações concorrentes: cada início de operação incrementa a contagem e cada término a decrementa, e o cursor só é alterado na transição de zero para uma operação ativa e restaurado na transição de volta a zero. Nenhum caminho de operação DEVE alterar o cursor fora dessa autoridade, de modo que operações que começam e terminam sobrepostas não apaguem nem deixem preso o cursor "watch" de outra operação ainda ativa. Cada widget DEVE ser restaurado ao cursor que tinha antes da primeira operação da contagem, e não ao valor capturado por uma operação aninhada.

O cursor padrão DEVE ser restaurado mesmo quando uma operação falha ao iniciar ou publicar seu job após já ter sido contabilizada, e quando a aquisição de documentos em background trava ou morre sem publicar o término, aplicando o mesmo watchdog de inatividade/liveness usado pela análise fundamentalista. O cursor exibido DEVE ser reafirmado enquanto a contagem estiver ativa, de modo que cursores transitórios geridos pelo toolkit (como o cursor de redimensionamento sobre separadores de coluna de tabelas e sobre sashes de painéis divididos) não sobreponham nem ressuscitem o cursor "watch" em um widget isolado. Os dois grids da tabela de Fundamentos (colunas congeladas e campos roláveis) DEVEM apresentar sempre o mesmo cursor entre si.

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
