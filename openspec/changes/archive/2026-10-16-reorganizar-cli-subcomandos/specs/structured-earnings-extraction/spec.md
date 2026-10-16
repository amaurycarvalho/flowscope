## MODIFIED Requirements

### Requirement: CLI para extração de proventos

O sistema DEVE expor a extração via subcomando `flowscope consultar proventos <TICKER>`, exigindo `--data-inicio <AAAA-MM-DD>` e `--data-fim <AAAA-MM-DD>` e aceitando `--saida <ARQUIVO>` opcional. Sem `--saida`, o JSON DEVE ser impresso em `stdout`; com `--saida`, o JSON DEVE ser gravado no arquivo indicado.

#### Scenario: Extração via CLI com output em arquivo

- **WHEN** o usuário executa `flowscope consultar proventos ALZR11 --data-inicio 2026-01-01 --data-fim 2026-07-29 --saida proventos.json`
- **THEN** o sistema DEVE extrair os proventos e salvar o JSON no arquivo especificado

#### Scenario: Extração via CLI com ticker não-fundo

- **WHEN** o usuário executa `flowscope consultar proventos PETR4 --data-inicio 2026-01-01 --data-fim 2026-07-29`
- **THEN** o sistema DEVE exibir "Nenhum dado disponível" sem erro
