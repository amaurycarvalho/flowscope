## ADDED Requirements

### Requirement: Dividend Payout

O sistema DEVE calcular o Dividend Payout como a razão `Dividend Yield / FFO Yield`, exibindo `N/A` quando qualquer um dos dois não estiver disponível ou o FFO Yield for zero.

#### Scenario: Dividend Payout calculado
- **WHEN** Dividend Yield é `0,08` e FFO Yield é `0,10`
- **THEN** o Dividend Payout DEVE ser `0,8`

#### Scenario: Dividend Payout indisponível
- **WHEN** Dividend Yield ou FFO Yield não estão disponíveis
- **THEN** o Dividend Payout DEVE ser `N/A`
