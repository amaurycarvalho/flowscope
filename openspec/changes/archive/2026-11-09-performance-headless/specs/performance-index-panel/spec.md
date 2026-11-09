# Spec Delta

## ADDED Requirements

### Requirement: Snapshot estável dos resultados de Performance

O sistema DEVE persistir, após cada cálculo de Performance, um snapshot estável e auto-descritivo em `~/.cache/flowscope/performance/latest.json`, contendo versão de schema, origem, data de referência, período, amostragem, base de retorno, instante do cálculo e o payload por benchmark. A escrita DEVE ser atômica e a leitura DEVE tratar snapshot ausente, corrompido ou de schema divergente como ausência de resultado.

#### Scenario: Snapshot gravado após cálculo da GUI

- **WHEN** o job de Performance da GUI conclui o cálculo de um benchmark
- **THEN** o snapshot `latest.json` DEVE ser gravado com o contexto da carga e o payload calculado

#### Scenario: Snapshot gravado após atualização headless

- **WHEN** `flowscope atualizar performance` conclui o cálculo
- **THEN** o snapshot `latest.json` DEVE ser gravado com a watchlist, a data resolvida, o período e a amostragem usados

#### Scenario: Snapshot expõe o contexto do cálculo

- **WHEN** o snapshot é lido por chat, CLI ou MCP
- **THEN** ele DEVE conter `ref_date`, `period_days`, `sampling_method`, `cached_at` e a base de retorno, para que o consumidor descreva corretamente o período e a convenção

#### Scenario: Snapshot corrompido é tratado como ausência

- **WHEN** o arquivo `latest.json` não é JSON válido ou não contém um objeto de resultado
- **THEN** o sistema DEVE tratar o snapshot como ausente, registrar o problema e não falhar a navegação

#### Scenario: Schema divergente é tratado como ausência

- **WHEN** o snapshot tem versão de schema diferente da suportada
- **THEN** o sistema DEVE ignorá-lo, registrar o problema e não misturar resultados de schemas distintos

### Requirement: Cálculo headless da Performance

O sistema DEVE calcular a Performance sem interface gráfica a partir da watchlist persistida e da data de referência resolvida, usando a configuração headless padrão (30 dias, Fibonacci). O cálculo DEVE reutilizar dados de mercado e a classificação fundamentalista em cache, gravar o cache por chave e o snapshot, e isolar a falha de um benchmark sem derrubar os demais.

#### Scenario: Cálculo sem abrir a GUI

- **WHEN** a watchlist está persistida e a data de referência pode ser resolvida
- **THEN** o cálculo DEVE produzir os resultados dos benchmarks elegíveis sem exigir interface gráfica

#### Scenario: Classificação usa fundamentação e fallback

- **WHEN** a classificação fundamentalista resolve FII ou ação
- **THEN** os tickers DEVEM ser elegíveis ao benchmark correspondente; sem classificação confiável, DEVEM ficar fora com registro em log

#### Scenario: Nenhum benchmark elegível

- **WHEN** nenhum ticker da watchlist é FII ou ação
- **THEN** o cálculo DEVE concluir sem benchmarks, gravar o snapshot com a configuração e registrar o motivo

#### Scenario: Índice indisponível

- **WHEN** a série do índice de um benchmark não está disponível
- **THEN** o resultado daquele benchmark DEVE registrar `index_available` falso, sem impedir os demais benchmarks

#### Scenario: Falha de um benchmark é isolada

- **WHEN** o cálculo de um benchmark levanta uma exceção inesperada
- **THEN** os demais benchmarks DEVEM continuar e o benchmark com falha DEVE ser registrado como indisponível

### Requirement: Consistência entre GUI e headless

O sistema DEVE produzir o payload e o snapshot da Performance pela mesma regra de montagem na GUI e no headless, de modo que uma mesma configuração gere o mesmo resultado observável e o snapshot reflita o cálculo mais recente, independentemente da superfície.

#### Scenario: Mesma configuração, mesmo resultado

- **WHEN** GUI e headless calculam a Performance com a mesma data, período, amostragem, tickers e base
- **THEN** os resultados observáveis DEVEM ser equivalentes

#### Scenario: Snapshot reflete o cálculo mais recente

- **WHEN** a GUI ou o headless conclui um novo cálculo
- **THEN** o snapshot DEVE ser substituído de forma atômica pelo resultado mais recente
