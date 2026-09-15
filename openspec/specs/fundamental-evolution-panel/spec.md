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

### Requirement: Amostragem Fibonacci das datas

O sistema DEVE selecionar as datas exibidas caminhando da observação mais recente para a mais antiga com intervalos sucessivos da sequência de Fibonacci (1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377 dias), aproximando cada alvo para a data de cache mais próxima e incluindo sempre a observação mais antiga e a mais recente disponíveis.

#### Scenario: Extremos sempre presentes

- **WHEN** o cache do ticker possui observações em várias datas
- **THEN** a data mais antiga e a data mais recente disponíveis DEVEM estar entre as datas exibidas

#### Scenario: Aproximação para datas existentes

- **WHEN** um alvo calculado pela sequência de Fibonacci não coincide com uma data do cache
- **THEN** o sistema DEVE usar a data de cache mais próxima do alvo, sem criar datas inexistentes

#### Scenario: Intervalos crescentes rumo ao passado

- **WHEN** as datas selecionadas são comparadas em ordem cronológica
- **THEN** os intervalos entre datas consecutivas DEVEM seguir a progressão de Fibonacci, ficando mais densos no presente e mais espaçados no passado

#### Scenario: Poucas observações

- **WHEN** o cache do ticker possui menos de três observações
- **THEN** o sistema DEVE exibir todas as observações disponíveis, sem repetir datas

### Requirement: Sete campos fundamentalistas

O sistema DEVE representar a evolução dos campos Cotação, VP (VP/Cota), P/VP, Dividend Yield, Último dividendo, Nº de cotistas e Nº de cotas, cada um associado à sua observação datada no cache.

#### Scenario: Todos os campos representados

- **WHEN** a sub-aba é exibida para um ticker com histórico
- **THEN** o sistema DEVE apresentar uma série para cada um dos sete campos

#### Scenario: Campo ausente em uma observação

- **WHEN** uma observação não possui valor para um dos campos
- **THEN** o sistema NÃO DEVE inventar um valor, deixando uma lacuna na série daquele campo

#### Scenario: Campo sem nenhum valor no histórico

- **WHEN** nenhuma observação retida possui valor para um dos campos
- **THEN** o painel daquele campo DEVE indicar ausência de dado, mantendo os demais painéis visíveis

### Requirement: Representação em small multiples

O sistema DEVE representar os sete campos como small multiples — um mini-gráfico de linha por campo, com eixo de datas compartilhado e escala própria por campo — preservando a leitura dos valores absolutos.

#### Scenario: Um painel por campo

- **WHEN** a sub-aba é exibida com histórico disponível
- **THEN** o sistema DEVE exibir sete painéis, um por campo, com título identificando o campo e sua unidade

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
