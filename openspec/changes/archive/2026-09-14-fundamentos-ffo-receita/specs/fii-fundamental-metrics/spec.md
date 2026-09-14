## ADDED Requirements

### Requirement: Razões FFO/Receita, Dividendos/Receita e Dividendos/FFO

O sistema DEVE calcular, para tickers do tipo `FII`, as razões `FFO/Receita = (FFO ÷ Receita) × 100`, `Dividendos/Receita = (Rend. Distribuído ÷ Receita) × 100` e `Dividendos/FFO = (Rend. Distribuído ÷ FFO) × 100`, nos períodos de 12 meses e 3 meses, a partir dos demonstrativos do Fundamentus, tratando `Rend. Distribuído` como Dividendos. Os valores DEVEM ser armazenados como fração em `Decimal` e apresentados em notação percentual com uma casa decimal. Para tickers do tipo `Papel`, as razões DEVEM ser `N/A`. Insumo ausente DEVE resultar em `N/A` na razão correspondente, sem impedir as demais.

#### Scenario: FFO/Receita calculado
- **WHEN** um FII possui FFO de 12 meses `417655000` e Receita de 12 meses `478420000`
- **THEN** `FFO/Receita (12m)` DEVE ser aproximadamente `87,3%`

#### Scenario: Dividendos/Receita calculado
- **WHEN** um FII possui Rend. Distribuído de 12 meses `553687000` e Receita de 12 meses `478420000`
- **THEN** `Dividendos/Receita (12m)` DEVE ser aproximadamente `115,7%`

#### Scenario: Dividendos/FFO calculado
- **WHEN** um FII possui Rend. Distribuído de 3 meses `112411000` e FFO de 3 meses `125081000`
- **THEN** `Dividendos/FFO (3m)` DEVE ser aproximadamente `89,9%`

#### Scenario: Tipo Papel não calcula as razões
- **WHEN** o ticker é do tipo `Papel`
- **THEN** as seis razões DEVEM ser `N/A`

#### Scenario: Insumo ausente
- **WHEN** a fonte não fornece Receita, FFO ou Rend. Distribuído de um período
- **THEN** somente as razões que dependem desse insumo DEVEM ser `N/A`

### Requirement: Tratamento de insumos negativos nas razões

O sistema DEVE substituir o valor numérico por texto quando um insumo do denominador for negativo: `Receita negativa` quando a Receita for negativa, `FFO negativo` quando o FFO for negativo e `Receita e FFO negativos` quando ambos forem negativos na razão `FFO/Receita`. Divisão por zero DEVE resultar em `N/A`. O texto DEVE ser aplicado apenas no campo da razão correspondente, sem afetar as demais.

#### Scenario: Receita negativa
- **WHEN** a Receita do período é negativa e o FFO é positivo
- **THEN** `FFO/Receita` e `Dividendos/Receita` DEVEM exibir `Receita negativa`

#### Scenario: FFO negativo
- **WHEN** o FFO do período é negativo e a Receita é positiva
- **THEN** `Dividendos/FFO` DEVE exibir `FFO negativo`

#### Scenario: Receita e FFO negativos
- **WHEN** a Receita e o FFO do período são ambos negativos
- **THEN** `FFO/Receita` DEVE exibir `Receita e FFO negativos`

#### Scenario: Divisão por zero
- **WHEN** o denominador da razão é zero
- **THEN** a razão correspondente DEVE exibir `N/A`

### Requirement: Dividend Yield de FII recalculado pelo último dividendo

O sistema DEVE recalcular o Dividend Yield de tickers do tipo `FII` como `(último dividendo × 12) ÷ P (Cotação)` quando o último dividendo e a cotação atual existirem e a cotação for diferente de zero. Quando qualquer um desses insumos não existir, o sistema DEVE manter o Dividend Yield do Fundamentus. Para tickers do tipo `Papel`, o sistema NÃO DEVE recalcular o Dividend Yield, preservando os fallbacks existentes.

#### Scenario: Recálculo com último dividendo
- **WHEN** um FII possui último dividendo `0,10` e cotação `10,00`
- **THEN** o Dividend Yield DEVE ser aproximadamente `0,12` (12,0% ao ano sobre a cotação atual)

#### Scenario: Sem último dividendo ou cotação
- **WHEN** o último dividendo ou a cotação de um FII não está disponível
- **THEN** o Dividend Yield DEVE ser o valor do Fundamentus, quando disponível

#### Scenario: Tipo Papel preserva o fallback
- **WHEN** o ticker é do tipo `Papel`
- **THEN** o Dividend Yield NÃO DEVE ser recalculado pelo último dividendo

### Requirement: Tendência do FFO pela variação da margem FFO/Receita

O sistema DEVE classificar a tendência do FFO de tickers do tipo `FII` pela diferença, em pontos percentuais, entre `FFO/Receita (3m)` e `FFO/Receita (12m)`, reutilizando as cinco faixas determinísticas existentes: `FORTE_ALTA` (≥ +20 p.p.), `ALTA` (≥ +5 p.p.), `ESTAVEL` (> −5 p.p.), `QUEDA` (≥ −20 p.p.) e `FORTE_QUEDA` (< −20 p.p.). Quando uma das margens não estiver disponível (inclusive por insumo negativo ou ausente) ou o ticker for do tipo `Papel`, a tendência DEVE ser `N/A`.

#### Scenario: Margem estável
- **WHEN** `FFO/Receita (12m)` é `87,3%` e `FFO/Receita (3m)` é `85,5%`
- **THEN** a tendência DEVE ser `ESTAVEL` (diferença de −1,8 p.p.)

#### Scenario: Margem em leve queda
- **WHEN** `FFO/Receita (12m)` é `104,0%` e `FFO/Receita (3m)` é `94,5%`
- **THEN** a tendência DEVE ser `QUEDA` (diferença de −9,5 p.p.)

#### Scenario: Margem indisponível
- **WHEN** `FFO/Receita (12m)` ou `FFO/Receita (3m)` é `N/A` ou um texto de insumo negativo
- **THEN** a tendência DEVE ser `N/A`

## REMOVED Requirements

### Requirement: Dividend Payout

**Reason**: A coluna `Dividend Payout (DY/FFOY)` foi substituída pelas razões sobre a receita (`Dividendos/Receita` e `Dividendos/FFO`), que expressam a relação entre dividendos, FFO e receita de forma mais direta.

**Migration**: Use `Dividendos/FFO` para medir quanto do caixa operacional é consumido pelos dividendos e `Dividendos/Receita` para medir quanto da receita é distribuído.
