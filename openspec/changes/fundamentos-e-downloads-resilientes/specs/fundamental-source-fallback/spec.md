## ADDED Requirements

### Requirement: Nome de exibição a partir da identidade B3 existente

Quando o nome de exibição não for fornecido pela fonte primária, o sistema DEVE obter o nome a partir da identidade B3 já consultada para o ticker, sem nova fonte de dados: para ações e BDR, do cadastro de empresas listadas (`companyName`/`tradingName`); para FII, da listagem de fundos (`fundName`). O nome obtido DEVE ser preservado como proveniência da respectiva fonte.

#### Scenario: Nome de ação sem a fonte primária
- **WHEN** a fonte primária está indisponível e o ticker é uma ação ou BDR listado
- **THEN** o nome de exibição DEVE ser obtido do cadastro de empresas listadas da B3

#### Scenario: Nome de FII sem a fonte primária
- **WHEN** a fonte primária está indisponível e o ticker é um FII
- **THEN** o nome de exibição DEVE ser obtido da listagem de fundos da B3

#### Scenario: Sem identidade, o nome permanece ausente
- **WHEN** nem a fonte primária nem a identidade B3 fornecem o nome do ticker
- **THEN** o nome DEVE permanecer ausente, sinalizado como `N/A`, sem erro fatal

### Requirement: Registro da fonte indisponível na composição

Ao consultar as fontes em ordem de prioridade, o sistema DEVE registrar no log a fonte que ficou indisponível para o ticker (por exemplo, falha de rede ou de verificação TLS), mantendo a tolerância atual: a indisponibilidade de uma fonte NÃO DEVE interromper a análise nem os demais tickers.

#### Scenario: Fonte indisponível registrada na composição
- **WHEN** uma fonte da composição falha para um ticker
- **THEN** o log DEVE registrar a fonte e o ticker, e a composição DEVE seguir para a próxima fonte

#### Scenario: Ticker sem dados em uma fonte não é erro
- **WHEN** uma fonte não encontra dados para o ticker (sem dados, distinto de falha)
- **THEN** o evento DEVE ser registrado como informativo e a composição DEVE seguir para a próxima fonte
