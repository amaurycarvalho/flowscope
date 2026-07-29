## ADDED Requirements

### Requirement: Extração de informe mensal via CLI
O sistema DEVE aceitar `--informe-mensal <TICKER>` com `--data-inicio`, `--data-fim` e `--output` opcional.

#### Scenario: Extração com output
- **WHEN** `flowscope --informe-mensal ALZR11 --data-inicio 2026-01-01 --data-fim 2026-07-29 --output informe.json`
- **THEN** salvar JSON em `informe.json`

#### Scenario: Ticker sem dados
- **WHEN** `flowscope --informe-mensal PETR4 --data-inicio 2026-01-01 --data-fim 2026-07-29`
- **THEN** exibir "Nenhum dado disponível" sem erro
