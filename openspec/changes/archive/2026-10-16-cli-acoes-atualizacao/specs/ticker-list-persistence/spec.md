## ADDED Requirements

### Requirement: Carregar a watchlist de um arquivo pela CLI

O sistema DEVE permitir que a watchlist seja carregada de um arquivo indicado por meio da CLI, com um ticker por linha, normalizando cada ticker com `strip().upper()` e descartando linhas vazias. A carga DEVE persistir imediatamente o resultado em `last_tickers` no `config.json`, sem aguardar o fechamento da aplicação, de modo que as ações subsequentes da CLI enxerguem a watchlist carregada. A carga DEVE também persistir o caminho completo do arquivo em `last_ticker_file`, de modo que a interface gráfica reflita o arquivo carregado no título na próxima sessão.

#### Scenario: Watchlist carregada de arquivo

- **WHEN** a CLI carrega a watchlist de um arquivo válido
- **THEN** `config.json` DEVE conter os tickers normalizados em `last_tickers` imediatamente após a carga
- **AND** `config.json` DEVE conter o caminho completo do arquivo em `last_ticker_file`

#### Scenario: Arquivo vazio ou inexistente

- **WHEN** a CLI recebe um arquivo inexistente ou sem tickers
- **THEN** a persistência NÃO DEVE ocorrer e `last_tickers` e `last_ticker_file` DEVEM permanecer inalterados
