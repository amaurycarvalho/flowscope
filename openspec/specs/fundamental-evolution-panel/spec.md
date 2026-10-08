# fundamental-evolution-panel Specification

## Purpose
Apresenta graficamente a evolução temporal dos principais fundamentos de um ticker a partir das observações retidas no cache histórico, permitindo perceber tendências de preço, valor patrimonial, renda e base de cotistas ao longo das datas observadas.

## Requirements

### Requirement: Origem exclusiva do cache histórico

O sistema DEVE construir a evolução do ticker apenas a partir das observações retidas no cache histórico de fundamentos, sem executar qualquer aquisição de rede ao abrir ou atualizar a sub-aba.

#### Scenario: Abertura sem aquisição

- **WHEN** o usuário seleciona a sub-aba "Evolução dos Fundamentos" com o ticker selecionado
- **THEN** o sistema DEVE montar as séries apenas com as observações do cache histórico, sem consultar Fundamentus, B3, CVM ou qualquer fonte remota

#### Scenario: Apenas observações retidas

- **WHEN** o cache do ticker possui observações dentro da janela de retenção
- **THEN** o sistema DEVE usar somente essas observações, ignorando as expiradas

### Requirement: Oito campos fundamentalistas

O sistema DEVE representar a evolução dos campos Cotação, VP (VP/Cota), P/VP, Dividend Yield, Último dividendo, Nº de cotistas, Nº de cotas e `Shorts%`, cada um associado à sua observação datada no cache. O `Shorts%` corresponde à métrica já calculada na análise fundamentalista (ações alugadas ÷ *free float* ou total emitido) e DEVE ser exibido em notação percentual com uma casa decimal, igual à coluna `Shorts%` da tabela de Fundamentos.

#### Scenario: Todos os campos representados

- **WHEN** a sub-aba é exibida para um ticker com histórico
- **THEN** o sistema DEVE apresentar uma série para cada um dos oito campos

#### Scenario: Campo ausente em uma observação

- **WHEN** uma observação não possui valor para um dos campos
- **THEN** o sistema NÃO DEVE inventar um valor, deixando uma lacuna na série daquele campo

#### Scenario: Campo sem nenhum valor no histórico

- **WHEN** nenhuma observação retida possui valor para um dos campos
- **THEN** o painel daquele campo DEVE indicar ausência de dado, mantendo os demais painéis visíveis

#### Scenario: Shorts% representado como percentual com uma casa decimal

- **WHEN** um ticker possui observações com `Shorts%` no cache histórico
- **THEN** o painel do campo `Shorts%` DEVE exibir os pontos em notação percentual com uma casa decimal, e os demais campos DEVEM usar a sua própria formatação

### Requirement: Representação em small multiples

O sistema DEVE representar os oito campos como small multiples — um mini-gráfico de linha por campo, com eixo de datas compartilhado e escala própria por campo — preservando a leitura dos valores absolutos.

#### Scenario: Um painel por campo

- **WHEN** a sub-aba é exibida com histórico disponível
- **THEN** o sistema DEVE exibir oito painéis, um por campo, com título identificando o campo e sua unidade

#### Scenario: Escalas independentes

- **WHEN** dois campos possuem ordens de grandeza diferentes, como Cotação em reais e Nº de cotas
- **THEN** cada painel DEVE usar a sua própria escala no eixo vertical, sem misturar unidades no mesmo eixo

### Requirement: Ordenação cronológica crescente

O sistema DEVE exibir as datas amostradas em ordem cronológica crescente, da mais antiga para a mais recente.

#### Scenario: Eixo do tempo crescente

- **WHEN** a sub-aba é exibida com histórico disponível
- **THEN** o eixo de datas DEVE estar ordenado da observação mais antiga à mais recente

### Requirement: Estado vazio

O sistema DEVE exibir um estado vazio explícito quando o ticker não possuir observações retidas no cache histórico.

#### Scenario: Sem histórico para o ticker

- **WHEN** a sub-aba é exibida para um ticker sem observações no cache
- **THEN** o sistema DEVE exibir uma mensagem de ausência de histórico, sem lançar erro e sem acionar aquisição

### Requirement: Legibilidade para leigo

O sistema DEVE formatar os valores de cada campo de forma legível, com unidade adequada e destaque da observação mais recente, para que um usuário leigo compreenda a direção da evolução.

#### Scenario: Formatação por tipo de campo

- **WHEN** os valores são exibidos
- **THEN** campos monetários DEVEM ser apresentados em reais, o Dividend Yield e o P/VP em percentual ou razão conforme a natureza do campo, e as contagens como inteiros

#### Scenario: Destaque do valor mais recente

- **WHEN** a sub-aba é exibida com histórico disponível
- **THEN** o sistema DEVE destacar e anotar o valor mais recente de cada campo

### Requirement: Formato das datas no eixo

O sistema DEVE rotular as datas do eixo de todos os painéis da evolução dos fundamentos com dia, mês e ano, no formato `DD/MM/AA`.

#### Scenario: Rótulo de data com dia, mês e ano

- **WHEN** a sub-aba é exibida com histórico disponível
- **THEN** cada rótulo de data do eixo DEVE exibir dia, mês e ano (por exemplo, `01/09/26`), e não apenas mês e ano

### Requirement: Tooltip de inspeção dos pontos

O sistema DEVE exibir, ao passar o mouse sobre um ponto de qualquer painel da evolução dos fundamentos, um tooltip com a data e o valor correspondente daquele ponto, formatado conforme o tipo do campo.

#### Scenario: Tooltip com data e valor ao pairar sobre um ponto

- **WHEN** o usuário posiciona o mouse sobre um ponto de um dos painéis
- **THEN** o sistema DEVE exibir a data do ponto no formato `DD/MM/AA` e o valor do ponto formatado conforme o tipo do campo

#### Scenario: Tooltip some ao sair do painel

- **WHEN** o cursor deixa a área de um painel ou não está próximo de nenhum ponto
- **THEN** o tooltip DEVE ser ocultado

### Requirement: Leitura do cache histórico fora da thread da interface

O sistema DEVE ler as observações do cache histórico e montar as séries da sub-aba "Evolução dos Fundamentos" fora da thread da interface, aplicando o resultado por evento na thread do Tk, com estado de carregamento durante a leitura. A origem continua sendo exclusivamente o cache histórico, sem aquisição de rede.

#### Scenario: Seleção com estado de carregamento
- **WHEN** o usuário seleciona a sub-aba "Evolução dos Fundamentos" com um ticker selecionado
- **THEN** a leitura do cache histórico DEVE ocorrer fora da thread da interface e as séries DEVEM ser aplicadas por evento ao concluir

#### Scenario: Interface responsiva durante a leitura
- **WHEN** a leitura do cache histórico está em andamento
- **THEN** a thread do Tk DEVE continuar processando eventos

#### Scenario: Sem aquisição de rede
- **WHEN** as séries são montadas
- **THEN** nenhuma consulta a Fundamentus, B3, CVM ou outra fonte remota DEVE ser feita

#### Scenario: Leitura obsoleta descartada
- **WHEN** o ticker apresentado muda antes de uma leitura em andamento concluir
- **THEN** o resultado da leitura anterior NÃO DEVE ser aplicado ao novo ticker

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
