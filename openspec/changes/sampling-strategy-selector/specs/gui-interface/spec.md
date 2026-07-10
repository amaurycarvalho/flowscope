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

O sistema DEVE exibir um combobox do tipo `ttk.Combobox` em modo read-only na barra superior, posicionado entre o combobox de período e o botão "Copiar dados CSV", com as opções: "Fibonacci", "Fibonacci reverso", "Fibonacci duplo", "Monte Carlos", "Monte Carlos duplo", "Todos os dias". O valor padrão DEVE ser "Fibonacci".

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

### Requirement: Texto explicativo dinâmico na barra de status

Ao navegar pelos itens do combobox (via teclado ou mouse), a barra de status DEVE exibir temporariamente o texto explicativo do item selecionado. Apenas quando o usuário finaliza a seleção (evento `<<ComboboxSelected>>`) é que a ação de recarga (se aplicável) DEVE ser disparada.

#### Scenario: Texto explicativo ao navegar no período

- **WHEN** o usuário navega para o item "Últimos 60 dias (cache)" no combobox de período
- **THEN** a barra de status DEVE exibir "Janela de 60 dias corridos. Apenas dados já em cache serão utilizados — sem download da B3."

### Requirement: Recarga automática ao mudar seleção com dados carregados

O sistema DEVE monitorar o evento `<<ComboboxSelected>>` de ambos os comboboxes. Se houver dados previamente carregados (`self._current_data` não vazio), DEVE iniciar automaticamente uma nova carga de dados usando a nova configuração de período e amostragem, respeitando o OperationGuard.

#### Scenario: Mudança de período com dados carregados

- **WHEN** o usuário tem dados carregados e seleciona "Últimos 60 dias (cache)" no combobox de período
- **THEN** o sistema DEVE desabilitar os controles, iniciar nova carga com período=60, e restaurar os controles ao finalizar

#### Scenario: Mudança de amostragem sem dados carregados

- **WHEN** o usuário abre a aplicação (sem dados carregados) e seleciona "Monte Carlos duplo"
- **THEN** o sistema NÃO DEVE executar nenhuma ação além de atualizar o valor selecionado

### Requirement: Comboboxes desabilitados durante operações

Os comboboxes de período e amostragem DEVEM ser desabilitados (state=DISABLED) durante qualquer operação de carga ou processamento, juntamente com os demais botões da interface.

#### Scenario: Combos desabilitados durante carga

- **WHEN** o usuário clica em "Carregar"
- **THEN** os comboboxes de período e amostragem DEVEM ser desabilitados, impedindo qualquer alteração durante o processamento

#### Scenario: Combos restaurados após carga

- **WHEN** o processamento finaliza (com sucesso ou erro)
- **THEN** os comboboxes DEVEM retornar ao estado "readonly"
