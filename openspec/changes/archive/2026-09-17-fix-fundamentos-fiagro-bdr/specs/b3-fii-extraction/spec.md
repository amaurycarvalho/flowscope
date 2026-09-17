## ADDED Requirements

### Requirement: Resolução de ticker para múltiplos tipos de fundo

O sistema DEVE resolver a identidade de um ticker de fundo na B3 consultando `GetListFunds` para mais de um tipo de fundo, tentando `FII`, `FIAGRO`, `FIP` e `FIDC` até encontrar o registro cujo `acronym` corresponde à raiz do ticker. Cada tipo DEVE ser consultado uma única vez por período de validade, com cache próprio por tipo. Encontrado o registro primário, o sistema DEVE resolver o `idFNET` final via `GetListClassFund` para aquele tipo, preferindo o registro com `idMain` não nulo. Ticker sem correspondência em nenhum tipo DEVE resultar em ausência de fundo, sem lançar exceção.

#### Scenario: FIAGRO resolvido fora do tipo FII
- **WHEN** `GetListFunds(typeFund="FII")` não retorna `BBGO`, mas `GetListFunds(typeFund="FIAGRO")` retorna `acronym=BBGO, id=6919`
- **THEN** o sistema DEVE resolver o fundo e obter o `idFNET` derivado via `GetListClassFund` com `typeFund="FIAGRO"`

#### Scenario: Cache por tipo de fundo
- **WHEN** a listagem do tipo `FIAGRO` já foi obtida dentro do período de validade
- **THEN** o sistema DEVE reutilizá-la sem nova requisição HTTP ao consultar outro ticker FIAGRO

#### Scenario: Ticker não encontrado em nenhum tipo
- **WHEN** nenhum tipo de fundo contém o `acronym` do ticker
- **THEN** o sistema DEVE indicar ausência de fundo sem erro

#### Scenario: Ordem de tentativa preservada
- **WHEN** o ticker corresponde a um FII clássico
- **THEN** o sistema DEVE resolvê-lo na tentativa do tipo `FII`, sem consultar os tipos seguintes
