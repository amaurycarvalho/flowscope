## Purpose

Classificar deterministicamente o tipo e o sub-tipo de um ativo (ação, FII, ETF ou BDR) para alimentar as colunas de identidade da tabela fundamentalista e decidir a elegibilidade para as métricas FFO.

## ADDED Requirements

### Requirement: Classificação do tipo de ativo
O sistema DEVE classificar um ticker em um tipo de ativo (`ACAO`, `FII`, `ETF` ou `BDR`) de forma determinística, combinando a derivação sintática do ticker (segmento e sufixo) com a resolução `code-cvm-resolution` (identidade CVM). O resultado DEVE ser registrado com a fonte da classificação.

#### Scenario: Ticker de ação ordinária
- **WHEN** um ticker de ação ordinária (ex.: `PETR3`) é classificado
- **THEN** o tipo DEVE ser `ACAO` e o sub-tipo DEVE ser `ORDINARIA`

#### Scenario: Ticker de FII
- **WHEN** um ticker de FII (ex.: `KNRI11`) é classificado
- **THEN** o tipo DEVE ser `FII`

#### Scenario: Ticker de ETF
- **WHEN** um ticker de ETF (ex.: `BOVA11`) é classificado
- **THEN** o tipo DEVE ser `ETF`

#### Scenario: Ticker não classificado deterministicamente
- **WHEN** um ticker não pode ser classificado de forma determinística
- **THEN** o tipo DEVE ser `DESCONHECIDO` e o sistema NÃO DEVE inferir o tipo a partir do nome do ativo

### Requirement: Sub-tipo de ação
O sistema DEVE derivar o sub-tipo de uma ação (`ORDINARIA`, `PREFERENCIAL` ou `ETF`) a partir do sufixo do ticker, de forma determinística.

#### Scenario: Ação preferencial
- **WHEN** um ticker de ação preferencial (ex.: `PETR4`) é classificado
- **THEN** o sub-tipo DEVE ser `PREFERENCIAL`

#### Scenario: Ação ordinária
- **WHEN** um ticker de ação ordinária (ex.: `VALE3`) é classificado
- **THEN** o sub-tipo DEVE ser `ORDINARIA`

### Requirement: Sub-tipo de FII via taxonomia versionada
O sistema DEVE classificar o sub-tipo de um FII (`TIJOLO`, `PAPEL`, `HIBRIDO`, `FIAGRO` ou `FIINFRA`) por meio de uma taxonomia versionada (mapa estático `ticker → sub-tipo`) mantida no repositório. A taxonomia DEVE ter uma versão explícita.

#### Scenario: FII de tijolo mapeado
- **WHEN** um ticker de FII mapeado como tijolo (ex.: `KNRI11`) é classificado
- **THEN** o sub-tipo DEVE ser `TIJOLO`

#### Scenario: FII não mapeado na taxonomia
- **WHEN** um FII não possui entrada na taxonomia
- **THEN** o sub-tipo DEVE ser `DESCONHECIDO` e o sistema NÃO DEVE inferir o sub-tipo a partir do nome do fundo

### Requirement: Elegibilidade para métricas FFO
O sistema DEVE considerar elegível para as métricas FFO somente FIIs classificados como `TIJOLO` ou `HIBRIDO`. Papel, FIAGRO, FIINFRA, ações, ETFs, BDRs e ativos de tipo `DESCONHECIDO` DEVEM ser tratados como não elegíveis.

#### Scenario: FII de tijolo é elegível
- **WHEN** um FII classificado como `TIJOLO` é analisado
- **THEN** as métricas FFO DEVEM ser calculadas

#### Scenario: FII de papel não é elegível
- **WHEN** um FII classificado como `PAPEL` é analisado
- **THEN** as métricas FFO DEVEM ser `N/A`

#### Scenario: Ação não é elegível
- **WHEN** um ativo do tipo `ACAO` é analisado
- **THEN** as métricas FFO DEVEM ser `N/A`
