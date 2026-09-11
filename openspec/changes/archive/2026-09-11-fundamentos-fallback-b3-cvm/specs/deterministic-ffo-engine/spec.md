## MODIFIED Requirements

### Requirement: Integração com as métricas fundamentalistas

O FFO calculado DEVE atuar como fallback das métricas `FFO Yield`, `P/FFO` e `FFO Trend` da análise fundamentalista, sendo usado quando o Fundamentus não fornecer o dado. O motor determinístico DEVE ser aplicado apenas a FIIs de tijolo ou híbrido; para FII de papel, as métricas derivadas do motor DEVEM permanecer `N/A`, sem afetar os valores de FFO reportados pelo Fundamentus.

#### Scenario: Métricas de FFO preenchidas
- **WHEN** o FFO 12m e o preço estão disponíveis para um FII de tijolo ou híbrido
- **THEN** `FFO Yield` e `P/FFO` DEVEM ser calculados e exibidos

#### Scenario: FII de papel
- **WHEN** o ativo é um FII de papel sem FFO reportado pelo Fundamentus
- **THEN** `FFO Yield`, `P/FFO` e `FFO Trend` DEVEM ser exibidos como `N/A`

#### Scenario: FFO indisponível
- **WHEN** os componentes necessários não estão disponíveis
- **THEN** as métricas de FFO DEVEM ser exibidas como `N/A` sem impedir as demais
