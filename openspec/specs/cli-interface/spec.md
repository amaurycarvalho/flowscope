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

