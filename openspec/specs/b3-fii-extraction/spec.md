# b3-fii-extraction Specification

## Purpose
Aquisição determinística de identidade e documentos de FII na B3 (`fundsListedProxy` e FundosNet), provendo o identificador FNET, o nome do fundo e os proventos estruturados de rendimentos/amortizações com paginação, retry, rate-limit, cache e preservação de metadados.

## Requirements

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

### Requirement: Listagem paginada de documentos de rendimentos

O sistema DEVE listar os documentos estruturados de rendimentos e amortizações (`GetStructuredReports`, `type=41`) de um fundo em um período, tratando o bloco `page` como contrato e continuando as requisições até `pageNumber` exceder `totalPages`. A ausência de documentos DEVE resultar em lista vazia, distinta de falha de aquisição.

#### Scenario: Múltiplas páginas
- **WHEN** a primeira página informa `totalPages=3`
- **THEN** o sistema DEVE requisitar as páginas 2 e 3 e consolidar todos os `results` em uma única lista

#### Scenario: Período sem documentos
- **WHEN** a resposta informa `totalRecords=0`
- **THEN** o sistema DEVE retornar lista vazia sem erro

### Requirement: Download e extração de documento FundosNet

O sistema DEVE, para cada documento listado, obter o identificador a partir de `urlViewerFundosNet`, baixar o documento e extrair os campos estruturados do provento (entidade e provento), reutilizando as estratégias de parsing tolerantes a HTML malformado.

#### Scenario: Documento com identificador na URL
- **WHEN** a URL do documento contém `?id=<N>`
- **THEN** o sistema DEVE usar `<N>` como identificador e retornar o provento extraído

#### Scenario: Documento sem provento extraível
- **WHEN** o documento não contém um código ISIN reconhecível
- **THEN** o sistema DEVE registrar a falha daquele documento sem interromper os demais

### Requirement: Retry e rate-limit na aquisição

O sistema DEVE repetir requisições que falharem por erro transitório, respeitando uma sequência de espera crescente, e NÃO DEVE repetir automaticamente erros permanentes (como HTTP 400 e 404). As requisições DEVEM ser serializadas por host, no máximo uma por vez.

#### Scenario: Erro transitório é repetido
- **WHEN** uma requisição falha por erro de conexão e uma tentativa seguinte tem sucesso
- **THEN** o sistema DEVE retornar a resposta bem-sucedida sem propagar a falha

#### Scenario: Erro permanente não é repetido
- **WHEN** uma requisição retorna HTTP 404
- **THEN** o sistema NÃO DEVE repetir a requisição

### Requirement: Resultado de aquisição com metadados e distinção de falha

O sistema DEVE produzir um resultado de aquisição que preserva os dados brutos e os metadados (endpoint, payload, data de obtenção, status HTTP, versão do parser), e que distingue explicitamente lista vazia de falha de aquisição, registrando avisos e erros em vez de retornar um conjunto parcialmente válido como se estivesse completo.

#### Scenario: Falha em um conjunto
- **WHEN** a listagem de rendimentos falha por indisponibilidade da B3
- **THEN** o resultado DEVE registrar a falha em `errors` e sinalizar o conjunto como indisponível, não como lista vazia

#### Scenario: Resposta bruta preservada
- **WHEN** uma resposta JSON é obtida com sucesso
- **THEN** o sistema DEVE preservar a resposta bruta e os metadados da requisição para reprocessamento e auditoria

### Requirement: Validações de entrada da aquisição

O sistema DEVE validar o ticker (não vazio, sem espaços internos, convertido para maiúsculas), o identificador FNET (numérico) e o intervalo de datas (`dataInicial` não posterior a `dataFinal`) antes de consultar as fontes.

#### Scenario: Intervalo de datas inválido
- **WHEN** a data inicial é posterior à data final
- **THEN** o sistema DEVE rejeitar a consulta com erro de validação sem realizar requisição

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
