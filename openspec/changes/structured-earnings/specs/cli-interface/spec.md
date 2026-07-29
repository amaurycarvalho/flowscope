## ADDED Requirements

### Requirement: Extração de earnings estruturados via CLI
O sistema DEVE aceitar o argumento `--structured-earnings <TICKER>` para disparar a extração de rendimentos e amortizações estruturados. O argumento DEVE exigir obrigatoriamente `--data-inicio <AAAA-MM-DD>` e `--data-fim <AAAA-MM-DD>`. O argumento opcional `--output <ARQUIVO>` DEVE definir o caminho do JSON de saída; quando omitido, o JSON DEVE ser impresso em stdout.

#### Scenario: Extração completa com output em arquivo
- **WHEN** o usuário executa `flowscope --structured-earnings ALZR11 --data-inicio 2026-01-01 --data-fim 2026-07-29 --output proventos.json`
- **THEN** o sistema DEVE extrair os proventos, salvar em `proventos.json` e imprimir mensagem de sucesso

#### Scenario: Extração com ticker sem dados
- **WHEN** o usuário executa `flowscope --structured-earnings PETR4 --data-inicio 2026-01-01 --data-fim 2026-07-29`
- **THEN** o sistema DEVE exibir "Nenhum dado disponível para PETR4" sem erro
