## ADDED Requirements

### Requirement: Exposição da quantidade de cotas/ações emitidas

O sistema DEVE expor, na composição de campos fundamentalistas consumida pela análise, a quantidade de cotas/ações emitidas a partir da página de detalhes do Fundamentus: `Nro. Cotas` para FIIs e `Nro. Ações` para Papéis, normalizada em `Decimal`. O campo exposto DEVE ser `cotas_emitidas`. Campos ausentes ou não numéricos DEVEM ser omitidos, sem impedir a exposição dos demais campos.

#### Scenario: Quantidade de cotas disponível para FII
- **WHEN** a página de um FII contém o rótulo `Nro. Cotas`
- **THEN** o campo `cotas_emitidas` DEVE ser exposto com o valor normalizado

#### Scenario: Quantidade de ações disponível para Papel
- **WHEN** a página de uma ação contém o rótulo `Nro. Ações`
- **THEN** o campo `cotas_emitidas` DEVE ser exposto com o valor normalizado

#### Scenario: Quantidade ausente
- **WHEN** a página não contém `Nro. Cotas` nem `Nro. Ações`
- **THEN** o campo DEVE ser ausente, sem impedir a exposição dos demais campos
