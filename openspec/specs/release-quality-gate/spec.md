## Purpose

Define the release workflow quality gate: the release pipeline must depend on a successful CI run before any platform build is initiated.

## Requirements

### Requirement: Release workflow depende de CI

O workflow `release.yml` DEVE conter um job `ci` que invoca o workflow reutilizavel `ci.yml` antes que qualquer build de plataforma seja iniciado. Os jobs `build` e `release` DEVEM declarar dependencia no job `ci`.

#### Scenario: Release abortado se CI falha
- **WHEN** uma tag `v*` e pushed ou um `workflow_dispatch` e disparado
- **AND** o job `ci` (que invoca `ci.yml`) falha
- **THEN** os jobs `build` e `release` NAO DEVEM executar

#### Scenario: Release procede se CI passa
- **WHEN** uma tag `v*` e pushed ou um `workflow_dispatch` e disparado
- **AND** o job `ci` completa com sucesso
- **THEN** os jobs `build` (matrix: linux, windows, macos) DEVEM executar
- **AND** o job `release` DEVE executar apos todos os builds completarem

#### Scenario: Build mantem instalacao de dependencias existente
- **WHEN** o job `build` executa
- **THEN** o passo `make install` DEVE instalar o projeto com `pip install -e .`
- **AND** o passo `make build` DEVE executar PyInstaller via `flowscope.spec`

#### Scenario: Release mantem artefatos de build para publicacao
- **WHEN** o job `release` executa
- **THEN** os artefatos de cada plataforma DEVEM ser baixados via `actions/download-artifact@v4`
- **AND** o release DEVE ser publicado via `softprops/action-gh-release@v2` com body do `CHANGELOG.md`
