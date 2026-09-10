## MODIFIED Requirements

### Requirement: Última data-com
O sistema DEVE determinar, para um ticker, a data-com do dividendo mais recente consolidando o histórico de B3 (FII, primário), o histórico de proventos do Fundamentus (ações e fallback) e demais fontes secundárias, exibindo `N/A` quando não houver dado em nenhuma fonte.

#### Scenario: Data-com do provento mais recente
- **WHEN** o ticker possui dividendo com data-base em ao menos uma das fontes consolidadas
- **THEN** a última data-com DEVE ser a data-base do dividendo mais recente entre as fontes

#### Scenario: Data-com para ação
- **WHEN** o ticker é uma ação e o histórico de proventos do Fundamentus possui data-base
- **THEN** a última data-com DEVE ser a data do provento mais recente do histórico

#### Scenario: Sem proventos
- **WHEN** nenhuma fonte possui dividendo para o ticker
- **THEN** a última data-com DEVE ser `N/A`

### Requirement: Último dividendo
O sistema DEVE determinar, para um ticker, o valor do último dividendo consolidando o histórico de B3 (FII, primário), o histórico de proventos do Fundamentus (ações e fallback) e demais fontes secundárias, excluindo proventos de tipo `Amortização` e usando o `Dividendo/cota` do Fundamentus apenas quando não houver histórico nas demais fontes.

#### Scenario: Último dividendo de rendimento
- **WHEN** o ticker possui rendimentos na B3
- **THEN** o último dividendo DEVE ser o rendimento mais recente do histórico consolidado

#### Scenario: Último dividendo de ação
- **WHEN** o ticker é uma ação e possui histórico de proventos
- **THEN** o último dividendo DEVE ser o provento mais recente do histórico, com a respectiva data-base

#### Scenario: Fallback no Fundamentus
- **WHEN** nem a B3 nem o histórico de proventos possuem rendimentos para o ticker
- **THEN** o último dividendo DEVE usar o campo `Dividendo/cota` do Fundamentus

#### Scenario: Apenas amortização
- **WHEN** as fontes possuem somente proventos de tipo `Amortização`
- **THEN** o último dividendo DEVE ser `N/A`

### Requirement: Consolidação de fontes de dividendos
O sistema DEVE consolidar os dividendos de um ticker a partir da B3, do histórico de proventos do Fundamentus e de demais fontes secundárias, preservando a origem de cada valor e priorizando a fonte que tiver o dado mais recente, de modo que a ausência em uma fonte não deixe a coluna vazia quando outra fonte possuir o dado.

#### Scenario: Fonte primária sem o dado
- **WHEN** a B3 não possui um dividendo que existe em uma fonte secundária
- **THEN** o dividendo da fonte secundária DEVE ser utilizado

#### Scenario: Ação sem histórico na B3
- **WHEN** o ticker é uma ação (não coberta pela B3 de FIIs) e possui histórico no Fundamentus
- **THEN** os dividendos do Fundamentus DEVEM preencher data-com, último dividendo, dividendo anterior e tendência

#### Scenario: Origem preservada
- **WHEN** um dividendo é consolidado
- **THEN** a fonte que o forneceu DEVE ser registrada
