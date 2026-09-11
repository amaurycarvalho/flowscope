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

O sistema DEVE, para cada documento listado, obter o identificador a partir de `urlViewerFundosNet`, baixar o documento e extrair os campos estruturados do provento (entidade e provento), reutilizando as estratégias de parsing tolerantes a HTML malformado. No layout real do documento, em que `Rendimento` e `Amortização` são colunas e cada linha de atributo traz o valor na coluna aplicável, o sistema DEVE identificar o tipo do provento pela coluna que contém o valor (não pela presença de um marcador `X`) e DEVE extrair a `Data-base` mesmo quando o rótulo vier acompanhado de texto parentético (ex.: `Data-base (último dia de negociação "com" direito ao provento)`).

#### Scenario: Documento com identificador na URL
- **WHEN** a URL do documento contém `?id=<N>`
- **THEN** o sistema DEVE usar `<N>` como identificador e retornar o provento extraído

#### Scenario: Documento sem provento extraível
- **WHEN** o documento não contém um código ISIN reconhecível
- **THEN** o sistema DEVE registrar a falha daquele documento sem interromper os demais

#### Scenario: Rendimento no layout de duas colunas
- **WHEN** o documento traz as colunas `Rendimento` e `Amortização` e a linha `Data-base`/`Valor do provento` tem o valor na coluna `Rendimento`
- **THEN** o provento extraído DEVE ter tipo `Rendimento`, com `data_base` preenchida pela data da linha `Data-base`

#### Scenario: Amortização no layout de duas colunas
- **WHEN** o documento traz as colunas `Rendimento` e `Amortização` e o valor está na coluna `Amortização`
- **THEN** o provento extraído DEVE ter tipo `Amortização`

#### Scenario: Data-base com rótulo parentético
- **WHEN** o rótulo da data-base contém texto adicional entre parênteses
- **THEN** a data-base DEVE ser extraída do valor associado ao rótulo

### Requirement: Teste de contrato do documento FundosNet real

O sistema DEVE manter uma fixture estática de um documento FundosNet real de rendimentos e amortizações e um teste de contrato que garanta a extração de `tipo` e `data_base`, de modo que uma mudança de layout da B3 seja detectada explicitamente.

#### Scenario: Fixture real valida a extração
- **WHEN** o parser é executado sobre a fixture do documento real
- **THEN** o provento DEVE ser classificado como `Rendimento` e conter `data_base` não nula

#### Scenario: Mudança de layout detectada
- **WHEN** a fixture perde a coluna de valor ou o rótulo de data-base
- **THEN** o teste de contrato DEVE falhar explicitamente

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

O sistema DEVE listar os documentos do Informe Mensal Estruturado (`GetStructuredReports`, `type=40`) de um fundo e, para o documento ativo mais recente cuja referência não seja posterior à data de referência, baixar o HTML do FundosNet e extrair, por rótulo, o número de cotistas, o patrimônio líquido, a quantidade de cotas emitidas, o valor patrimonial por cota e a classificação autorregulação do fundo (Classificação, Subclassificação, Gestão e Segmento de Atuação). A ausência de informes DEVE resultar em ausência de dados, distinta de falha de aquisição.

#### Scenario: Informe mensal extraído
- **WHEN** o informe ativo mais recente contém os rótulos `Número de cotistas`, `Patrimônio Líquido`, `Número de Cotas Emitidas` e `Valor Patrimonial das Cotas`
- **THEN** o sistema DEVE expor o número de cotistas, o patrimônio líquido, as cotas emitidas e o VP/Cota, com a data de referência do informe

#### Scenario: Classificação autorregulação extraída
- **WHEN** o informe ativo contém o rótulo `Classificação autorregulação` com Classificação, Subclassificação, Gestão e Segmento de Atuação
- **THEN** o sistema DEVE expor esses quatro campos no informe normalizado, tolerando rótulos ausentes

#### Scenario: Sem informes no período
- **WHEN** a listagem `type=40` retorna lista vazia
- **THEN** o sistema DEVE indicar ausência de dados sem erro

#### Scenario: Falha ao baixar o documento
- **WHEN** o download do documento do FundosNet falha
- **THEN** o sistema DEVE registrar a falha como indisponibilidade, não como ausência de dados

### Requirement: Cache do HTML do documento FundosNet

O sistema DEVE persistir o HTML bruto de cada documento do FundosNet obtido por `buscar_html_documento`, indexado pelo identificador do documento, de modo que solicitações subsequentes do mesmo documento sejam servidas do cache sem nova requisição HTTP. O cache DEVE ser compartilhado entre os documentos de proventos (`type=41`) e os do informe mensal (`type=40`), que usam o mesmo endpoint. Quando o download falhar e existir HTML armazenado, o sistema DEVE servir o conteúdo em cache; sem conteúdo armazenado, DEVE sinalizar a indisponibilidade.

#### Scenario: Documento servido do cache
- **WHEN** o HTML de um documento já foi baixado e é solicitado novamente dentro do período de retenção
- **THEN** o sistema DEVE devolver o HTML armazenado sem realizar nova requisição HTTP

#### Scenario: Documento novo é armazenado
- **WHEN** um documento ainda não está em cache
- **THEN** o sistema DEVE baixar o HTML e armazená-lo indexado pelo identificador do documento

#### Scenario: Proventos e informe mensal compartilham o cache
- **WHEN** o mesmo identificador de documento é lido pela extração de proventos e pela extração do informe mensal
- **THEN** o HTML DEVE ser baixado uma única vez e reutilizado pelas duas leituras

#### Scenario: Falha de rede com cache disponível
- **WHEN** o download do documento falha por indisponibilidade e existe HTML armazenado para o identificador
- **THEN** o sistema DEVE servir o conteúdo em cache

#### Scenario: Falha de rede sem cache
- **WHEN** o download do documento falha e não existe HTML armazenado para o identificador
- **THEN** o sistema DEVE sinalizar a indisponibilidade, sem retornar conteúdo vazio como se fosse válido

### Requirement: Cache da identidade do fundo

O sistema DEVE persistir a resposta de `GetListClassFund` usada na resolução de identidade, indexada pelo `id` primário do fundo, de modo que `find_by_ticker` não consulte a B3 novamente dentro do período de validade. A ausência de correspondência NÃO DEVE ser armazenada, para não congelar falhas transitórias.

#### Scenario: Identidade servida do cache
- **WHEN** a identidade de um fundo já foi resolvida e é solicitada novamente dentro do período de validade
- **THEN** o sistema DEVE devolver os registros de classe armazenados sem nova requisição HTTP

#### Scenario: Validade vencida reconsulta a fonte
- **WHEN** o período de validade da identidade armazenada vence
- **THEN** o sistema DEVE consultar a B3 novamente e substituir o cache

#### Scenario: Ticker sem correspondência não é cacheado
- **WHEN** a resolução de um ticker não encontra correspondência na B3
- **THEN** o resultado vazio NÃO DEVE ser armazenado, permitindo nova tentativa em execução futura

### Requirement: Chaves de cache versionadas e políticas centralizadas

O sistema DEVE versionar as chaves de cache de documentos e de identidade com a versão do parser/aquisição da B3 e DEVE centralizar os prazos de validade e os nomes de chave em constantes do cliente, para que uma mudança de parser invalide os registros anteriores e as políticas de cache evoluam em um único ponto.

#### Scenario: Mudança de versão do parser invalida registros
- **WHEN** a versão do parser/aquisição difere da versão registrada no cache
- **THEN** os registros de documento e de identidade anteriores DEVEM ser tratados como ausentes e a fonte DEVE ser consultada novamente

#### Scenario: Política de cache em um único ponto
- **WHEN** um prazo de validade ou nome de chave da aquisição B3 precisa mudar
- **THEN** a alteração DEVE ocorrer nas constantes do cliente, sem duplicar valores literais nos métodos de aquisição

### Requirement: Extração da identidade fiscal do Informe Mensal Estruturado

O sistema DEVE extrair, por rótulo, o CNPJ do fundo e o administrador (nome e CNPJ) do HTML do Informe Mensal Estruturado do FundosNet, tolerando rótulos ausentes sem invalidar os demais campos do informe.

#### Scenario: CNPJ do fundo extraído
- **WHEN** o informe ativo contém o rótulo `CNPJ do Fundo/Classe`
- **THEN** o sistema DEVE expor o CNPJ do fundo normalizado

#### Scenario: Administrador e CNPJ extraídos
- **WHEN** o informe ativo contém os rótulos `Nome do Administrador` e `CNPJ do Administrador`
- **THEN** o sistema DEVE expor o nome e o CNPJ do administrador

#### Scenario: Rótulo ausente
- **WHEN** um dos rótulos de identidade fiscal está ausente
- **THEN** o campo correspondente DEVE ser ausência de valor, sem impedir a extração dos demais
