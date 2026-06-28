## ADDED Requirements

### Requirement: OrientationPanel atualizado com novos indicadores

O OrientationPanel DEVE exibir conteúdo explicativo para cada novo indicador à medida que as sub-abas são implementadas, seguindo o mesmo padrão existente (título + texto explicativo + interpretação).

#### Scenario: OrientationPanel para Dominância do Pregão

- **WHEN** o usuário seleciona a sub-aba "Dominância do Pregão"
- **THEN** o OrientationPanel DEVE exibir título e texto explicativo sobre Range, Range%, Typical Price, Median Price e Weighted Close

#### Scenario: OrientationPanel para Fluxo Financeiro

- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o OrientationPanel DEVE exibir título e texto explicativo sobre CLV, Money Flow Volume, Buying Pressure e Selling Pressure

### Requirement: Exposição dos resultados do engine DAG para a GUI

O sistema DEVE expor os resultados completos do `IndicatorEngine.execute()` para que os widgets da GUI possam consumir qualquer indicador pelo seu `id`.

#### Scenario: Consumo de indicador pela GUI

- **WHEN** o engine retorna resultados com `results["clv"]["PETR4"]` contendo dados de CLV
- **THEN** o widget da sub-aba "Fluxo Financeiro" DEVE acessar `results["clv"]` para exibir o CLV do ticker selecionado
