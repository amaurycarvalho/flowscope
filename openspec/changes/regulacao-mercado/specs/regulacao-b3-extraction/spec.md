## ADDED Requirements

### Requirement: Extração de Censuras Públicas via parsing HTML
O sistema DEVE extrair a lista de Censuras Públicas da página HTML estática da B3 (`www.b3.com.br/pt_br/regulacao/regulacao-de-emissores/censuras-publicas/`) utilizando BeautifulSoup.

#### Scenario: Extração de censuras com ticker no título
- **WHEN** a página de censuras contém um bloco com título "FII TORDE EI (TORD)"
- **THEN** o sistema DEVE extrair o ticker "TORD" do título via regex
- **AND** DEVE extrair a data no formato DD/MM/AAAA
- **AND** DEVE extrair o conteúdo descritivo da infração

#### Scenario: Título sem ticker entre parênteses
- **WHEN** o título de uma censura não contém padrão `(TICKER)`
- **THEN** o campo `ticker` DEVE ser `None` e os demais campos DEVEM ser extraídos normalmente

#### Scenario: Página fora do ar retorna erro tratado
- **WHEN** a requisição HTTP à página de censuras falha
- **THEN** o sistema DEVE lançar exceção com mensagem descritiva, sem crash silencioso

### Requirement: Extração de Condições Excepcionais via parsing de tabela HTML
O sistema DEVE extrair a tabela de Condições Excepcionais da página HTML estática da B3 (`www.b3.com.br/pt_br/regulacao/regulacao-de-emissores/condicoes-excepcionais/`), mapeando colunas para os campos da entidade `CondicaoExcepcional`.

#### Scenario: Extração de tabela completa com 5 colunas
- **WHEN** a página contém uma tabela com colunas Companhia, Segmento, Condição Excepcional, Data da Concessão, Prazo
- **THEN** o sistema DEVE extrair cada linha como uma `CondicaoExcepcional` com os campos correspondentes

#### Scenario: Linha com colunas faltantes
- **WHEN** uma linha da tabela tem menos de 5 colunas
- **THEN** o sistema DEVE pular a linha e registrar warning no log

### Requirement: Cache de regulação B3 com TTL de 7 dias
As extrações de Censuras Públicas e Condições Excepcionais DEVEM ser cacheadas via `CacheManager` com TTL de 7 dias, já que esses dados mudam esporadicamente.

#### Scenario: Cache de censuras evita nova requisição HTTP
- **WHEN** `listar_censuras()` é chamado duas vezes em menos de 7 dias
- **THEN** a segunda chamada DEVE retornar do cache sem nova requisição HTTP

#### Scenario: Cache de condições excepcionais expira após 7 dias
- **WHEN** `listar_condicoes_excepcionais()` é chamado mais de 7 dias após a primeira consulta
- **THEN** o sistema DEVE fazer nova requisição HTTP à página

### Requirement: Parsing com funções puras em structured_parser.py
As funções de extração de HTML regulatório DEVEM ser implementadas como funções puras em `infrastructure/b3/structured_parser.py`, seguindo o padrão de parsing encadeado do projeto. As funções DEVEM ser: `extrair_censuras(html: str) -> list[CensuraPublica]` e `extrair_condicoes_excepcionais(html: str) -> list[CondicaoExcepcional]`.

#### Scenario: Função pura recebe HTML e retorna entidades
- **WHEN** `extrair_censuras(html_string)` é chamado com HTML válido
- **THEN** a função DEVE retornar uma lista de `CensuraPublica` sem efeitos colaterais

#### Scenario: HTML sem dados retorna lista vazia
- **WHEN** `extrair_censuras("<html><body></body></html>")` é chamado
- **THEN** a função DEVE retornar `[]` sem lançar exceção
