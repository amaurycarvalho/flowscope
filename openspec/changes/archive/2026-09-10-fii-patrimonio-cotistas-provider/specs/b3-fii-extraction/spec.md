## MODIFIED Requirements

### Requirement: Resolução de ticker para fundo B3

O sistema DEVE resolver um ticker para a identidade do fundo na B3 em duas etapas: consultar `GetListFunds` para localizar o registro cujo `acronym` corresponde à raiz do ticker e obter o `id` primário; em seguida consultar `GetListClassFund` com esse `id` como `idFNET` e tratar a resposta como uma relação de registros (`id`, `idMain`, `fundName`, `tradingName`), NÃO assumindo que o primeiro registro é o identificador usado nas consultas seguintes. Quando houver registro com `idMain` não nulo, o `idFNET` final DEVE ser o `id` desse registro; caso contrário, o `id` primário. Ticker sem correspondência DEVE resultar em ausência de fundo, sem lançar exceção.

#### Scenario: Resolução com registro derivado
- **WHEN** `GetListFunds` retorna `acronym=ALZR, id=870` e `GetListClassFund(idFNET=870)` retorna um registro com `id=870, idMain=null` e outro com `id=20294, idMain=870`
- **THEN** o `idFNET` resolvido DEVE ser `20294` e o nome DEVE vir de `fundName`

#### Scenario: Ticker sem correspondência
- **WHEN** nenhum registro de `GetListFunds` corresponde ao `acronym` do ticker
- **THEN** o sistema DEVE indicar ausência de fundo sem erro e sem lançar exceção

#### Scenario: Resolução determinística e cacheada
- **WHEN** o mesmo ticker é resolvido novamente dentro do período de cache
- **THEN** o sistema DEVE retornar o mesmo resultado sem nova requisição HTTP

## ADDED Requirements

### Requirement: Listagem e extração do Informe Mensal Estruturado

O sistema DEVE listar os documentos do Informe Mensal Estruturado (`GetStructuredReports`, `type=40`) de um fundo e, para o documento ativo mais recente cuja referência não seja posterior à data de referência, baixar o HTML do FundosNet e extrair, por rótulo, o número de cotistas, o patrimônio líquido, a quantidade de cotas emitidas e o valor patrimonial por cota. A ausência de informes DEVE resultar em ausência de dados, distinta de falha de aquisição.

#### Scenario: Informe mensal extraído
- **WHEN** o informe ativo mais recente contém os rótulos `Número de cotistas`, `Patrimônio Líquido`, `Número de Cotas Emitidas` e `Valor Patrimonial das Cotas`
- **THEN** o sistema DEVE expor o número de cotistas, o patrimônio líquido, as cotas emitidas e o VP/Cota, com a data de referência do informe

#### Scenario: Sem informes no período
- **WHEN** a listagem `type=40` retorna lista vazia
- **THEN** o sistema DEVE indicar ausência de dados sem erro

#### Scenario: Falha ao baixar o documento
- **WHEN** o download do documento do FundosNet falha
- **THEN** o sistema DEVE registrar a falha como indisponibilidade, não como ausência de dados
