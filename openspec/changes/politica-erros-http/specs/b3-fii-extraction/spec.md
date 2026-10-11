## MODIFIED Requirements

### Requirement: Retry e rate-limit na aquisição

O sistema DEVE repetir requisições que falharem por erro transitório usando a política central de status HTTP (`politica-erros-http`) — `THROTTLE`, `TRANSITORIO` e `GATEWAY` são repetidos com espera crescente; `PERMANENTE` não é repetido — e NÃO DEVE repetir automaticamente erros permanentes (HTTP 403 e demais `4xx`, além dos `5xx` permanentes). As requisições DEVEM ser serializadas por host, no máximo uma por vez, com o retry ocorrendo dentro da serialização do host.

#### Scenario: Erro transitório é repetido
- **WHEN** uma requisição falha por erro de conexão e uma tentativa seguinte tem sucesso
- **THEN** o sistema DEVE retornar a resposta bem-sucedida sem propagar a falha

#### Scenario: Erro permanente não é repetido
- **WHEN** uma requisição retorna HTTP 404
- **THEN** o sistema NÃO DEVE repetir a requisição

#### Scenario: Recurso proibido não é repetido
- **WHEN** uma requisição retorna HTTP 403
- **THEN** o sistema NÃO DEVE repetir a requisição

#### Scenario: Excesso de requisições respeita Retry-After
- **WHEN** uma requisição retorna HTTP 429 com o cabeçalho `Retry-After`
- **THEN** o sistema DEVE aguardar o tempo indicado (limitado ao teto) antes de repetir

#### Scenario: Serialização por host é preservada
- **WHEN** duas requisições ao mesmo host são acionadas
- **THEN** elas DEVEM ser executadas uma por vez, com o retry contido na serialização
