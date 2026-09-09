## Purpose

Define the command-line interface for FlowScope, including argument parsing, data export (VWAP CSV), ticker filtering, and desktop shortcut creation.

## Requirements

### Requirement: Exportação CSV de VWAP via --vwap
O sistema DEVE exportar os valores de VWAP dos tickers selecionados em formato CSV quando a flag `--vwap` é utilizada. O CSV DEVE incluir colunas para cada data da janela Fibonacci, com os VWAPs diários de cada ticker. Quando a flag `--tickers` é fornecida, o sistema DEVE filtrar a exportação para conter apenas os tickers listados no arquivo.

#### Scenario: Exportação VWAP com colunas diárias
- **WHEN** o usuário executa `flowscope --vwap`
- **THEN** o CSV gerado DEVE conter colunas: Ticker, VWAP_Periodo, e uma coluna por data da janela Fibonacci (ex: 2026-06-25, 2026-06-24, ...) com o VWAP diário de cada ticker

#### Scenario: Exportação VWAP com tickers específicos
- **WHEN** o usuário executa `flowscope --vwap --tickers meus_tickers.txt`
- **THEN** o CSV gerado DEVE conter apenas os tickers listados no arquivo, e apenas as datas com dados disponíveis para esses tickers

### Requirement: Extração de earnings estruturados via CLI
O sistema DEVE aceitar o argumento `--structured-earnings <TICKER>` para disparar a extração de rendimentos e amortizações estruturados. O argumento DEVE exigir obrigatoriamente `--data-inicio <AAAA-MM-DD>` e `--data-fim <AAAA-MM-DD>`. O argumento opcional `--output <ARQUIVO>` DEVE definir o caminho do JSON de saída; quando omitido, o JSON DEVE ser impresso em stdout.

#### Scenario: Extração completa com output em arquivo
- **WHEN** o usuário executa `flowscope --structured-earnings ALZR11 --data-inicio 2026-01-01 --data-fim 2026-07-29 --output proventos.json`
- **THEN** o sistema DEVE extrair os proventos, salvar em `proventos.json` e imprimir mensagem de sucesso

#### Scenario: Extração com ticker sem dados
- **WHEN** o usuário executa `flowscope --structured-earnings PETR4 --data-inicio 2026-01-01 --data-fim 2026-07-29`
- **THEN** o sistema DEVE exibir "Nenhum dado disponível para PETR4" sem erro

