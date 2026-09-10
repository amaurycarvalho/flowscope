## MODIFIED Requirements

### Requirement: Classificação do tipo de ativo
O sistema DEVE classificar um ticker como `Papel` ou `FII` a partir do rótulo do campo de ticker no Fundamentus (`Papel`/`FII`), usando a classificação determinística (derivação sintática do ticker, resolução `code-cvm-resolution` e taxonomia) apenas como fallback quando o dado do Fundamentus não estiver disponível. O resultado DEVE ser registrado com a fonte da classificação.

#### Scenario: Ticker de ação ordinária
- **WHEN** o Fundamentus apresenta o rótulo `Papel` para um ticker de ação
- **THEN** o tipo DEVE ser `Papel`

#### Scenario: Ticker de FII
- **WHEN** o Fundamentus apresenta o rótulo `FII` para o ticker
- **THEN** o tipo DEVE ser `FII`

#### Scenario: Ticker de ETF
- **WHEN** um ticker de ETF listado é classificado
- **THEN** o tipo DEVE ser `Papel` (não-FII), conforme o rótulo do Fundamentus

#### Scenario: Ticker não classificado deterministicamente
- **WHEN** nem o Fundamentus nem a classificação determinística de fallback resolvem o ticker
- **THEN** o tipo DEVE ser `DESCONHECIDO` e o sistema NÃO DEVE inferir o tipo a partir do nome do ativo

### Requirement: Sub-tipo de ação
O sistema DEVE compor o sub-tipo de um ativo classificado como `Papel` concatenando os campos `Tipo` (espécie), `Setor` e `Subsetor`, separados por `"; "`, na ordem informada, ignorando campos ausentes.

#### Scenario: Ação preferencial
- **WHEN** `Tipo` é `PN`, `Setor` é `Petróleo, Gás e Biocombustíveis` e `Subsetor` é `Exploração, Refino e Distribuição`
- **THEN** o sub-tipo DEVE ser `PN; Petróleo, Gás e Biocombustíveis; Exploração, Refino e Distribuição`

#### Scenario: Ação ordinária
- **WHEN** `Tipo` é `ON` e os demais campos de classificação estão presentes
- **THEN** o sub-tipo DEVE iniciar com `ON; `

### Requirement: Sub-tipo de FII via taxonomia versionada
O sistema DEVE compor o sub-tipo de um FII concatenando `Segmento` e `Gestão`, separados por `"; "`, prefixado por `Tijolo: ` quando `Qtd imóveis` for maior que zero e por `Papel: ` caso contrário. Quando os campos do Fundamentus estiverem ausentes, DEVE usar a taxonomia versionada (mapa estático `ticker → sub-tipo`) como fallback.

#### Scenario: FII de tijolo mapeado
- **WHEN** `Qtd imóveis` é maior que zero
- **THEN** o sub-tipo DEVE iniciar com `Tijolo: ` seguido de `Segmento; Gestão`

#### Scenario: FII não mapeado na taxonomia
- **WHEN** `Qtd imóveis` é zero ou ausente
- **THEN** o sub-tipo DEVE iniciar com `Papel: ` seguido de `Segmento; Gestão`

#### Scenario: Fundamentus indisponível
- **WHEN** os dados do Fundamentus não estão disponíveis para o FII
- **THEN** o sub-tipo DEVE ser obtido pela taxonomia determinística de fallback

## REMOVED Requirements

### Requirement: Elegibilidade para métricas FFO
**Reason**: A elegibilidade por tipo/sub-tipo deixa de restringir o cálculo; as métricas FFO são preenchidas sempre que a fonte fornecer o dado.
**Migration**: Consumidores não devem mais filtrar por `TIJOLO`/`HIBRIDO`; exibem `N/A` apenas quando o dado não existir na fonte.
