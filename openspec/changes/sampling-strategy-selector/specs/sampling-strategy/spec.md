## ADDED Requirements

### Requirement: Seleção de período de análise

O sistema DEVE exibir um combobox na barra superior com as opções de período: "Últimos 30 dias" (default), "Últimos 60 dias (cache)", "Últimos 90 dias (cache)". O combobox DEVE ser do tipo read-only (apenas seleção).

#### Scenario: Período default é 30 dias

- **WHEN** o usuário abre a aplicação pela primeira vez
- **THEN** o combobox de período DEVE exibir "Últimos 30 dias" como valor selecionado

#### Scenario: Seleção de período 60 dias

- **WHEN** o usuário seleciona "Últimos 60 dias (cache)" no combobox de período
- **THEN** o sistema DEVE configurar a janela de análise para 60 dias corridos

### Requirement: Seleção de método de amostragem

O sistema DEVE exibir um combobox na barra superior com as opções de amostragem: "Fibonacci" (default), "Fibonacci reverso", "Fibonacci duplo", "Monte Carlos", "Monte Carlos duplo", "Todos os dias". O combobox DEVE ser do tipo read-only.

#### Scenario: Amostragem default é Fibonacci

- **WHEN** o usuário abre a aplicação pela primeira vez
- **THEN** o combobox de amostragem DEVE exibir "Fibonacci" como valor selecionado

#### Scenario: Seleção de amostragem Monte Carlos

- **WHEN** o usuário seleciona "Monte Carlos" no combobox de amostragem
- **THEN** o sistema DEVE configurar a amostragem para selecionar a data mais recente, a data mais antiga do período e 5 dias aleatórios intermediários

### Requirement: Geração de datas conforme período e amostragem

O sistema DEVE gerar a lista de datas para download com base na combinação de período e método de amostragem selecionados, conforme as regras abaixo.

#### Scenario: Fibonacci em 30 dias

- **WHEN** período=30 e amostragem=Fibonacci
- **THEN** as datas geradas DEVEM ser: ref_date - 1, -2, -3, -5, -8, -13, -21 (ajustadas para próximo dia útil)

#### Scenario: Fibonacci reverso em 30 dias

- **WHEN** período=30 e amostragem=Fibonacci reverso
- **THEN** as datas geradas DEVEM ser: ref_date - 22 + d, onde d ∈ {1,2,3,5,8,13,21}

#### Scenario: Fibonacci duplo em 30 dias

- **WHEN** período=30 e amostragem=Fibonacci duplo
- **THEN** as datas geradas DEVEM ser: ref_date - 22 + d, onde d ∈ {1,2,3,13,19,20,21}

#### Scenario: Monte Carlos em 30 dias

- **WHEN** período=30 e amostragem=Monte Carlos
- **THEN** as datas geradas DEVEM ser: ref_date - 1, ref_date - 30 (ou mais próxima disponível), e 5 dias aleatórios entre a primeira e a última (excluindo ambas)

#### Scenario: Monte Carlos duplo em 30 dias

- **WHEN** período=30 e amostragem=Monte Carlos duplo
- **THEN** as datas geradas DEVEM ser: ref_date - 1, ref_date - 30 (ou mais próxima disponível), e 12 dias aleatórios entre a primeira e a última (excluindo ambas)

#### Scenario: Todos os dias em 30 dias

- **WHEN** período=30 e amostragem=Todos os dias
- **THEN** as datas geradas DEVEM ser todos os dias de ref_date - 30 até ref_date - 1

#### Scenario: Fibonacci em 60 dias

- **WHEN** período=60 e amostragem=Fibonacci
- **THEN** as datas geradas DEVEM incluir offsets de Fibonacci até 55: 1, 2, 3, 5, 8, 13, 21, 34, 55

#### Scenario: Fibonacci em 90 dias

- **WHEN** período=90 e amostragem=Fibonacci
- **THEN** as datas geradas DEVEM incluir offsets de Fibonacci até 89: 1, 2, 3, 5, 8, 13, 21, 34, 55, 89

### Requirement: Cache-only para períodos acima de 30 dias

Quando o período selecionado for 60 ou 90 dias, o sistema DEVE utilizar apenas dados já existentes no cache local, sem realizar downloads da B3. Se uma data calculada não existir no cache, o sistema DEVE buscar a data mais próxima no cache dentro de uma margem de ±7 dias. Se nenhuma data for encontrada dentro dessa margem, a data DEVE ser pulada.

#### Scenario: Período 60 dias com cache populado

- **WHEN** período=60 e cache contém dados para os últimos 60 dias
- **THEN** o sistema DEVE usar os dados do cache sem fazer requisições HTTP

#### Scenario: Período 90 dias com cache parcial

- **WHEN** período=90, cache contém dados para ref_date - 1 e ref_date - 89, mas ref_date - 55 não está em cache
- **THEN** o sistema DEVE buscar a data mais próxima de ref_date - 55 no cache dentro de ±7 dias; se encontrar, usar essa data; se não, pular

#### Scenario: Período 30 dias faz download normalmente

- **WHEN** período=30 e cache não contém a data calculada
- **THEN** o sistema DEVE fazer o download da B3 e armazenar em cache

### Requirement: Ajuste para próximo dia útil

Cada data calculada DEVE ser ajustada individualmente para o próximo dia útil (aproximação local, sem cascata). Dias úteis são segunda a sexta, excluindo feriados nacionais brasileiros definidos na lista de feriados.

#### Scenario: Data calculada cai em sábado

- **WHEN** a data calculada é um sábado
- **THEN** o sistema DEVE avançar para o próximo domingo, depois segunda (se aplicável), até encontrar um dia útil

#### Scenario: Data calculada cai em feriado

- **WHEN** a data calculada é 25 de dezembro (Natal)
- **THEN** o sistema DEVE avançar para 26 de dezembro (se for dia útil) ou próximo dia útil seguinte

### Requirement: Deduplicação de datas

O sistema DEVE eliminar datas duplicadas da lista final, mantendo a ordem cronológica.

#### Scenario: Duas amostras calibram no mesmo dia útil

- **WHEN** duas datas de Fibonacci diferentes (ex: d-20 e d-22) ajustam para o mesmo dia útil
- **THEN** a data DEVE aparecer apenas uma vez na lista final

### Requirement: Recarga automática ao mudar seleção

Se o usuário modificar o combobox de período ou amostragem e houver dados previamente carregados (self._current_data não vazio), o sistema DEVE iniciar automaticamente uma nova carga com a nova configuração, respeitando o OperationGuard. Se não houver dados carregados, a mudança de seleção não DEVE ter efeito.

#### Scenario: Mudança de período com dados carregados

- **WHEN** o usuário tem dados carregados e seleciona "Últimos 60 dias (cache)"
- **THEN** o sistema DEVE iniciar nova carga com período=60 e a amostragem atualmente selecionada

#### Scenario: Mudança de amostragem sem dados carregados

- **WHEN** o usuário abre a aplicação (sem dados carregados) e seleciona "Monte Carlos"
- **THEN** o sistema NÃO DEVE executar nenhuma ação

### Requirement: Tooltips e textos explicativos

Cada combobox DEVE ter um tooltip fixo explicando sua função. Ao percorrer os itens de um combobox (via teclado), a barra de status DEVE exibir um texto explicativo do item atualmente selecionado. A carga de dados só DEVE ser acionada quando o usuário finalizar a seleção.

#### Scenario: Tooltip do combobox de período

- **WHEN** o usuário passa o mouse sobre o combobox de período
- **THEN** DEVE exibir o tooltip "Seleciona a janela de tempo para análise dos dados históricos"

#### Scenario: Texto explicativo na statusbar para Fibonacci

- **WHEN** o usuário navega até o item "Fibonacci" no combobox de amostragem
- **THEN** a barra de status DEVE exibir "Amostragem com offsets de Fibonacci: 1, 2, 3, 5, 8, 13, 21... até o limite do período."
