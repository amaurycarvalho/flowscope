## Purpose

Define a resolução de ticker para o código CVM de empresas listadas via API `listedCompaniesProxy` e cadastro de empresas da B3, com cache de 30 dias e retorno `None` para tickers sem código CVM.

## Requirements

### Requirement: Resolução de ticker para codeCVM
O sistema DEVE resolver um ticker da B3 para seu código CVM correspondente via API `listedCompaniesProxy`, consultando `GetInitialCompanies` com o filtro `company` pela raiz do ticker (ticker sem o sufixo numérico) e casando o registro cujo `issuingCompany` é igual a essa raiz. A resolução DEVE ser cacheada com TTL de 30 dias sob uma chave versionada. Para tickers sem código CVM, o sistema DEVE retornar `None` sem lançar exceção.

#### Scenario: Ticker de empresa listada retorna codeCVM
- **WHEN** `resolver_code_cvm("PETR4")` é chamado
- **THEN** o sistema DEVE consultar `GetInitialCompanies` com `company="PETR"` e retornar o `codeCVM` do registro cujo `issuingCompany` é `PETR` (ex: "9512")

#### Scenario: Homônimos no filtro textual são ignorados
- **WHEN** o filtro `company` retorna empresas cujo nome contém a raiz do ticker, mas nenhuma tem `issuingCompany` igual à raiz
- **THEN** o sistema DEVE ignorar esses registros e continuar a busca

#### Scenario: Ticker não listado retorna None
- **WHEN** `resolver_code_cvm("TICKER_INEXISTENTE")` é chamado
- **THEN** o sistema DEVE retornar `None` sem lançar exceção

#### Scenario: Cache evita requisições repetidas
- **WHEN** `resolver_code_cvm("PETR4")` é chamado duas vezes em menos de 30 dias
- **THEN** a segunda chamada DEVE retornar do cache sem nova requisição HTTP

#### Scenario: Cache armazena None para tickers sem codeCVM
- **WHEN** `resolver_code_cvm("TICKER_SEM_CVM")` retorna `None`
- **THEN** o valor `None` DEVE ser cacheado para evitar requisições repetidas ao mesmo ticker inválido

#### Scenario: Chave de cache versionada
- **WHEN** uma resolução é cacheada
- **THEN** a chave DEVE incluir a versão do parser/aquisição, de modo que valores gravados por versões anteriores não sejam reutilizados

### Requirement: Compartilhamento da resolução com outras changes
A infraestrutura de resolução `ticker → codeCVM` DEVE ser implementada no `B3FundosClient` e estar disponível para uso por outras changes que necessitem acessar dados CVM.

#### Scenario: Método acessível via B3FundosClient
- **WHEN** uma instância de `B3FundosClient` é criada com `CacheManager`
- **THEN** o método `resolver_code_cvm(ticker: str) -> str | None` DEVE estar disponível
