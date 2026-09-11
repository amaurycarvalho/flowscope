## ADDED Requirements

### Requirement: Preço Típico e P / PT

O sistema DEVE calcular o `Preço Típico` como `(Cotação Max 52 sem + Cotação Min 52 sem + Cotação) / 3` e o `P / PT` como `(Cotação − Preço Típico) / Preço Típico`, por funções puras e determinísticas em `Decimal`, exibindo `N/A` quando qualquer insumo estiver ausente ou o Preço Típico for zero.

#### Scenario: Preço Típico calculado
- **WHEN** a cotação é `10`, a mínima de 52 semanas é `8` e a máxima é `12`
- **THEN** o Preço Típico DEVE ser `10`

#### Scenario: P / PT calculado
- **WHEN** a cotação é `9` e o Preço Típico é `10`
- **THEN** o P / PT DEVE ser `-0,10` (−10%)

#### Scenario: Insumo ausente
- **WHEN** a cotação, a mínima ou a máxima de 52 semanas não está disponível
- **THEN** o Preço Típico e o P / PT DEVEM ser `N/A`

### Requirement: Percentuais por indexador na análise

O sistema DEVE expor, por ticker de FII, os percentuais de patrimônio por indexador fornecidos pela CVM, omitindo os indexadores sem valor.

#### Scenario: Percentuais disponíveis
- **WHEN** a CVM fornece os percentuais de `IPCA`, `IGP-M`, `INPC` e `INCC` para o FII
- **THEN** a análise DEVE expor os percentuais por indexador

#### Scenario: Sem percentuais
- **WHEN** a CVM não fornece percentuais para o ticker
- **THEN** nenhum percentual DEVE ser exposto, sem impedir as demais métricas
