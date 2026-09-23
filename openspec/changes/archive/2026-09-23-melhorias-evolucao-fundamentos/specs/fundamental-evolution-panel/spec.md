## RENAMED Requirements

- FROM: `### Requirement: Sete campos fundamentalistas`
- TO: `### Requirement: Oito campos fundamentalistas`

## MODIFIED Requirements

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

## ADDED Requirements

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
