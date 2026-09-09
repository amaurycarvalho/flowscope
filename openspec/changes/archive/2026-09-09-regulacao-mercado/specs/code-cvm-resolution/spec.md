## ADDED Requirements

### Requirement: Resolução de ticker para codeCVM
O sistema DEVE resolver um ticker da B3 para seu código CVM correspondente via API `listedCompaniesProxy`. A resolução DEVE ser cacheada com TTL de 30 dias. Para tickers sem código CVM, o sistema DEVE retornar `None` sem lançar exceção.

#### Scenario: Ticker de empresa listada retorna codeCVM
- **WHEN** `resolver_code_cvm("PETR4")` é chamado
- **THEN** o sistema DEVE retornar uma string contendo o código CVM da Petrobras (ex: "9512")

#### Scenario: Ticker não listado retorna None
- **WHEN** `resolver_code_cvm("TICKER_INEXISTENTE")` é chamado
- **THEN** o sistema DEVE retornar `None` sem lançar exceção

#### Scenario: Cache evita requisições repetidas
- **WHEN** `resolver_code_cvm("PETR4")` é chamado duas vezes em menos de 30 dias
- **THEN** a segunda chamada DEVE retornar do cache sem nova requisição HTTP

#### Scenario: Cache armazena None para tickers sem codeCVM
- **WHEN** `resolver_code_cvm("TICKER_SEM_CVM")` retorna `None`
- **THEN** o valor `None` DEVE ser cacheado para evitar requisições repetidas ao mesmo ticker inválido

### Requirement: Compartilhamento da resolução com outras changes
A infraestrutura de resolução `ticker → codeCVM` DEVE ser implementada no `B3FundosClient` e estar disponível para uso por outras changes que necessitem acessar dados CVM.

#### Scenario: Método acessível via B3FundosClient
- **WHEN** uma instância de `B3FundosClient` é criada com `CacheManager`
- **THEN** o método `resolver_code_cvm(ticker: str) -> str | None` DEVE estar disponível
