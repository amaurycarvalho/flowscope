## MODIFIED Requirements

### Requirement: Informações institucionais na aba "Sobre"

O sistema DEVE exibir, na aba "Sobre", nesta ordem: o ícone da aplicação; o nome e a versão no formato `FlowScopeBR vX.Y.Z`; a data de lançamento em formato ISO (`YYYY-MM-DD`); e a licença "Software livre e de código aberto (GNU GPLv3)". A versão DEVE ser obtida de `flowscope.__version__` e a data de `flowscope.__release_date__`.

#### Scenario: Ordem das informações

- **WHEN** a aba "Sobre" é exibida
- **THEN** o ícone, o nome com a versão, a data ISO e a licença DEVEM aparecer nessa ordem

#### Scenario: Valores de versão e data

- **WHEN** `__version__` é "1.1.0" e `__release_date__` é "2026-09-18"
- **THEN** a aba DEVE exibir "FlowScopeBR v1.1.0" e "2026-09-18"
