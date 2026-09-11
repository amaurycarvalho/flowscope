## MODIFIED Requirements

### Requirement: Data de referência dos dados

O sistema DEVE expor, por ticker, a data de referência dos dados de mercado, usando `Data últ cot` do Fundamentus quando disponível e, na sua ausência, a data do último fechamento da B3 utilizado no cálculo, exibindo `N/A` quando nenhuma das fontes fornecer uma data.

#### Scenario: Data de referência disponível
- **WHEN** o Fundamentus informa `Data últ cot`
- **THEN** a data de referência DEVE ser essa data

#### Scenario: Fundamentus indisponível com preço da B3
- **WHEN** o Fundamentus não informa `Data últ cot` e a análise usa um fechamento da B3
- **THEN** a data de referência DEVE ser a data desse fechamento

#### Scenario: Data de referência indisponível
- **WHEN** não há data de última cotação nem preço de fechamento
- **THEN** a data de referência DEVE ser `N/A`
