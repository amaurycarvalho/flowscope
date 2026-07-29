## ADDED Requirements

### Requirement: Listagem de notícias do Plantão B3 por período
O sistema DEVE consultar o endpoint `PlantaoNoticias/Noticias/ListarTitulosNoticias` da B3, suportando filtros de agência, palavra-chave e intervalo de datas.

#### Scenario: Listagem de notícias dos últimos 3 dias
- **WHEN** `listar_noticias(agencia="18", data_inicio="2026-07-27", data_fim="2026-07-29")` é chamado
- **THEN** o sistema DEVE retornar uma lista de notícias publicadas no período
- **AND** cada notícia DEVE conter título, data de publicação e URL

#### Scenario: Listagem com filtro de palavra-chave
- **WHEN** `listar_noticias(agencia="18", data_inicio="2026-01-01", data_fim="2026-12-31", palavra="PETROBRAS")` é chamado
- **THEN** o sistema DEVE retornar apenas notícias cujo título ou conteúdo contenha o termo

#### Scenario: Sem notícias no período retorna lista vazia
- **WHEN** uma consulta não encontra notícias no período
- **THEN** o sistema DEVE retornar uma lista vazia sem lançar exceção

### Requirement: Conversão para entidade NoticiaB3
Os resultados da API de notícias DEVEM ser convertidos para entidades `NoticiaB3` de domínio com os campos `titulo`, `data_publicacao`, `url` e `agencia`.

#### Scenario: JSON da API mapeado para NoticiaB3
- **WHEN** a API retorna uma notícia com título, data e link
- **THEN** o sistema DEVE instanciar `NoticiaB3(titulo=..., data_publicacao=..., url=..., agencia="18")`

### Requirement: Cache de notícias com TTL de 1 hora
As listagens de notícias DEVEM ser cacheadas via `CacheManager` com TTL de 1 hora, usando chave composta por `agencia`, `data_inicio`, `data_fim` e `palavra`.

#### Scenario: Segunda consulta em menos de 1 hora retorna do cache
- **WHEN** `listar_noticias(...)` é chamado duas vezes em menos de 1 hora com os mesmos parâmetros
- **THEN** a segunda chamada DEVE retornar do cache sem nova requisição HTTP

#### Scenario: Consulta após 1 hora busca dados frescos
- **WHEN** `listar_noticias(...)` é chamado mais de 1 hora após a primeira consulta
- **THEN** o sistema DEVE fazer nova requisição HTTP à API

### Requirement: Notícias não requerem resolução de ticker
A consulta de notícias do Plantão B3 é global (mercado) e NÃO DEVE exigir resolução de ticker ou codeCVM. O parâmetro `agencia` default é "18" (B3).

#### Scenario: Chamada sem ticker funciona
- **WHEN** `listar_noticias(data_inicio="2026-07-01", data_fim="2026-07-31")` é chamado sem informar ticker
- **THEN** o sistema DEVE consultar a API sem erro
