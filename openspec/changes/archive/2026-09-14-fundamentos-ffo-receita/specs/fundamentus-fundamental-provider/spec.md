## ADDED Requirements

### Requirement: Exposição dos demonstrativos de Receita e Rend. Distribuído

O sistema DEVE expor, na composição de campos fundamentalistas consumida pela análise, a `Receita` e o `Rend. Distribuído` dos demonstrativos de 12 e 3 meses, normalizados em `Decimal`. A `Receita` DEVE usar o rótulo `Receita` e, na sua ausência, `Receita Líquida`. O `Rend. Distribuído` DEVE ser tratado como Dividendos no cálculo das métricas. Campos ausentes DEVEM ser omitidos sem impedir a exposição dos demais.

#### Scenario: Receita disponível
- **WHEN** a página contém `Receita` nos demonstrativos de 12 e 3 meses
- **THEN** os campos de receita de 12m e 3m DEVEM ser expostos com os valores normalizados

#### Scenario: Receita Líquida como alternativa
- **WHEN** a página não contém `Receita` mas contém `Receita Líquida`
- **THEN** o campo de receita DEVE ser exposto com o valor de `Receita Líquida`

#### Scenario: Rend. Distribuído disponível
- **WHEN** a página contém `Rend. Distribuído` nos demonstrativos de 12 e 3 meses
- **THEN** os campos de rendimento distribuído de 12m e 3m DEVEM ser expostos com os valores normalizados

#### Scenario: Campo ausente
- **WHEN** a página não contém `Receita`, `Receita Líquida` nem `Rend. Distribuído`
- **THEN** os campos correspondentes DEVEM ser ausentes, sem impedir a exposição dos demais
