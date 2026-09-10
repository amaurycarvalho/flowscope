## ADDED Requirements

### Requirement: Exposição do campo VP/Cota

O sistema DEVE expor o indicador `VP/Cota` (valor patrimonial por cota) do Fundamentus na composição de campos fundamentalistas consumida pela análise fundamentalista, quando presente na página.

#### Scenario: VP/Cota disponível
- **WHEN** a página do FII contém o indicador `VP/Cota`
- **THEN** o campo `vp_cota` DEVE ser exposto com o valor normalizado

#### Scenario: VP/Cota ausente
- **WHEN** a página não contém o indicador `VP/Cota`
- **THEN** o campo DEVE ser ausente, sem impedir a exposição dos demais campos
