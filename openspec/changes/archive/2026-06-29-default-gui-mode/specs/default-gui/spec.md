## ADDED Requirements

### Requirement: GUI launch by default

The system SHALL open the graphical user interface when `flowscope` is executed without any arguments.

#### Scenario: No arguments opens GUI
- **WHEN** the user runs `flowscope` without any arguments
- **THEN** the system SHALL open the Tkinter GUI window

#### Scenario: Explicit --gui flag still works
- **WHEN** the user runs `flowscope --gui`
- **THEN** the system SHALL open the Tkinter GUI window (same behavior as no arguments)

#### Scenario: CLI flags override default
- **WHEN** the user runs `flowscope --tickers meus_tickers.txt`
- **THEN** the system SHALL run the CLI analysis mode, not the GUI

#### Scenario: Meta flags still work
- **WHEN** the user runs `flowscope --version`
- **THEN** the system SHALL print the version string and exit (no GUI)

#### Scenario: VWAP export still works
- **WHEN** the user runs `flowscope --vwap`
- **THEN** the system SHALL export VWAP data to CSV (no GUI)
