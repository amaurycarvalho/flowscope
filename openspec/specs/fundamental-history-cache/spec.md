# fundamental-history-cache Specification

## Purpose
Cache estruturado e histórico do resultado da análise fundamentalista por `(ticker, data)`, servindo recargas rápidas da sub-aba "Fundamentos" e habilitando consultas futuras da evolução do ticker.

## Requirements

### Requirement: Chave de cache por ticker e data

O sistema DEVE identificar cada observação pela combinação `(ticker, data)` em que a data é a data de referência solicitada na carga, e DEVE armazenar a `data_referencia` observada dentro da própria observação, sem usá-la como chave.

#### Scenario: Mesma data solicitada

- **WHEN** a análise de um ticker é executada para a data `D`
- **THEN** a observação DEVE ser registrada sob a chave `(ticker, D)`, preservando a `data_referencia` da fonte no conteúdo do registro

#### Scenario: Datas distintas do mesmo ticker

- **WHEN** o mesmo ticker é analisado para as datas `D1` e `D2`
- **THEN** o sistema DEVE manter duas observações independentes, uma por data

### Requirement: Observação estruturada versionada

O sistema DEVE persistir o resultado da análise como dado estruturado, não como valores já formatados, e DEVE registrar em cada observação a versão do schema que a produziu.

#### Scenario: Resultado persistido estruturado

- **WHEN** uma observação é gravada
- **THEN** o conteúdo DEVE conter os campos estruturados da análise (números, datas e classificação) e a versão do schema, permitindo reconstruir a linha da tabela sem reprocessar as fontes

#### Scenario: Versão gravada por observação

- **WHEN** duas observações do mesmo ticker foram produzidas por versões de schema diferentes
- **THEN** cada observação DEVE manter a sua própria versão registrada

### Requirement: Leitura read-through no pipeline de análise

O sistema DEVE consultar o cache antes de executar a aquisição de um ticker e, em caso de acerto, DEVE servir a observação sem executar o pipeline de aquisição; em caso de ausência, DEVE executar o pipeline atual e registrar o resultado quando aplicável.

#### Scenario: Acerto evita aquisição

- **WHEN** existe observação para `(ticker, data)` compatível com o schema atual
- **THEN** o sistema DEVE usar a observação armazenada sem consultar Fundamentus, B3, CVM, FFO ou preço

#### Scenario: Ausência executa e registra

- **WHEN** não existe observação compatível para `(ticker, data)`
- **THEN** o sistema DEVE executar a análise normalmente e registrar a observação resultante

### Requirement: Retenção de 365 dias

O sistema DEVE reter observações por 365 dias, descartando as mais antigas que esse limite e ignorando observações expiradas na leitura.

#### Scenario: Observação dentro do limite

- **WHEN** uma observação tem data dentro dos últimos 365 dias
- **THEN** ela DEVE permanecer recuperável

#### Scenario: Observação expirada

- **WHEN** uma observação tem data anterior ao limite de 365 dias
- **THEN** o sistema DEVE descartá-la ao gravar novas observações e NÃO DEVE servi-la na leitura

### Requirement: Política de falhas e dados parciais

O sistema NÃO DEVE registrar observações que representem falha total da análise. Observações parciais (sem a identidade do Fundamentus) DEVEM poder ser substituídas por uma computação melhor no mesmo dia, enquanto observações completas DEVEM permanecer imutáveis dentro do mesmo dia.

#### Scenario: Falha total não é registrada

- **WHEN** a análise de um ticker termina com erro
- **THEN** nenhuma observação DEVE ser gravada para aquela `(ticker, data)`

#### Scenario: Parcial sobrescrita no mesmo dia

- **WHEN** já existe uma observação parcial para `(ticker, data)` e uma nova computação produz uma observação com a identidade do Fundamentus
- **THEN** a observação parcial DEVE ser substituída pela nova

#### Scenario: Completa imutável no mesmo dia

- **WHEN** já existe uma observação completa para `(ticker, data)`
- **THEN** o sistema NÃO DEVE substituí-la, exceto por bypass explícito

### Requirement: Versionamento com histórico tolerante

O sistema DEVE exigir a versão de schema atual para servir um acerto do dia e DEVE servir observações de versões anteriores em consultas de histórico de forma tolerante, identificando a versão de cada observação.

#### Scenario: Acerto do dia exige versão atual

- **WHEN** existe observação para `(ticker, data)` produzida por versão de schema anterior à atual
- **THEN** o sistema NÃO DEVE tratá-la como acerto do dia e DEVE recomputar a análise

#### Scenario: Histórico tolerante a versões antigas

- **WHEN** uma consulta de histórico abrange observações de versões de schema anteriores
- **THEN** o sistema DEVE devolvê-las, preservando os campos disponíveis e identificando a versão de cada uma

### Requirement: Recuperação histórica

O sistema DEVE expor a recuperação das observações de forma que consumidores possam obter uma data específica, listar as datas disponíveis de um ticker e recuperar um intervalo de datas, sem reprocessar as fontes.

#### Scenario: Obter uma data específica

- **WHEN** o consumidor solicita `(ticker, data)` existente
- **THEN** o sistema DEVE devolver a observação correspondente

#### Scenario: Listar datas disponíveis

- **WHEN** o consumidor solicita as datas de um ticker
- **THEN** o sistema DEVE devolver as datas com observação retida, em ordem

#### Scenario: Recuperar intervalo

- **WHEN** o consumidor solicita um intervalo de datas de um ticker
- **THEN** o sistema DEVE devolver as observações contidas no intervalo, sem consultar as fontes

### Requirement: Persistência atômica e tolerância a corrupção

O sistema DEVE gravar as observações de forma atômica e DEVE tratar armazenamento ausente ou corrompido como ausência de observação, refazendo a análise.

#### Scenario: Escrita atômica

- **WHEN** uma observação é gravada
- **THEN** o sistema DEVE escrever em arquivo temporário e renomeá-lo para o destino

#### Scenario: Armazenamento corrompido

- **WHEN** o armazenamento de um ticker não puder ser interpretado
- **THEN** o sistema DEVE tratá-lo como ausência de observações e recomputar a análise

### Requirement: Bypass explícito do cache

O sistema DEVE oferecer um caminho explícito para ignorar o cache e forçar a recomputação, sobrescrevendo a observação do mesmo dia mesmo quando ela for completa.

#### Scenario: Forçar recomputação no mesmo dia

- **WHEN** o usuário solicita o bypass do cache para `(ticker, data)`
- **THEN** o sistema DEVE executar a análise e substituir a observação existente daquele dia
