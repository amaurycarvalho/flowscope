## ADDED Requirements

### Requirement: Fallback de cotação, VP/Cota e data de referência

Quando o Fundamentus não fornecer cotação, valor patrimonial por cota ou a data de referência de mercado, o sistema DEVE preencher esses campos a partir das fontes de fallback — preço de fechamento da B3 e patrimônio do Informe Mensal da B3/CVM — registrando a origem do valor utilizado.

#### Scenario: Cotação ausente no Fundamentus
- **WHEN** o Fundamentus não fornece a cotação de um ticker e a B3 possui o último fechamento até a data de referência
- **THEN** o sistema DEVE usar o preço da B3 como `P (Cotação)`

#### Scenario: VP/Cota ausente no Fundamentus
- **WHEN** o Fundamentus não fornece `VP/Cota` e o patrimônio da B3 ou da CVM está disponível
- **THEN** o sistema DEVE preencher `VP (VP/Cota)` com o valor patrimonial por cota da fonte, ou derivá-lo de `patrimônio líquido / cotas`

#### Scenario: Data de referência ausente no Fundamentus
- **WHEN** o Fundamentus não fornece a data de última cotação e existe preço de fechamento da B3
- **THEN** o sistema DEVE usar a data do último fechamento da B3 como `Data de referência`

#### Scenario: Nenhuma fonte fornece o campo
- **WHEN** nem o Fundamentus nem a B3/CVM fornecem o campo
- **THEN** a coluna correspondente DEVE ser exibida como `N/A` sem impedir as demais

### Requirement: Fallback do Preço Típico pela janela de mercado em cache

Quando o Fundamentus não fornecer a máxima e a mínima de 52 semanas, o sistema DEVE preencher os extremos com o menor preço mínimo e o maior preço máximo da janela de mercado da B3 já carregada em cache para a análise, restrita a 52 semanas antes da data de referência, sem realizar novo acesso à B3, e DEVE calcular `Preço Típico` e `P / PT` a partir desses extremos. Quando a janela em cache não tiver nenhum dia válido, `Preço Típico` e `P / PT` DEVEM ser exibidos como `N/A`.

#### Scenario: Fundamentus sem extremos de 52 semanas
- **WHEN** o Fundamentus não fornece a máxima e a mínima de 52 semanas e a janela da B3 em cache contém dias dentro das últimas 52 semanas
- **THEN** o sistema DEVE usar o menor mínimo e o maior máximo desses dias como `Min 52 sem` e `Max 52 sem` para calcular `Preço Típico` e `P / PT`

#### Scenario: Janela de cache vazia
- **WHEN** o Fundamentus não fornece os extremos e a janela da B3 em cache não contém dias válidos
- **THEN** `Preço Típico` e `P / PT` DEVEM ser `N/A`

#### Scenario: Extremos do Fundamentus presentes
- **WHEN** o Fundamentus fornece a máxima e a mínima de 52 semanas
- **THEN** o sistema DEVE usá-las, sem consultar a janela em cache
