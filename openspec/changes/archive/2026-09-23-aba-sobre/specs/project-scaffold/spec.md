## ADDED Requirements

### Requirement: Metadados de licença GPL-3.0-only

O `pyproject.toml` DEVE declarar a licença `GPL-3.0-only`, consistente com o arquivo `LICENSE` (GNU GPL v3), e o `build-system` DEVE exigir `setuptools>=77` para suportar a expressão SPDX no campo `license`.

#### Scenario: Licença declarada como GPL-3.0-only

- **WHEN** o `pyproject.toml` é inspecionado
- **THEN** o campo `license` DEVE conter `"GPL-3.0-only"` e NÃO DEVE conter `MIT`

#### Scenario: Setuptools mínimo para PEP 639

- **WHEN** o `pyproject.toml` é inspecionado
- **THEN** `build-system.requires` DEVE incluir `setuptools>=77`

#### Scenario: Consistência com o arquivo LICENSE

- **WHEN** a licença declarada no `pyproject.toml` é comparada ao arquivo `LICENSE`
- **THEN** ambas DEVEM corresponder à GNU GPL versão 3
