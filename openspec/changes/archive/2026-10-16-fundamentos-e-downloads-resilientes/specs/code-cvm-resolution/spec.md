## MODIFIED Requirements

### Requirement: Resolução de ticker para codeCVM
O sistema DEVE resolver um ticker da B3 para seu código CVM correspondente exclusivamente via API `listedCompaniesProxy`, consultando `GetInitialCompanies` com o filtro `company` pela raiz do ticker (ticker sem o sufixo numérico) e casando o registro cujo `issuingCompany` é igual a essa raiz. O sistema NÃO DEVE depender do cadastro `empresas-listadas.csv`, cuja URL foi desativada pela B3. Uma resolução bem-sucedida DEVE ser cacheada com TTL de 30 dias sob uma chave versionada. Para tickers sem código CVM — quando a API respondeu e não houve correspondência — o sistema DEVE retornar `None` e cachear esse `None` por 30 dias. Uma **falha de resolução** (erro de rede/HTTP não recuperado após as retentativas) NÃO DEVE ser cacheada como ausência: o sistema DEVE retornar `None` sem gravar o resultado no cache, de modo que uma nova tentativa futura possa resolver o ticker.

#### Scenario: Ticker de empresa listada retorna codeCVM
- **WHEN** `resolver_code_cvm("PETR4")` é chamado
- **THEN** o sistema DEVE consultar `GetInitialCompanies` com `company="PETR"` e retornar o `codeCVM` do registro cujo `issuingCompany` é `PETR` (ex: "9512")

#### Scenario: Homônimos no filtro textual são ignorados
- **WHEN** o filtro `company` retorna empresas cujo nome contém a raiz do ticker, mas nenhuma tem `issuingCompany` igual à raiz
- **THEN** o sistema DEVE ignorar esses registros e continuar a busca

#### Scenario: Ticker não listado retorna None
- **WHEN** `resolver_code_cvm("TICKER_INEXISTENTE")` é chamado e a API responde sem correspondência
- **THEN** o sistema DEVE retornar `None` sem lançar exceção

#### Scenario: Cache evita requisições repetidas
- **WHEN** `resolver_code_cvm("PETR4")` é chamado duas vezes em menos de 30 dias
- **THEN** a segunda chamada DEVE retornar do cache sem nova requisição HTTP

#### Scenario: Cache armazena None para tickers sem codeCVM
- **WHEN** a API responde sem correspondência para um ticker sem código CVM
- **THEN** o valor `None` DEVE ser cacheado para evitar requisições repetidas ao mesmo ticker inválido

#### Scenario: Falha de resolução não é cacheada
- **WHEN** a API `GetInitialCompanies` fica indisponível e a resolução falha após as retentativas
- **THEN** o sistema DEVE retornar `None` sem gravar `None` no cache, de modo que uma nova tentativa futura volte a consultar a API

#### Scenario: Cadastro CSV não é usado
- **WHEN** a API `GetInitialCompanies` está indisponível
- **THEN** o sistema NÃO DEVE baixar nem consultar o cadastro `empresas-listadas.csv` como alternativa

#### Scenario: Chave de cache versionada
- **WHEN** uma resolução é cacheada
- **THEN** a chave DEVE incluir a versão do parser/aquisição, de modo que valores gravados por versões anteriores não sejam reutilizados
