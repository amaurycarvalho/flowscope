## Purpose

Define the persistence behavior for the last-used ticker list, ensuring the list is saved on close and on change, and restored on startup without triggering a data download.

## Requirements

### Requirement: Persist last-used ticker list on close
The system SHALL save the current ticker list to the preferences file (`~/.flowscope/config.json`, key `last_tickers`) when the application closes.

#### Scenario: Save ticker list on close
- **WHEN** the user closes the application and the ticker list contains tickers
- **THEN** `config.json` SHALL store those tickers under `last_tickers`

#### Scenario: Close with empty ticker list
- **WHEN** the user closes the application with an empty ticker list
- **THEN** `last_tickers` SHALL be persisted as an empty list

### Requirement: Persist ticker list on change
The system SHALL save the ticker list to preferences when it changes during a session (e.g., loading from file or changing directory), so it is not lost on a crash or non-graceful exit.

#### Scenario: Ticker list changed mid-session
- **WHEN** the user loads a ticker list from file or changes the ticker directory
- **THEN** the preferences file SHALL be updated with the current ticker list

### Requirement: Restore last-used ticker list on startup
When the application opens, the system SHALL populate the ticker list with the last-used list if one exists, without triggering a data download.

#### Scenario: Previous list exists
- **WHEN** the application starts and `last_tickers` contains tickers
- **THEN** the ticker list SHALL display those tickers and SHALL NOT start any download

#### Scenario: No previous list
- **WHEN** the application starts and no `last_tickers` value exists
- **THEN** the ticker list SHALL be blank

#### Scenario: Empty saved list
- **WHEN** the application starts and `last_tickers` is an empty list
- **THEN** the ticker list SHALL be blank

#### Scenario: Counter reflects restored list
- **WHEN** the application starts with a restored ticker list
- **THEN** the ticker counter SHALL show the number of tickers (e.g., `Tickers (N)`)

### Requirement: Persist source watchlist file path

The system SHALL store the full path of the last watchlist file loaded or saved through the ticker load/save buttons in the preferences file (`~/.flowscope/config.json`, key `last_ticker_file`). The key SHALL be updated when the user loads a file and when the user saves a file. Populating the ticker list via an index button (IBOV/IDIV/IFIX) SHALL NOT write or replace the stored file path. On startup, the system SHALL make the base name of the stored file available for the window title without re-reading the file contents.

#### Scenario: Loading a file persists its path

- **WHEN** the user loads the watchlist from `/home/user/dados/petr4.txt`
- **THEN** `config.json` SHALL store `last_ticker_file` as `/home/user/dados/petr4.txt`

#### Scenario: Saving a file persists its path

- **WHEN** the user saves the watchlist to `/home/user/dados/carteira.txt`
- **THEN** `config.json` SHALL store `last_ticker_file` as `/home/user/dados/carteira.txt`

#### Scenario: Index button does not persist a file

- **WHEN** the user clicks "IBOV" and no file was loaded or saved in the session
- **THEN** `last_ticker_file` SHALL remain unchanged

#### Scenario: Base name restored on startup

- **WHEN** the application starts and `last_ticker_file` is set
- **THEN** the base name of the stored file SHALL be available for the window title

#### Scenario: No stored file

- **WHEN** the application starts and `last_ticker_file` is absent
- **THEN** no file name SHALL be available and the title SHALL fall back to its default

### Requirement: Carregar a watchlist de um arquivo pela CLI

O sistema DEVE permitir que a watchlist seja carregada de um arquivo indicado por meio da CLI, com um ticker por linha, normalizando cada ticker com `strip().upper()` e descartando linhas vazias. A carga DEVE persistir imediatamente o resultado em `last_tickers` no `config.json`, sem aguardar o fechamento da aplicação, de modo que as ações subsequentes da CLI enxerguem a watchlist carregada. A carga DEVE também persistir o caminho completo do arquivo em `last_ticker_file`, de modo que a interface gráfica reflita o arquivo carregado no título na próxima sessão.

#### Scenario: Watchlist carregada de arquivo

- **WHEN** a CLI carrega a watchlist de um arquivo válido
- **THEN** `config.json` DEVE conter os tickers normalizados em `last_tickers` imediatamente após a carga
- **AND** `config.json` DEVE conter o caminho completo do arquivo em `last_ticker_file`

#### Scenario: Arquivo vazio ou inexistente

- **WHEN** a CLI recebe um arquivo inexistente ou sem tickers
- **THEN** a persistência NÃO DEVE ocorrer e `last_tickers` e `last_ticker_file` DEVEM permanecer inalterados
