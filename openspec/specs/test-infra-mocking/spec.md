## Purpose

Define test coverage requirements for infrastructure-layer components (B3Client, B3DataRepository, CacheManager) and application-layer components (AnalyzeTickersUseCase, OperationGuard, LoadIndexPortfolioUseCase) to ensure reliable mocking and error handling.

## Requirements

### Requirement: B3Client deve ter fetch testado com cache hit/miss e falha HTTP

O sistema DEVE testar `B3Client.fetch_file()` nos cenários de cache hit (dado já em cache), cache miss (download HTTP mockado), e falha HTTP no download. O sistema DEVE testar `B3Client.fetch_portfolio()` com resposta válida, vazia, e falha HTTP.

#### Scenario: fetch_file retorna dado do cache quando disponível
- **WHEN** `B3Client.fetch_file()` é chamado com uma data cujo conteúdo já está no cache
- **THEN** o método retorna o conteúdo do cache sem fazer requisição HTTP

#### Scenario: fetch_file baixa via HTTP quando cache está vazio
- **WHEN** `B3Client.fetch_file()` é chamado com uma data sem cache
- **THEN** o método faz requisição HTTP, armazena no cache, e retorna o conteúdo baixado

#### Scenario: fetch_file repassa falha HTTP como RuntimeError
- **WHEN** o download HTTP retorna status de erro
- **THEN** `B3Client.fetch_file()` levanta `RuntimeError`

#### Scenario: fetch_file com progress_callback reporta cache hit
- **WHEN** `B3Client.fetch_file()` encontra dado em cache
- **AND** um `progress_callback` é fornecido
- **THEN** o callback é invocado com a mensagem indicando cache

#### Scenario: fetch_portfolio retorna lista de tickers
- **WHEN** `B3Client.fetch_portfolio("IBOV")` é chamado
- **AND** o servidor retorna CSV válido
- **THEN** o método retorna lista de strings com os tickers

#### Scenario: fetch_portfolio retorna lista vazia quando resposta é vazia
- **WHEN** `B3Client.fetch_portfolio("IBOV")` é chamado
- **AND** o servidor retorna resposta vazia
- **THEN** a excessão é logada e o método retorna lista vazia

#### Scenario: fetch_portfolio retorna lista vazia quando HTTP falha
- **WHEN** `B3Client.fetch_portfolio("IBOV")` é chamado
- **AND** a requisição HTTP lança excessão
- **THEN** `B3Client.fetch_portfolio()` retorna lista vazia

### Requirement: B3DataRepository deve ter fetch_trades testado com erros de parser e download

O sistema DEVE testar `B3DataRepository.fetch_trades()` nos cenários de parser bem-sucedido, erro de parser (CSV inválido), erro de download (HTTP fail), e filtro por tickers.

#### Scenario: fetch_trades processa múltiplas datas com parser bem-sucedido
- **WHEN** `B3DataRepository.fetch_trades()` é chamado com um date_range de 2 datas
- **AND** ambas as datas retornam CSV válido do B3Client
- **THEN** o resultado contém trades de ambas as datas

#### Scenario: fetch_trades ignora datas com erro de parser e continua
- **WHEN** `B3DataRepository.fetch_trades()` é chamado com 2 datas
- **AND** a primeira data retorna CSV inválido (ParseError)
- **AND** a segunda data retorna CSV válido
- **THEN** o resultado contém apenas trades da segunda data

#### Scenario: fetch_trades ignora datas com erro de download e continua
- **WHEN** `B3DataRepository.fetch_trades()` é chamado com 2 datas
- **AND** a primeira data lança excessão no download
- **AND** a segunda data retorna CSV válido
- **THEN** o resultado contém apenas trades da segunda data

#### Scenario: fetch_trades filtra por tickers quando fornecido
- **WHEN** `B3DataRepository.fetch_trades()` é chamado com tickers=["PETR4"]
- **THEN** o resultado contém apenas trades com ticker PETR4

### Requirement: CacheManager deve ter get_or_fetch e invalidate testados

O sistema DEVE testar `CacheManager.get_or_fetch()` com cache válido (dentro do TTL), expirado (fora do TTL), cache ausente, e fetch function que falha. O sistema DEVE testar `CacheManager.invalidate()` com chave existente e inexistente.

#### Scenario: get_or_fetch retorna cache válido dentro do TTL
- **WHEN** `get_or_fetch()` é chamado com uma chave que tem cache recente
- **THEN** retorna o dado em cache sem executar fetch_fn

#### Scenario: get_or_fetch executa fetch_fn quando cache está expirado
- **WHEN** `get_or_fetch()` é chamado com uma chave cujo cache está fora do TTL
- **THEN** executa fetch_fn, armazena resultado, e retorna dado atualizado

#### Scenario: get_or_fetch executa fetch_fn quando cache não existe
- **WHEN** `get_or_fetch()` é chamado com uma chave sem cache existente
- **THEN** executa fetch_fn, armazena resultado, e retorna dado novo

#### Scenario: invalidate remove chave existente
- **WHEN** `invalidate()` é chamado com uma chave que tem cache
- **THEN** o arquivo de cache é removido do disco

#### Scenario: invalidate não levanta excessão para chave inexistente
- **WHEN** `invalidate()` é chamado com uma chave sem cache
- **THEN** não levanta excessão alguma

### Requirement: AnalyzeTickersUseCase deve ter execute testado com e sem filtro de tickers

O sistema DEVE testar `AnalyzeTickersUseCase.execute()` nos cenários: com lista de tickers fornecida, sem tickers (usando top_tickers do engine), com progress_callback, e quando não há trades retornados.

#### Scenario: execute com tickers fornecidos retorna resultado por ticker
- **WHEN** `AnalyzeTickersUseCase.execute()` é chamado com tickers=["PETR4"]
- **THEN** o resultado contém chave "PETR4" com dados de vwap, volume_profile, daily_data, money_flow_volume, e all_indicators

#### Scenario: execute sem tickers usa top_tickers do engine
- **WHEN** `AnalyzeTickersUseCase.execute()` é chamado sem tickers
- **THEN** o método usa `top_tickers` do engine para determinar quais tickers incluir

#### Scenario: execute com progress_callback invoca callback durante execução
- **WHEN** `AnalyzeTickersUseCase.execute()` é chamado com um progress_callback
- **THEN** o callback é invocado pelo menos uma vez durante a execução

#### Scenario: execute retorna dict vazio quando não há trades
- **WHEN** `AnalyzeTickersUseCase.execute()` é chamado sem trades retornados pelo repositório
- **THEN** o resultado é um dict vazio

### Requirement: OperationGuard deve ter acquire testado nos estados livre e ocupado

O sistema DEVE testar `OperationGuard.acquire()` retornando `True` quando livre, `False` quando ocupado, e voltando a `False` após liberação.

#### Scenario: acquire retorna True quando está livre
- **WHEN** `OperationGuard.acquire()` é usado como context manager
- **THEN** o valor yieldado é `True`

#### Scenario: acquire retorna False quando está ocupado
- **WHEN** `OperationGuard.acquire()` já está ativo
- **AND** uma segunda chamada `acquire()` é feita
- **THEN** a segunda chamada retorna `False`

#### Scenario: acquire volta a True após liberação do primeiro contexto
- **WHEN** o primeiro `acquire()` sai do bloco `with`
- **AND** um novo `acquire()` é chamado
- **THEN** o novo acquire retorna `True`

### Requirement: LoadIndexPortfolioUseCase deve ter execute testado com índices válidos, inválidos, e retorno vazio

O sistema DEVE testar `LoadIndexPortfolioUseCase.execute()` com índice válido (IBOV/IDIV/IFIX), índice inválido (levanta InvalidIndexError), e portfólio vazio (levanta PortfolioNotFoundError).

#### Scenario: execute com índice IBOV retorna lista de tickers
- **WHEN** `LoadIndexPortfolioUseCase.execute("IBOV")` é chamado
- **AND** o repositório retorna tickers válidos
- **THEN** o resultado é uma lista de strings

#### Scenario: execute com índice inválido levanta InvalidIndexError
- **WHEN** `LoadIndexPortfolioUseCase.execute("INVALIDO")` é chamado
- **THEN** levanta `InvalidIndexError`

#### Scenario: execute com portfólio vazio levanta PortfolioNotFoundError
- **WHEN** `LoadIndexPortfolioUseCase.execute("IBOV")` é chamado
- **AND** o repositório retorna lista vazia
- **THEN** levanta `PortfolioNotFoundError`
