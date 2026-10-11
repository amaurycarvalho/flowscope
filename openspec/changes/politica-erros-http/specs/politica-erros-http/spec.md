## Purpose

Define uma política única de tratamento de erros HTTP por código de status e um motor de retry comum, para que todos os acessos de rede (leitura de dados e download de arquivos) reajam de forma consistente a 403, 429, 502/504 e 520–524, excluindo os probes de cache condicional e o provedor de LLM.

## ADDED Requirements

### Requirement: Classificação de status HTTP em categorias

O sistema DEVE classificar todo status de resposta HTTP em exatamente uma categoria: `PERMANENTE` (não repetir), `THROTTLE` (repetir respeitando `Retry-After`), `TRANSITORIO` (repetir com backoff crescente) ou `GATEWAY` (repetir com backoff maior). A classificação DEVE seguir: todo `4xx` é `PERMANENTE`, exceto 408 e 425 (`TRANSITORIO`) e 429 (`THROTTLE`); todo `5xx` é `TRANSITORIO`, exceto 501, 505, 506 e 511 (`PERMANENTE`); os códigos 520, 521, 522, 523 e 524 DEVEM ser `GATEWAY`; o código 503 DEVE ser `THROTTLE` quando a resposta trouxer `Retry-After` e `TRANSITORIO` caso contrário. O código 403 DEVE ser `PERMANENTE`.

#### Scenario: Recurso proibido é permanente
- **WHEN** uma resposta tem status 403
- **THEN** ela DEVE ser classificada como `PERMANENTE` e não ser repetida

#### Scenario: Excesso de requisições é throttling
- **WHEN** uma resposta tem status 429
- **THEN** ela DEVE ser classificada como `THROTTLE`

#### Scenario: Bad gateway e gateway timeout são transitórios
- **WHEN** uma resposta tem status 502 ou 504
- **THEN** ela DEVE ser classificada como `TRANSITORIO`

#### Scenario: Erros de origem atrás de Cloudflare são gateway
- **WHEN** uma resposta tem status entre 520 e 524
- **THEN** ela DEVE ser classificada como `GATEWAY`

#### Scenario: Serviço indisponível com Retry-After é throttling
- **WHEN** uma resposta tem status 503 e traz o cabeçalho `Retry-After`
- **THEN** ela DEVE ser classificada como `THROTTLE`

#### Scenario: Erro de cliente desconhecido é permanente
- **WHEN** uma resposta tem um status `4xx` não listado explicitamente
- **THEN** ela DEVE ser classificada como `PERMANENTE`

### Requirement: Motor de retry por categoria

O sistema DEVE repetir requisições classificadas como `THROTTLE`, `TRANSITORIO` ou `GATEWAY` até um número máximo de tentativas, com espera crescente entre tentativas, e NÃO DEVE repetir requisições `PERMANENTE`. Erros de rede sem resposta HTTP (ex.: falha de conexão) DEVEM ser tratados como repetíveis. O motor DEVE ser o mesmo para todos os acessos de rede, aplicado a partir de uma função central.

#### Scenario: Erro transitório é repetido
- **WHEN** uma requisição falha por erro de conexão e uma tentativa seguinte tem sucesso
- **THEN** o sistema DEVE retornar a resposta bem-sucedida sem propagar a falha

#### Scenario: Erro permanente não é repetido
- **WHEN** uma requisição retorna um status `PERMANENTE`
- **THEN** o sistema DEVE propagar o erro sem repetir

#### Scenario: Sucesso não repete
- **WHEN** uma requisição retorna status `2xx`
- **THEN** o sistema DEVE devolver a resposta sem nova tentativa

### Requirement: Respeito ao Retry-After

Quando a categoria for `THROTTLE` e a resposta trouxer o cabeçalho `Retry-After`, o sistema DEVE aguardar o tempo indicado antes da próxima tentativa, aceitando o valor em segundos e em data HTTP, limitado por um teto configurável para não bloquear indefinidamente.

#### Scenario: Retry-After em segundos
- **WHEN** uma resposta 429 traz `Retry-After: 5`
- **THEN** o sistema DEVE aguardar até 5 segundos (limitado ao teto) antes de repetir

#### Scenario: Retry-After em data HTTP
- **WHEN** uma resposta 429 traz `Retry-After` no formato de data HTTP
- **THEN** o sistema DEVE calcular a espera a partir da diferença até a data informada, limitada ao teto

#### Scenario: Retry-After acima do teto
- **WHEN** o valor de `Retry-After` excede o teto configurado
- **THEN** o sistema DEVE aguardar apenas o teto antes de repetir

### Requirement: Backoff com jitter entre tentativas

Entre tentativas repetíveis, o sistema DEVE aguardar um intervalo crescente acrescido de variação aleatória (jitter) para evitar sincronização entre acessos. As requisições classificadas como `GATEWAY` DEVEM usar uma espera base maior que as `TRANSITORIO`.

#### Scenario: Jitter aplicado
- **WHEN** uma requisição repetível falha e há nova tentativa
- **THEN** a espera DEVE incluir variação aleatória sobre o intervalo base

#### Scenario: Gateway espera mais que transitório
- **WHEN** duas requisições falham, uma com 502 e outra com 522, na mesma tentativa
- **THEN** a espera base aplicada ao 522 DEVE ser maior que a aplicada ao 502

### Requirement: Métodos repetíveis

O sistema DEVE repetir somente métodos idempotentes (GET, HEAD, OPTIONS, PUT, DELETE) e requisições POST explicitamente marcadas como leitura pelo ponto de chamada. Um POST não marcado NÃO DEVE ser repetido automaticamente.

#### Scenario: GET é repetido em erro transitório
- **WHEN** um GET falha com 502 e a tentativa seguinte sucede
- **THEN** o sistema DEVE repetir o GET

#### Scenario: POST de leitura marcado é repetido
- **WHEN** um POST marcado como leitura falha com 504 e a tentativa seguinte sucede
- **THEN** o sistema DEVE repetir o POST

#### Scenario: POST não marcado não é repetido
- **WHEN** um POST não marcado como leitura falha com 500
- **THEN** o sistema NÃO DEVE repetir o POST

### Requirement: Exceções à política comum

Os probes do cache condicional (requisições HEAD/condicionais que interpretam 304, 403 e 404 como estados de validação) NÃO DEVEM usar o motor de retry: nesses acessos, 304 indica "inalterado" e 403/404 indicam validação desconhecida, sem nova tentativa automática. O provedor de LLM NÃO DEVE adotar esta política de status; mantém a classificação própria por tipo de exceção do provedor.

#### Scenario: Probe não repete
- **WHEN** um probe condicional recebe 404 ou 403
- **THEN** ele DEVE ser interpretado como validação desconhecida, sem nova tentativa

#### Scenario: Provedor de LLM inalterado
- **WHEN** uma chamada de LLM falha por cota
- **THEN** ela DEVE continuar seguindo a classificação por exceção do provedor, não a tabela de status

### Requirement: Override por ponto de chamada

O motor DEVE permitir que um ponto de chamada declare códigos adicionais como repetíveis, para exceções documentadas em que um status normalmente permanente é intermitente naquele endpoint. O override DEVE ser explícito e local ao ponto de chamada.

#### Scenario: 404 intermitente por override
- **WHEN** um endpoint documentado responde 404 de forma intermitente e o ponto de chamada declara 404 como repetível
- **THEN** o motor DEVE repetir o 404 nesse ponto de chamada apenas

#### Scenario: Sem override, 404 não repete
- **WHEN** um ponto de chamada não declara override e a resposta é 404
- **THEN** o motor NÃO DEVE repetir

### Requirement: Espera limitada e cancelável

O motor DEVE limitar a espera total de uma sequência de tentativas e DEVE permitir que o ponto de chamada interrompa a espera quando houver um pedido de cancelamento, de modo que uma espera longa não bloqueie indefinidamente uma operação cancelável.

#### Scenario: Espera total limitada
- **WHEN** o número máximo de tentativas se esgota
- **THEN** o motor DEVE propagar a última falha sem nova espera

#### Scenario: Cancelamento interrompe a espera
- **WHEN** há um pedido de cancelamento durante a espera entre tentativas
- **THEN** o motor DEVE interromper a espera e propagar o cancelamento

### Requirement: Registo do erro classificado

Ao esgotar as tentativas ou descartar uma repetição, o sistema DEVE registrar o status e a categoria correspondentes, distinguindo falha permanente de transitória, para permitir diagnóstico sem alterar a tolerância atual a falhas.

#### Scenario: Falha permanente registrada
- **WHEN** uma requisição não é repetida por ser `PERMANENTE`
- **THEN** o registro DEVE indicar o status e a categoria permanente

#### Scenario: Falha transitória registrada
- **WHEN** uma requisição repetível esgota as tentativas
- **THEN** o registro DEVE indicar o status e a categoria transitória ou de gateway
