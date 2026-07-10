## ADDED Requirements

### Requirement: Combobox de seleção de período

O sistema DEVE exibir um combobox do tipo `ttk.Combobox` em modo read-only na barra superior, posicionado entre o botão "Carregar" e o botão "Copiar dados CSV", com as opções: "Últimos 30 dias", "Últimos 60 dias (cache)", "Últimos 90 dias (cache)". O valor padrão DEVE ser "Últimos 30 dias".

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
