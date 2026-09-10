## MODIFIED Requirements

### Requirement: Classificação por número de cotistas
O sistema DEVE expor, por ticker, o número atual de cotistas e sua classificação determinística (`MICRO`, `MUITO_PEQUENO`, `PEQUENO`, `MEDIO`, `GRANDE`, `MUITO_GRANDE`, `GIGANTE`) conforme os limiares absolutos fixos da RFC-006, exibindo `N/A` quando o número não estiver disponível.

#### Scenario: Cotistas em faixa média
- **WHEN** o número de cotistas está entre 5.001 e 35.000
- **THEN** a classificação DEVE ser `MEDIO` e o número de cotistas DEVE ser exposto

#### Scenario: Cotistas indisponíveis
- **WHEN** o número de cotistas não está disponível na fonte
- **THEN** o número e a classificação DEVEM ser `N/A`

### Requirement: Classificação por tamanho patrimonial
O sistema DEVE expor, por ticker, o tamanho patrimonial do fundo (patrimônio líquido) e sua classificação determinística (`MICRO`, `PEQUENO`, `MEDIO`, `GRANDE`, `MUITO_GRANDE`, `GIGANTE`) conforme os limiares absolutos fixos da RFC-006, exibindo `N/A` quando o valor não estiver disponível.

#### Scenario: Patrimônio em faixa grande
- **WHEN** o patrimônio líquido está entre R$ 250 milhões e R$ 500 milhões
- **THEN** a classificação DEVE ser `GRANDE` e o valor DEVE ser exposto

#### Scenario: Patrimônio indisponível
- **WHEN** o patrimônio líquido não está disponível na fonte
- **THEN** o valor e a classificação DEVEM ser `N/A`

### Requirement: Não elegível gera N/A
O sistema DEVE preencher cada métrica (FFO Yield, Dividend Yield, P/FFO, P/VP, FFO Momentum) sempre que a fonte fornecer os dados, independentemente do tipo ou sub-tipo do ticker, exibindo `N/A` somente quando o dado não existir.

#### Scenario: Métricas disponíveis na fonte
- **WHEN** a fonte fornece os dados de FFO, dividendo e patrimônio para o ticker
- **THEN** FFO Yield, Dividend Yield, P/FFO, P/VP e FFO Momentum DEVEM ser preenchidos

#### Scenario: Ação gera N/A nas métricas FFO
- **WHEN** um ativo do tipo `Papel` é analisado e a fonte não fornece FFO
- **THEN** somente as métricas dependentes de FFO DEVEM ser `N/A`

#### Scenario: Dado ausente na fonte
- **WHEN** a fonte não fornece o dado de uma métrica
- **THEN** somente aquela métrica DEVE ser `N/A`

## ADDED Requirements

### Requirement: Data de referência dos dados
O sistema DEVE expor, por ticker, a data de referência dos dados de mercado (`Data últ cot` do Fundamentus), exibindo `N/A` quando indisponível.

#### Scenario: Data de referência disponível
- **WHEN** o Fundamentus informa `Data últ cot`
- **THEN** a data de referência DEVE ser essa data

#### Scenario: Data de referência indisponível
- **WHEN** a data de última cotação não está disponível
- **THEN** a data de referência DEVE ser `N/A`
