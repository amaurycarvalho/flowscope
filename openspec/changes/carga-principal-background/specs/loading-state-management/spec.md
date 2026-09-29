## MODIFIED Requirements

### Requirement: Botões desabilitados durante processamento de índice

O sistema DEVE desabilitar todos os botões da aplicação **e os comboboxes de período e amostragem** quando um botão de índice (IBOV, IDIV, IFIX) for pressionado, desde o início do download do portfólio até a finalização completa do processamento dos dados. Ao finalizar, os botões e comboboxes DEVEM retornar aos seus estados anteriores (habilitado/readonly ou desabilitado). Enquanto a carga principal executa em background, uma nova operação de carga distinta DEVE substituir a anterior, e o estado ocupado DEVE permanecer contínuo durante a substituição.

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
- **WHEN** o usuário aciona repetidamente o mesmo botão de índice enquanto o processamento correspondente ocorre
- **THEN** o acionamento repetido DEVE ser ignorado, sem iniciar carga duplicada

#### Scenario: Nova operação de carga substitui a anterior
- **WHEN** o usuário inicia uma carga (outro índice, "Carregar" ou troca de período/amostragem) enquanto uma carga principal está em andamento
- **THEN** a carga anterior DEVE ser cancelada e descartada, e a nova carga DEVE assumir o estado ocupado sem que os controles sejam restaurados entre as duas

## ADDED Requirements

### Requirement: Estado ocupado governado pelo job de background

O estado ocupado, o cursor "watch" e o bloqueio dos controles durante a carga principal DEVEM ser governados pelo ciclo de vida do job de carga em background: ao terminar por sucesso, erro ou cancelamento, o sistema DEVE restaurar controles e cursor. A transição de estado NÃO DEVE depender de um laço síncrono na thread do Tk.

#### Scenario: Restauração ao término do job de carga
- **WHEN** o job de carga principal termina por sucesso, erro ou cancelamento
- **THEN** os controles DEVEM voltar aos estados anteriores e o cursor "watch" DEVE ser removido

#### Scenario: Janela permanece responsiva durante a carga
- **WHEN** a carga principal está em andamento
- **THEN** a thread do Tk DEVE permanecer processando eventos, permitindo o repintar e o acionamento do botão de interromper

#### Scenario: Substituição sem quebra do estado ocupado
- **WHEN** uma carga é substituída por outra antes de concluir
- **THEN** a contagem de operações ativas DEVE permanecer equilibrada e o cursor NÃO DEVE ser restaurado entre as cargas
