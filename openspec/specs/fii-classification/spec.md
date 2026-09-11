# fii-classification Specification

## Purpose
Classificar deterministicamente o tipo e o sub-tipo de um ativo (ação, FII, ETF ou BDR) para alimentar as colunas de identidade da tabela fundamentalista e decidir a elegibilidade para as métricas FFO.

## Requirements

### Requirement: Classificação do tipo de ativo
O sistema DEVE classificar um ticker como `Papel` ou `FII` a partir do rótulo do campo de ticker no Fundamentus (`Papel`/`FII`); quando o Fundamentus não fornecer o rótulo, DEVE usar a classificação autorregulação do Informe Mensal da B3 (a existência de informe de FII indica `FII`); e apenas quando nenhuma dessas fontes resolver DEVE usar a classificação determinística (derivação sintática do ticker, resolução `code-cvm-resolution` e taxonomia). O resultado DEVE ser registrado com a fonte da classificação.

#### Scenario: Ticker de ação ordinária
- **WHEN** o Fundamentus apresenta o rótulo `Papel` para um ticker de ação
- **THEN** o tipo DEVE ser `Papel`

#### Scenario: Ticker de FII
- **WHEN** o Fundamentus apresenta o rótulo `FII` para o ticker
- **THEN** o tipo DEVE ser `FII`

#### Scenario: Fundamentus indisponível com informe mensal da B3
- **WHEN** o Fundamentus não fornece o rótulo e a B3 possui o Informe Mensal Estruturado do ticker
- **THEN** o tipo DEVE ser `FII`

#### Scenario: Ticker de ETF
- **WHEN** um ticker de ETF listado é classificado
- **THEN** o tipo DEVE ser `Papel` (não-FII), conforme o rótulo do Fundamentus

#### Scenario: Ticker não classificado deterministicamente
- **WHEN** nem o Fundamentus, nem a B3, nem a classificação determinística de fallback resolvem o ticker
- **THEN** o tipo DEVE ser `DESCONHECIDO` e o sistema NÃO DEVE inferir o tipo a partir do nome do ativo

### Requirement: Sub-tipo de ação
O sistema DEVE compor o sub-tipo de um ativo classificado como `Papel` concatenando os campos `Tipo` (espécie), `Setor` e `Subsetor`, separados por `", "`, na ordem informada, ignorando campos ausentes.

#### Scenario: Ação preferencial
- **WHEN** `Tipo` é `PN`, `Setor` é `Petróleo, Gás e Biocombustíveis` e `Subsetor` é `Exploração, Refino e Distribuição`
- **THEN** o sub-tipo DEVE ser `PN, Petróleo, Gás e Biocombustíveis, Exploração, Refino e Distribuição`

#### Scenario: Ação ordinária
- **WHEN** `Tipo` é `ON` e os demais campos de classificação estão presentes
- **THEN** o sub-tipo DEVE iniciar com `ON, `

### Requirement: Sub-tipo de FII via taxonomia versionada
O sistema DEVE compor o sub-tipo de um FII concatenando `Segmento` e `Gestão`, separados por `", "`, prefixado por `Tijolo: ` quando `Qtd imóveis` for maior que zero e por `Papel: ` caso contrário. Quando os campos do Fundamentus estiverem ausentes, DEVE usar a Classificação/Subclassificação/Gestão/Segmento de Atuação do Informe Mensal da B3 (prefixando `Tijolo: ` para Tijolo/Híbrido com imóveis e `Papel: ` para Papel) e, na ausência desta, a taxonomia versionada (mapa estático `ticker → sub-tipo`).

#### Scenario: FII de tijolo mapeado
- **WHEN** `Qtd imóveis` é maior que zero
- **THEN** o sub-tipo DEVE iniciar com `Tijolo: ` seguido de `Segmento, Gestão`

#### Scenario: FII não mapeado na taxonomia
- **WHEN** `Qtd imóveis` é zero ou ausente
- **THEN** o sub-tipo DEVE iniciar com `Papel: ` seguido de `Segmento, Gestão`

#### Scenario: Fundamentus indisponível com classificação da B3
- **WHEN** os dados do Fundamentus não estão disponíveis e a B3 informa `Classificação: Papel`, `Gestão: Ativa` e `Segmento de Atuação: Outros`
- **THEN** o sub-tipo DEVE ser `Papel: Outros, Ativa`

#### Scenario: Fundamentus indisponível
- **WHEN** os dados do Fundamentus não estão disponíveis para o FII e a B3 também não fornece a classificação
- **THEN** o sub-tipo DEVE ser obtido pela taxonomia determinística de fallback
