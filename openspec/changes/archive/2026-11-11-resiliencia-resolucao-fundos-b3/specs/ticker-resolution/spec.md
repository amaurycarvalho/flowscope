# Spec Delta — ticker-resolution

## MODIFIED Requirements

### Requirement: Cache de resolução de ticker
O sistema DEVE cachear o resultado positivo da resolução ticker → idFNET utilizando `CacheManager.get_or_fetch` com TTL de 30 dias e chave versionada no formato `fund_resolution_{ticker}`. Resultado negativo NÃO DEVE ser cacheado, para não congelar falhas transitórias.

#### Scenario: Cache hit para ticker já resolvido
- **WHEN** o ticker `ALZR11` foi resolvido há menos de 30 dias
- **THEN** o sistema DEVE retornar o idFNET do cache sem realizar requisição HTTP

#### Scenario: Resultado negativo não é cacheado
- **WHEN** um ticker não é encontrado na B3
- **THEN** o sistema DEVE retornar ausência sem gravar a ausência no cache, permitindo nova tentativa em execução futura

#### Scenario: Cache hit para ticker não-fundo
- **WHEN** `PETR4` foi consultado há menos de 30 dias e retornou `None`
- **THEN** o sistema NÃO DEVE reutilizar a ausência do cache e DEVE consultar a B3 novamente

#### Scenario: Versão anterior da chave é ignorada
- **WHEN** existe um registro de resolução gravado por versão anterior da aquisição
- **THEN** o sistema DEVE tratá-lo como ausente e resolver o ticker novamente

## ADDED Requirements

### Requirement: Fallback da identidade persistida quando a B3 está indisponível

O sistema DEVE consultar a identidade persistida ticker → idFNET → CNPJ quando a resolução na B3 falhar ou a listagem de fundos vier incompleta, retornando a identidade armazenada sem lançar exceção.

#### Scenario: B3 indisponível usa identidade persistida
- **WHEN** a consulta à B3 falha por indisponibilidade e existe identidade persistida para o ticker
- **THEN** o sistema DEVE retornar o `idFNET` e o CNPJ armazenados

#### Scenario: Listagem incompleta usa identidade persistida
- **WHEN** a listagem de fundos não pôde ser concluída e existe identidade persistida para o ticker
- **THEN** o sistema DEVE retornar a identidade armazenada em vez de tratar o ticker como ausente

#### Scenario: Sem identidade persistida, indisponibilidade vira ausência tolerada
- **WHEN** a B3 está indisponível e não existe identidade persistida para o ticker
- **THEN** o sistema DEVE retornar ausência sem lançar exceção, mantendo o pipeline sem dados dessa fonte

#### Scenario: Identidade persistida alimenta o CNPJ fiscal
- **WHEN** a identidade é servida do registro persistido com CNPJ
- **THEN** o CNPJ DEVE ficar disponível para a resolução fiscal, permitindo o fallback CVM Anual mesmo com a B3 indisponível

### Requirement: Listagem completa prevalece sobre identidade persistida

O sistema NÃO DEVE usar a identidade persistida quando a listagem completa da B3 for obtida com sucesso e não contiver o ticker, para não mascarar fundos removidos ou tickers inválidos.

#### Scenario: Ticker ausente em listagem completa
- **WHEN** a B3 fornece uma listagem completa e o ticker não está presente, embora exista identidade persistida antiga
- **THEN** o sistema DEVE tratar o ticker como ausente e não usar a identidade antiga
