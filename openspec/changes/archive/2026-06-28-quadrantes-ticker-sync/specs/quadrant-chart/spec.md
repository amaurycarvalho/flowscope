## MODIFIED Requirements

### Requirement: Setas de trajetória temporal (quiver)

O sistema DEVE exibir setas (quiver) conectando os dias anteriores de cada ticker apenas quando um ticker específico estiver selecionado no combobox de seleção de ticker do gráfico. A cauda representa o dia anterior e a ponta o dia atual, permitindo visualizar a evolução temporal. Quando "Todos" estiver selecionado, as setas NÃO devem ser exibidas.

#### Scenario: Ativo com 3 dias — ticker específico selecionado
- **WHEN** o usuário seleciona um ticker específico no combobox e o ativo possui dados em 3 dias (D1, D2, D3)
- **THEN** o sistema DEVE exibir duas setas: D1→D2 e D2→D3, com a bolha em D3

#### Scenario: Ativo com 3 dias — "Todos" selecionado
- **WHEN** o usuário seleciona "Todos" no combobox e um ativo possui dados em 3 dias (D1, D2, D3)
- **THEN** o sistema DEVE exibir a bolha em D3 sem as setas de trajetória

#### Scenario: Ativo com apenas 1 dia — ticker específico selecionado
- **WHEN** o usuário seleciona um ticker específico e ele possui dados em apenas 1 dia
- **THEN** o sistema DEVE exibir apenas a bolha, sem setas
