## ADDED Requirements

### Requirement: Exposição do indicador P/L

O sistema DEVE expor o indicador `P/L` do Fundamentus na composição de campos fundamentalistas consumida pela análise, quando presente na página, sem alterar a exposição dos demais indicadores.

#### Scenario: P/L disponível para ação
- **WHEN** a página de uma ação contém o indicador `P/L`
- **THEN** o campo `p_l` DEVE ser exposto com o valor normalizado

#### Scenario: P/L ausente
- **WHEN** a página não contém o indicador `P/L` (por exemplo, uma página de FII)
- **THEN** o campo DEVE ser ausente, sem impedir a exposição dos demais campos
