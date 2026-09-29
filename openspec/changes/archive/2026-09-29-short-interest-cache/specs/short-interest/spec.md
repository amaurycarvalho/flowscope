## ADDED Requirements

### Requirement: Cache de ações alugadas e publicação da B3

O sistema NÃO DEVE tratar um mapa vazio de ações alugadas como resultado definitivo: quando a B3 ainda não publicou as Posições em Aberto de uma data, o dia DEVE ser reconsultado em leituras posteriores e um mapa vazio NÃO DEVE ser persistido como cache definitivo. Um cache vazio já existente DEVE ser ignorado em favor de uma nova consulta. Ao inicializar a fonte, caches vazios legados DEVEM ser descartados. A ausência real do ticker nas posições publicadas DEVE permanecer `N/A`/`Inexistente` e NÃO DEVE ser confundida com dados ainda não publicados.

#### Scenario: Data ainda não publicada não é fixada como vazia

- **WHEN** uma data é consultada antes de a B3 publicar suas Posições em Aberto e a leitura retorna vazio
- **THEN** esse resultado vazio NÃO DEVE ser persistido como definitivo e uma leitura posterior, após a publicação, DEVE retornar as ações alugadas do ticker

#### Scenario: Cache vazio é reconsultado

- **WHEN** existe um cache vazio para a data e a B3 já publicou os dados
- **THEN** a leitura DEVE reconsultar a fonte e retornar as ações alugadas publicadas

#### Scenario: Cache vazio legado é descartado na inicialização

- **WHEN** a fonte é inicializada com caches vazios gravados anteriormente
- **THEN** esses caches vazios DEVEM ser descartados para permitir a recoleta

#### Scenario: Ticker ausente permanece indisponível

- **WHEN** o ticker não consta nas posições publicadas para as datas da janela
- **THEN** as métricas numéricas DEVEM permanecer `N/A` e as classificações `Inexistente`
