## REMOVED Requirements

### Requirement: Amostragem Fibonacci das datas

**Reason**: A amostragem fixa em Fibonacci não refletia os comboboxes de período e de estilo de amostragem da barra superior, impedindo o usuário de compor os gráficos conforme a configuração selecionada.

**Migration**: A seleção de datas passa a observar a janela de período e o método selecionados (ver os requisitos "Janela de período da amostra" e "Amostragem conforme o método selecionado"). O método "Fibonacci" mantém o comportamento anterior (concentração nas datas recentes, extremos sempre presentes), agora limitado à janela.

## ADDED Requirements

### Requirement: Janela de período da amostra

O sistema DEVE restringir as observações exibidas na sub-aba "Evolução dos Fundamentos" à janela do período selecionado no combobox (30, 60 ou 90 dias corridos), ancorada na data de referência. Quando a janela não contiver nenhuma observação, o sistema DEVE ancorar na observação mais recente disponível no cache, mantendo a mesma largura de período. A origem continua sendo exclusivamente o cache histórico, sem aquisição de rede.

#### Scenario: Período delimita as datas exibidas

- **WHEN** a data de referência é `D`, o período selecionado é "Últimos 30 dias" e o cache do ticker possui observações antes e depois de `D - 30`
- **THEN** o sistema DEVE exibir apenas as observações no intervalo `[D - 30, D]`

#### Scenario: Janela vazia ancora na observação mais recente

- **WHEN** a janela ancorada na data de referência não contém nenhuma observação do ticker, mas o cache possui observações mais antigas
- **THEN** o sistema DEVE ancorar a janela na observação mais recente disponível, preservando a largura do período selecionado

#### Scenario: Sem observações no cache

- **WHEN** o ticker não possui nenhuma observação retida no cache
- **THEN** o sistema DEVE exibir o estado vazio, sem lançar erro e sem acionar aquisição

#### Scenario: Sem aquisição de rede pela janela

- **WHEN** as séries são montadas para qualquer combinação de período e método
- **THEN** nenhuma consulta a Fundamentus, B3, CVM ou outra fonte remota DEVE ser feita

### Requirement: Amostragem conforme o método selecionado

O sistema DEVE selecionar as datas exibidas a partir das observações disponíveis no cache dentro da janela, conforme o método selecionado no combobox de amostragem. A seleção DEVE preservar o contrato: a observação mais antiga e a mais recente da janela DEVEM estar sempre presentes; com duas ou menos observações, todas DEVEM ser exibidas; datas não observadas NÃO DEVEM ser inventadas; o resultado DEVE estar em ordem cronológica crescente e sem duplicatas.

#### Scenario: Fibonacci concentra nas datas recentes

- **WHEN** o método selecionado é "Fibonacci"
- **THEN** as datas selecionadas DEVEM se concentrar nas observações mais recentes da janela, com intervalos crescentes rumo ao passado, incluindo sempre as observações mais antiga e mais recente

#### Scenario: Fibonacci reverso concentra nas datas distantes

- **WHEN** o método selecionado é "Fibonacci reverso"
- **THEN** as datas selecionadas DEVEM se concentrar nas observações mais antigas da janela, com intervalos crescentes rumo ao presente, incluindo sempre as observações mais antiga e mais recente

#### Scenario: Fibonacci duplo concentra nas margens

- **WHEN** o método selecionado é "Fibonacci duplo"
- **THEN** as datas selecionadas DEVEM se concentrar nas duas margens da janela, incluindo ao menos uma observação próxima do centro, além das extremidades

#### Scenario: Monte Carlo inclui extremos e intermediárias aleatórias

- **WHEN** o método selecionado é "Monte Carlo"
- **THEN** as datas selecionadas DEVEM incluir as observações mais antiga e mais recente da janela e uma amostra aleatória das observações intermediárias

#### Scenario: Monte Carlo duplo inclui mais intermediárias

- **WHEN** o método selecionado é "Monte Carlo duplo"
- **THEN** as datas selecionadas DEVEM incluir as extremidades e uma amostra aleatória de observações intermediárias maior que a de "Monte Carlo"

#### Scenario: Todos os dias exibe todas as observações

- **WHEN** o método selecionado é "Todos os dias"
- **THEN** todas as observações do ticker dentro da janela DEVEM ser exibidas

#### Scenario: Extremos sempre presentes

- **WHEN** a janela contém três ou mais observações, qualquer que seja o método
- **THEN** a observação mais antiga e a mais recente da janela DEVEM estar entre as datas exibidas

#### Scenario: Poucas observações

- **WHEN** a janela contém menos de três observações, qualquer que seja o método
- **THEN** o sistema DEVE exibir todas as observações disponíveis, sem repetir datas

#### Scenario: Amostra Monte Carlo estável entre renders

- **WHEN** o método é "Monte Carlo" ou "Monte Carlo duplo" e o ticker, a janela e o conjunto de observações não mudam
- **THEN** a amostra exibida DEVE ser a mesma em renders sucessivos

### Requirement: Atualização ao mudar os filtros

O sistema DEVE remontar as séries da sub-aba "Evolução dos Fundamentos" quando o período ou o método de amostragem mudar, mesmo que não haja dados da B3 carregados, aplicando o resultado na thread da interface e descartando resultados produzidos por uma configuração anterior.

#### Scenario: Mudança de período re-renderiza

- **WHEN** a sub-aba está visível e o usuário altera o combobox de período
- **THEN** o sistema DEVE remontar e redesenhar as séries com a nova janela

#### Scenario: Mudança de método re-renderiza

- **WHEN** a sub-aba está visível e o usuário altera o combobox de amostragem
- **THEN** o sistema DEVE remontar e redesenhar as séries com o novo método

#### Scenario: Mudança sem dados B3 carregados

- **WHEN** não há dados da B3 carregados e o usuário altera período ou método
- **THEN** o painel DEVE ser remontado a partir do cache, sem depender de carga corrente

#### Scenario: Resultado obsoleto descartado

- **WHEN** uma leitura em andamento termina após o período ou o método terem mudado
- **THEN** o resultado da configuração anterior NÃO DEVE ser aplicado ao painel
