## ADDED Requirements

### Requirement: Fallback de dividendos e identidade de BDR

Para ativos classificados como BDR, o sistema DEVE usar a fonte de dividendos de BDR como fonte secundária de dividendos, consolidando-a com as demais fontes e preservando a origem de cada valor. Quando o último dividendo do BDR existir, o sistema DEVE usá-lo para preencher data-com, dividendo anterior, tendência, P/L e Dividend Yield. O sistema DEVE expor o caminho da pasta de cache dos PDFs do BDR e, na ausência de identidade fiscal nas fontes primárias, o depositário, a empresa e o ISIN obtidos dos avisos.

#### Scenario: BDR com dividendos na fonte secundária
- **WHEN** a B3 e o Fundamentus não fornecem dividendos para o BDR e a fonte de BDR retorna o último dividendo e a data-com
- **THEN** a análise DEVE preencher último dividendo, data-com e tendência com os valores da fonte de BDR, registrando a origem

#### Scenario: BDR sem dados em nenhuma fonte
- **WHEN** nenhuma fonte fornece dividendos para o BDR
- **THEN** as colunas de dividendo DEVEM ser `N/A`, sem impedir as demais

#### Scenario: Identidade fiscal de BDR
- **WHEN** o BDR não possui CNPJ/administrador/gestor nas fontes primárias
- **THEN** `Dados fiscais` DEVE exibir depositário, empresa e ISIN obtidos dos avisos, omitindo itens indisponíveis

#### Scenario: Caminho de cache exposto
- **WHEN** a análise de um BDR é concluída com PDFs em cache
- **THEN** `Informações adicionais` DEVE exibir o caminho da pasta de cache do ticker

#### Scenario: Ativo não-BDR preservado
- **WHEN** o ativo não é um BDR
- **THEN** a fonte de BDR NÃO DEVE ser consultada e o comportamento das fontes existentes DEVE ser mantido
