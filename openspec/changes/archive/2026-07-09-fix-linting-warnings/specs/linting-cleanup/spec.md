## ADDED Requirements

### Requirement: Codebase is lint-clean
The codebase SHALL produce zero warnings when linted with the project's configured linter (ruff/flake8).

#### Scenario: Linter passes on all source files
- **WHEN** linter runs on all files under `src/` and `tests/`
- **THEN** output contains zero warnings

#### Scenario: Existing behavior is preserved
- **WHEN** all linting warnings are resolved
- **THEN** all existing tests pass and chart output is visually identical