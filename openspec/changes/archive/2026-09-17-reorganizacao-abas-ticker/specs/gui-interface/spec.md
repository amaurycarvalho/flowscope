## MODIFIED Requirements

### Requirement: Sub-aba Fundamentos na Análise Geral
O sistema DEVE adicionar uma sub-aba "Fundamentos" como a **primeira** sub-aba do sub-notebook da aba "Análise Geral", exibindo uma tabela fundamentalista para os tickers selecionados no Listbox. A sub-aba "Fundamentos" DEVE preceder "VWAP", "Quadrantes" e "Dominância do Pregão".

#### Scenario: Sub-aba Fundamentos é a primeira
- **WHEN** o usuário navega para a aba "Análise Geral"
- **THEN** a primeira sub-aba do sub-notebook DEVE ser "Fundamentos"

#### Scenario: Sub-aba Fundamentos exibe tabela
- **WHEN** o usuário navega para a aba "Análise Geral" e seleciona a sub-aba "Fundamentos"
- **THEN** o sistema DEVE exibir uma tabela com uma linha por ticker selecionado no Listbox

#### Scenario: Tabela usa os tickers do Listbox
- **WHEN** o usuário seleciona 5 tickers no Listbox e navega para a sub-aba "Fundamentos"
- **THEN** a tabela DEVE exibir os dados fundamentalistas para os 5 tickers selecionados
