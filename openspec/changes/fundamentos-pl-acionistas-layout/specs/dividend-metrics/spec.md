## MODIFIED Requirements

### Requirement: Tendência do dividendo
O sistema DEVE classificar a tendência do dividendo pela variação percentual entre o último dividendo e o dividendo imediatamente anterior, em cinco faixas com os rótulos descritivos: `Forte Alta` (≥ +5%), `Leve Alta` (> 0% e < +5%), `Estável` (= 0%), `Leve Queda` (≥ −5% e < 0%) e `Forte Queda` (< −5%). Sem dividendo anterior a tendência DEVE ser `N/A`.

#### Scenario: Dividendo subiu
- **WHEN** o último dividendo é maior que o anterior
- **THEN** a tendência DEVE ser `Forte Alta` quando a variação for maior ou igual a +5%, e `Leve Alta` caso contrário

#### Scenario: Dividendo caiu
- **WHEN** o último dividendo é menor que o anterior
- **THEN** a tendência DEVE ser `Forte Queda` quando a variação for menor que −5%, e `Leve Queda` caso contrário

#### Scenario: Dividendo manteve
- **WHEN** o último dividendo é igual ao anterior
- **THEN** a tendência DEVE ser `Estável`

#### Scenario: Sem dividendo anterior
- **WHEN** o ticker possui apenas um dividendo (ou nenhum)
- **THEN** a tendência DEVE ser `N/A`

#### Scenario: Limite de forte alta
- **WHEN** a variação percentual é exatamente +5%
- **THEN** a tendência DEVE ser `Forte Alta`

#### Scenario: Limite de leve queda
- **WHEN** a variação percentual é exatamente −5%
- **THEN** a tendência DEVE ser `Leve Queda`

#### Scenario: Dividendo anterior igual a zero
- **WHEN** o dividendo anterior é zero e o último é maior que zero
- **THEN** a tendência DEVE ser `Forte Alta`

#### Scenario: Ambos os dividendos zero
- **WHEN** o dividendo anterior e o último são ambos zero
- **THEN** a tendência DEVE ser `Estável`
