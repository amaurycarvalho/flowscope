## MODIFIED Requirements

### Requirement: Última data-com
O sistema DEVE determinar, para um ticker, a data-com do dividendo mais recente consolidando o histórico de B3 (primário), CVM (secundário) e Fundamentus (fallback), exibindo `N/A` quando não houver dado em nenhuma fonte.

#### Scenario: Data-com do provento mais recente
- **WHEN** o ticker possui dividendo com data-base em ao menos uma das fontes consolidadas
- **THEN** a última data-com DEVE ser a data-base do dividendo mais recente entre as fontes

#### Scenario: Sem proventos
- **WHEN** nenhuma fonte possui dividendo para o ticker
- **THEN** a última data-com DEVE ser `N/A`

### Requirement: Último dividendo
O sistema DEVE determinar, para um ticker, o valor do último dividendo consolidando o histórico de B3 (primário), CVM (secundário) e Fundamentus (fallback), excluindo proventos de tipo `Amortização` e usando o `Dividendo/cota` do Fundamentus apenas quando não houver histórico nas demais fontes.

#### Scenario: Último dividendo de rendimento
- **WHEN** o ticker possui rendimentos na B3
- **THEN** o último dividendo DEVE ser o rendimento mais recente do histórico consolidado

#### Scenario: Fallback no Fundamentus
- **WHEN** nem B3 nem CVM possuem histórico de rendimentos para o ticker
- **THEN** o último dividendo DEVE usar o campo `Dividendo/cota` do Fundamentus

#### Scenario: Apenas amortização
- **WHEN** as fontes possuem somente proventos de tipo `Amortização`
- **THEN** o último dividendo DEVE ser `N/A`

### Requirement: Tendência do dividendo
O sistema DEVE classificar a tendência do dividendo comparando diretamente o último dividendo com o dividendo imediatamente anterior, sem banda de tolerância: `Crescimento` quando o último é maior, `Redução` quando é menor e `Neutro` quando é igual. Sem dividendo anterior a tendência DEVE ser `N/A`.

#### Scenario: Dividendo subiu
- **WHEN** o último dividendo é maior que o anterior
- **THEN** a tendência DEVE ser `Crescimento`

#### Scenario: Dividendo caiu
- **WHEN** o último dividendo é menor que o anterior
- **THEN** a tendência DEVE ser `Redução`

#### Scenario: Dividendo manteve
- **WHEN** o último dividendo é igual ao anterior
- **THEN** a tendência DEVE ser `Neutro`

#### Scenario: Sem dividendo anterior
- **WHEN** o ticker possui apenas um dividendo (ou nenhum)
- **THEN** a tendência DEVE ser `N/A`

## ADDED Requirements

### Requirement: Consolidação de fontes de dividendos
O sistema DEVE consolidar os dividendos de um ticker a partir de B3, CVM e Fundamentus, preservando a origem de cada valor e priorizando a fonte que tiver o dado mais recente, de modo que a ausência em uma fonte não deixe a coluna vazia quando outra fonte possuir o dado.

#### Scenario: Fonte primária sem o dado
- **WHEN** a B3 não possui um dividendo que existe na CVM
- **THEN** o dividendo da CVM DEVE ser utilizado

#### Scenario: Origem preservada
- **WHEN** um dividendo é consolidado
- **THEN** a fonte que o forneceu DEVE ser registrada

## REMOVED Requirements

### Requirement: Banda de tendência configurável
**Reason**: A tendência passa a ser uma comparação direta (igual/acima/abaixo), sem banda de tolerância.
**Migration**: Remover o parâmetro de banda; a classificação usa a comparação estrita entre último e anterior.
