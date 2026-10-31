# Spec Delta

## MODIFIED Requirements

### Requirement: Botão "Hoje" carrega dados automaticamente

O sistema DEVE, ao clicar no botão "Hoje", atualizar o DateEntry para a data corrente no fuso local do processo E executar imediatamente o carregamento de dados (mesma ação do botão "Carregar"), como se o usuário tivesse clicado em "Carregar" em sequência. O DateEntry DEVE usar a data local do processo como `maxdate` e NÃO DEVE usar a data em UTC para o botão "Hoje" nem para o limite superior do calendário.

#### Scenario: Clique no botão Hoje carrega dados do dia
- **WHEN** o usuário clica no botão "Hoje"
- **THEN** o DateEntry DEVE ser atualizado para a data atual E os dados DEVEM ser carregados para essa data, com o mesmo comportamento (loading state, statusbar, gráficos) do botão "Carregar"

#### Scenario: Data local na virada do dia
- **WHEN** o dia local já avançou enquanto o dia UTC ainda é o anterior
- **THEN** o botão "Hoje" e o `maxdate` usam a data local
- **THEN** a data UTC não é usada

## ADDED Requirements

### Requirement: Data de referência padrão no fuso local

Quando a data de referência for solicitada sem um DateEntry disponível, o sistema DEVE usar a data local do processo como fallback e NÃO DEVE usar a data em UTC.

#### Scenario: Fallback de referência
- **WHEN** a data de referência é solicitada sem um DateEntry disponível
- **THEN** o sistema usa a data local do processo como fallback
- **THEN** não usa a data UTC

### Requirement: Aba Feriados com árvore e texto somente leitura

A aba `Feriados` DEVE exibir um `ttk.Treeview` à esquerda e um textbox somente leitura à direita. A árvore DEVE ler apenas o cache do calendário na primeira exibição, e a navegação entre anos, meses e dias NÃO DEVE iniciar requisição de rede.

#### Scenario: Árvore é montada a partir do cache
- **WHEN** a aba é exibida pela primeira vez e há anos no cache
- **THEN** a árvore é montada somente com os dados do cache
- **THEN** nenhuma requisição de rede é iniciada

#### Scenario: Sem cache
- **WHEN** não há anos no cache
- **THEN** a árvore fica vazia
- **THEN** o textbox orienta a usar o botão de atualização

#### Scenario: Seleção não acessa a rede
- **WHEN** o usuário navega entre anos, meses e dias
- **THEN** nenhuma requisição de rede é iniciada

#### Scenario: Orientação da aba
- **WHEN** o usuário seleciona a aba `Feriados`
- **THEN** o `OrientationPanel` exibe o texto explicativo da aba
- **THEN** a aba não exige sub-notebook nem sub-aba selecionada

### Requirement: Árvore ano/mês/dia

A árvore DEVE ter ramos de ano, ramos de mês e folhas de dia. Anos DEVEM aparecer em ordem decrescente; cada ano DEVE ter apenas os meses com feriados, em ordem crescente; cada mês DEVE ter as folhas de dia em ordem crescente. Cada folha DEVE mostrar `DD` seguido do dia da semana abreviado entre parênteses (`dom`, `seg`, `ter`, `qua`, `qui`, `sex`, `sáb`).

#### Scenario: Ordenação da árvore
- **WHEN** há feriados em mais de um ano e em mais de um mês
- **THEN** os anos aparecem em ordem decrescente
- **THEN** os meses aparecem em ordem crescente dentro de cada ano
- **THEN** as folhas de dia aparecem em ordem crescente dentro de cada mês

#### Scenario: Folha mostra o dia da semana
- **WHEN** uma folha de dia é exibida
- **THEN** o rótulo é `DD (abreviatura)`, como `03 (sex)`

### Requirement: Seleção na árvore atualiza o textbox

Ao selecionar um ano, o textbox DEVE listar todos os feriados do ano agrupados por mês. Ao selecionar um mês, DEVE listar os feriados do mês dia a dia. Ao selecionar um dia, DEVE mostrar apenas o feriado daquele dia. O textbox DEVE ser somente leitura e cada linha DEVE conter dia, dia da semana abreviado e nome do feriado.

#### Scenario: Ano selecionado
- **WHEN** o usuário seleciona um ano
- **THEN** o textbox mostra os feriados agrupados por mês
- **THEN** cada linha contém dia, dia da semana abreviado e nome do feriado

#### Scenario: Mês selecionado
- **WHEN** o usuário seleciona um mês
- **THEN** o textbox mostra os feriados daquele mês, dia a dia
- **THEN** cada linha contém dia, dia da semana abreviado e nome do feriado

#### Scenario: Dia selecionado
- **WHEN** o usuário seleciona uma folha de dia
- **THEN** o textbox mostra o feriado daquele dia com data, dia da semana abreviado e nome

#### Scenario: Textbox somente leitura
- **WHEN** o usuário tenta editar o textbox
- **THEN** a edição NÃO é permitida

### Requirement: Atualização forçada na aba Feriados

A aba DEVE ter um botão de atualização com o ícone `view-refresh`. O botão DEVE forçar a revalidação dos anos exibidos, ignorando o TTL, e DEVE preservar o cache anterior em caso de falha. Sem anos no cache, o botão DEVE revalidar o ano corrente no fuso local e montar a árvore.

#### Scenario: Atualização bem-sucedida
- **WHEN** o usuário clica no botão de atualização
- **THEN** os anos exibidos são revalidados na ANBIMA
- **THEN** a árvore é reconstruída com os dados atualizados

#### Scenario: Árvore vazia atualiza o ano corrente
- **WHEN** o usuário clica no botão de atualização sem anos no cache
- **THEN** o ano corrente no fuso local é revalidado na ANBIMA
- **THEN** a árvore é montada com os feriados obtidos

#### Scenario: Falha preserva o conteúdo
- **WHEN** a atualização falha
- **THEN** a árvore e o textbox mantêm o conteúdo anterior
- **THEN** a barra de status indica a falha ou a defasagem

### Requirement: Indicador de carga e preservação de seleção

Enquanto a atualização da aba `Feriados` estiver em andamento, o botão DEVE usar o ícone `content-loading` e ficar desabilitado até o fim da operação. Ao reconstruir a árvore, a seleção anterior DEVE ser preservada quando ainda existir.

#### Scenario: Indicador de carga
- **WHEN** a atualização está em andamento
- **THEN** o botão usa o ícone `content-loading`
- **THEN** o botão fica desabilitado até o fim da operação

#### Scenario: Seleção preservada
- **WHEN** a árvore é reconstruída e a seleção anterior ainda existe
- **THEN** a seleção anterior é restaurada
- **THEN** o textbox reflete a seleção restaurada
