## ADDED Requirements

### Requirement: Fallback de cotação, VP/Cota e data de referência

Quando o Fundamentus não fornecer cotação, valor patrimonial por cota ou a data de referência de mercado, o sistema DEVE preencher esses campos a partir das fontes de fallback — preço de fechamento da B3 e patrimônio do Informe Mensal da B3/CVM — registrando a origem do valor utilizado.

#### Scenario: Cotação ausente no Fundamentus
- **WHEN** o Fundamentus não fornece a cotação de um ticker e a B3 possui o último fechamento até a data de referência
- **THEN** o sistema DEVE usar o preço da B3 como `P (Cotação)`

#### Scenario: VP/Cota ausente no Fundamentus
- **WHEN** o Fundamentus não fornece `VP/Cota` e o patrimônio da B3 ou da CVM está disponível
- **THEN** o sistema DEVE preencher `VP (VP/Cota)` com o valor patrimonial por cota da fonte, ou derivá-lo de `patrimônio líquido / cotas`

#### Scenario: Data de referência ausente no Fundamentus
- **WHEN** o Fundamentus não fornece a data de última cotação e existe preço de fechamento da B3
- **THEN** o sistema DEVE usar a data do último fechamento da B3 como `Data de referência`

#### Scenario: Nenhuma fonte fornece o campo
- **WHEN** nem o Fundamentus nem a B3/CVM fornecem o campo
- **THEN** a coluna correspondente DEVE ser exibida como `N/A` sem impedir as demais
