## ADDED Requirements

### Requirement: P/L

O sistema DEVE expor, por ticker, a razão `P/L` como a quantidade de anos para recuperar o investimento. Para ativos do tipo `Papel`, DEVE usar o valor reportado pela fonte. Para FII, DEVE calcular `P/L = Preço / (Último dividendo × 12)`, anualizando o dividendo mensal, por função pura e determinística. O sistema DEVE exibir `N/A` quando o valor não estiver disponível ou o último dividendo for ausente ou zero.

#### Scenario: P/L de ação reportado pela fonte
- **WHEN** a fonte reporta `P/L` para um ativo do tipo `Papel`
- **THEN** o `P/L` DEVE ser o valor reportado

#### Scenario: P/L de FII calculado
- **WHEN** um FII possui preço `18,74` e último dividendo mensal `0,55`
- **THEN** o `P/L` DEVE ser aproximadamente `2,84`

#### Scenario: P/L indisponível
- **WHEN** o último dividendo de um FII é ausente ou zero, ou a fonte não reporta `P/L` para o Papel
- **THEN** o `P/L` DEVE ser `N/A`

## MODIFIED Requirements

### Requirement: Classificação por número de cotistas
O sistema DEVE expor, por ticker, o número atual de cotistas e sua classificação determinística (`MICRO`, `MUITO_PEQUENO`, `PEQUENO`, `MEDIO`, `GRANDE`, `MUITO_GRANDE`, `GIGANTE`) conforme os limiares absolutos fixos da RFC-006, exibindo `N/A` quando o número não estiver disponível. Para ativos do tipo `Papel`, o número de cotistas corresponde à quantidade de acionistas obtida da CVM, reutilizando a mesma classificação determinística.

#### Scenario: Cotistas em faixa média
- **WHEN** o número de cotistas está entre 5.001 e 35.000
- **THEN** a classificação DEVE ser `MEDIO` e o número de cotistas DEVE ser exposto

#### Scenario: Cotistas indisponíveis
- **WHEN** o número de cotistas não está disponível na fonte
- **THEN** o número e a classificação DEVEM ser `N/A`

#### Scenario: Acionistas de ação classificados
- **WHEN** um ativo do tipo `Papel` possui quantidade de acionistas obtida da CVM
- **THEN** o número de cotistas DEVE ser essa quantidade e a classificação DEVE usar os mesmos limiares determinísticos
