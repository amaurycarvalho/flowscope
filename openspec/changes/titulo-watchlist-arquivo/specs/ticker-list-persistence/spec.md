## ADDED Requirements

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
