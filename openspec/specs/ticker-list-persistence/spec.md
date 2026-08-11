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
