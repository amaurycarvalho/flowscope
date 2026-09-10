## MODIFIED Requirements

### Requirement: Sub-tipo de ação
O sistema DEVE compor o sub-tipo de um ativo classificado como `Papel` concatenando os campos `Tipo` (espécie), `Setor` e `Subsetor`, separados por `", "`, na ordem informada, ignorando campos ausentes.

#### Scenario: Ação preferencial
- **WHEN** `Tipo` é `PN`, `Setor` é `Petróleo, Gás e Biocombustíveis` e `Subsetor` é `Exploração, Refino e Distribuição`
- **THEN** o sub-tipo DEVE ser `PN, Petróleo, Gás e Biocombustíveis, Exploração, Refino e Distribuição`

#### Scenario: Ação ordinária
- **WHEN** `Tipo` é `ON` e os demais campos de classificação estão presentes
- **THEN** o sub-tipo DEVE iniciar com `ON, `

### Requirement: Sub-tipo de FII via taxonomia versionada
O sistema DEVE compor o sub-tipo de um FII concatenando `Segmento` e `Gestão`, separados por `", "`, prefixado por `Tijolo: ` quando `Qtd imóveis` for maior que zero e por `Papel: ` caso contrário. Quando os campos do Fundamentus estiverem ausentes, DEVE usar a taxonomia versionada (mapa estático `ticker → sub-tipo`) como fallback.

#### Scenario: FII de tijolo mapeado
- **WHEN** `Qtd imóveis` é maior que zero
- **THEN** o sub-tipo DEVE iniciar com `Tijolo: ` seguido de `Segmento, Gestão`

#### Scenario: FII não mapeado na taxonomia
- **WHEN** `Qtd imóveis` é zero ou ausente
- **THEN** o sub-tipo DEVE iniciar com `Papel: ` seguido de `Segmento, Gestão`

#### Scenario: Fundamentus indisponível
- **WHEN** os dados do Fundamentus não estão disponíveis para o FII
- **THEN** o sub-tipo DEVE ser obtido pela taxonomia determinística de fallback
