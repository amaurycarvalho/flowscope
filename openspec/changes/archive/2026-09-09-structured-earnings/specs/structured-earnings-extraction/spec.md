## ADDED Requirements

### Requirement: Listagem paginada de documentos estruturados
O sistema DEVE listar documentos de proventos estruturados (type=41) para um ticker em um período, utilizando o endpoint `GetStructuredReports`. Se a resolução do ticker retornar `None`, a listagem DEVE retornar lista vazia sem erro.

#### Scenario: Listagem com uma única página
- **WHEN** a resposta para `pageNumber=1` contém `totalPages=1`
- **THEN** o sistema DEVE retornar todos os `results` da página sem realizar requisições adicionais

#### Scenario: Listagem com múltiplas páginas
- **WHEN** a resposta para `pageNumber=1` contém `totalPages=3`
- **THEN** o sistema DEVE realizar requisições para `pageNumber=2` e `pageNumber=3`, consolidando todos os `results` em uma única lista

#### Scenario: Ticker sem idFNET — retorna vazio
- **WHEN** a resolução do ticker retorna `None`
- **THEN** o sistema DEVE retornar uma lista vazia sem realizar requisição HTTP

#### Scenario: Período sem documentos
- **WHEN** a resposta contém `totalRecords=0`
- **THEN** o sistema DEVE retornar uma lista vazia sem erro

### Requirement: Cache de listagem de documentos
O sistema DEVE cachear a listagem de documentos utilizando `CacheManager.get_or_fetch` com TTL de 1 dia, chave no formato `fund_docs_{idFNET}_{type}_{dataInicial}_{dataFinal}`.

#### Scenario: Cache hit para listagem recente
- **WHEN** a mesma consulta de documentos foi realizada há menos de 1 dia
- **THEN** o sistema DEVE retornar os documentos do cache sem realizar requisição HTTP

### Requirement: Extração de detalhes de documento de provento
O sistema DEVE, para cada documento da listagem, acessar a URL `urlViewerFundosNet`, fazer parsing do HTML tabular, extrair todos os campos mapeados (dados da entidade, administrador, contato, informação e provento) e retornar uma entidade `DocumentoProvento`.

#### Scenario: Extração completa de um documento
- **WHEN** o sistema acessa a URL de um documento de provento
- **THEN** o sistema DEVE extrair: nome, cnpj, nomeAdministrador, cnpjAdministrador, responsavel, telefone, dataInformacao, anoReferencia, codigoISIN, codigoNegociacao, tipoProvento, dataBase, valorPorUnidade, dataPagamento, periodoReferencia, isentoIR, notaIsencao

#### Scenario: Documento com HTML malformado
- **WHEN** o HTML do documento contém tabelas sem `<thead>` ou com células vazias
- **THEN** o sistema DEVE aplicar as estratégias de fallback definidas em `structured-html-parsing` e extrair o máximo de campos possível

### Requirement: Pipeline completo de extração via Use Case
O sistema DEVE expor um use case `ExtrairProventosUseCase` que orquestra o fluxo completo: recebe um `ProventosRepository` (port), ticker, dataInicial e dataFim, executa a resolução do ticker, lista documentos, extrai detalhes de cada um, e retorna uma lista de `DocumentoProvento`.

#### Scenario: Extração bem-sucedida para um ticker de fundo
- **WHEN** o use case é executado com ticker `ALZR11`, dataInicial `2026-01-01`, dataFim `2026-07-29`
- **THEN** o sistema DEVE retornar uma lista de `DocumentoProvento` com todos os proventos encontrados no período

#### Scenario: Ticker sem resolução — retorna vazio
- **WHEN** o use case é executado com ticker `PETR4`
- **THEN** o sistema DEVE retornar uma lista vazia sem erro

#### Scenario: Erro na extração de um documento individual
- **WHEN** a extração de um documento específico falha (ex: HTML inacessível)
- **THEN** o sistema DEVE logar o erro via `logger.warning` e continuar processando os demais documentos da lista

### Requirement: Progress callback no pipeline de extração
O use case DEVE aceitar um `progress_callback: Callable[[str, bool], None]` e reportar progresso em cada etapa: resolução de ticker, listagem de documentos, extração de cada documento.

#### Scenario: Progresso reportado durante extração
- **WHEN** o use case é executado com um progress callback
- **THEN** o callback DEVE ser invocado para cada etapa com mensagem descritiva e flag de erro `False` para sucessos

### Requirement: CLI para extração de proventos
O sistema DEVE expor a extração via CLI com os argumentos `--structured-earnings <TICKER>`, `--data-inicio <AAAA-MM-DD>`, `--data-fim <AAAA-MM-DD>` e `--output <ARQUIVO>`.

#### Scenario: Extração via CLI com output em arquivo
- **WHEN** o usuário executa `flowscope --structured-earnings ALZR11 --data-inicio 2026-01-01 --data-fim 2026-07-29 --output proventos.json`
- **THEN** o sistema DEVE extrair os proventos e salvar o JSON no arquivo especificado

#### Scenario: Extração via CLI com ticker não-fundo
- **WHEN** o usuário executa `flowscope --structured-earnings PETR4 --data-inicio 2026-01-01 --data-fim 2026-07-29`
- **THEN** o sistema DEVE exibir "Nenhum dado disponível" sem erro
