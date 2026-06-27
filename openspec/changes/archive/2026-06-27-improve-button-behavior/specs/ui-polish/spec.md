## MODIFIED Requirements

### Requirement: Preferências persistentes

O sistema DEVE salvar e restaurar a última data selecionada, último gráfico, geometria da janela, posição do divisor do PanedWindow e último diretório dos diálogos de ticker em `~/.flowscope/config.json`.

#### Scenario: Restauração de preferências
- **WHEN** o aplicativo inicia
- **THEN** a janela DEVE restaurar sua geometria, data, e `last_ticker_dir` da última sessão

#### Scenario: Último diretório salvo após salvar tickers
- **WHEN** o usuário clica em "Salvar Tickers" e seleciona um arquivo em `/home/user/dados/tickers.txt`
- **THEN** o diretório `/home/user/dados/` DEVE ser salvo como `last_ticker_dir` em `~/.flowscope/config.json`

#### Scenario: Último diretório salvo após carregar tickers
- **WHEN** o usuário clica em "Carregar Tickers" e seleciona um arquivo em `/home/user/dados/tickers.txt`
- **THEN** o diretório `/home/user/dados/` DEVE ser salvo como `last_ticker_dir` em `~/.flowscope/config.json`

#### Scenario: Diálogo abre no último diretório
- **WHEN** o usuário clica em "Salvar Tickers" ou "Carregar Tickers" e existe `last_ticker_dir` nas preferências
- **THEN** o diálogo DEVE abrir com `initialdir` apontando para `last_ticker_dir`
