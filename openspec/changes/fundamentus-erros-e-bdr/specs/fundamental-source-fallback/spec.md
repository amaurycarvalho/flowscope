## MODIFIED Requirements

### Requirement: Fallback por falha de conexão ou scraping

Quando a aquisição no Fundamentus falhar, o sistema DEVE continuar a análise usando as fontes de fallback, sem interromper os demais tickers. Um ticker não encontrado NÃO DEVE ser tratado como falha inesperada: DEVE ser registrado em nível informativo, sem traceback. Falhas de rede e de layout DEVEM manter o registro de aviso com traceback, por sinalizarem problemas que exigem atenção.

#### Scenario: Fundamentus indisponível
- **WHEN** a requisição ao Fundamentus falha para um ticker
- **THEN** o sistema DEVE compor os campos com B3/CVM/motor de FFO e manter a linha do ticker na tabela

#### Scenario: Isolamento entre tickers
- **WHEN** um ticker falha em todas as fontes
- **THEN** os demais tickers DEVEM continuar sendo processados normalmente

#### Scenario: Ticker ausente não é falha inesperada
- **WHEN** o Fundamentus sinaliza que o ticker não foi encontrado
- **THEN** o sistema DEVE registrar o fato em nível informativo, sem traceback, e seguir para o fallback
