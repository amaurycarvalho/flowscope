## ADDED Requirements

### Requirement: Exposição de indicadores adicionais e de imóveis

O sistema DEVE expor na composição de campos fundamentalistas, quando presentes na página, os indicadores `LPA`, `ROE` e `ROIC` e os campos de imóveis `Cap Rate` e `Vacância Média` (além de `Qtd imóveis`), sem alterar a exposição dos demais campos.

#### Scenario: Indicadores de ação disponíveis
- **WHEN** a página de uma ação contém os indicadores `LPA`, `ROE` e `ROIC`
- **THEN** os campos correspondentes DEVEM ser expostos com os valores normalizados

#### Scenario: Indicadores de imóveis disponíveis
- **WHEN** a página de um FII contém `Cap Rate` e `Vacância Média`
- **THEN** os campos correspondentes DEVEM ser expostos com os valores normalizados

#### Scenario: Indicador ausente ou não numérico
- **WHEN** um indicador está ausente ou contém `-`
- **THEN** o campo correspondente DEVE ser ausência de valor, sem impedir os demais
