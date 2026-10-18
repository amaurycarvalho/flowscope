## MODIFIED Requirements

### Requirement: Atualizar os fundamentos da watchlist carregada

O sistema DEVE aceitar `flowscope atualizar fundamentos [--data <AAAA-MM-DD>]` e atualizar os fundamentos dos tickers da watchlist carregada (`last_tickers`) para a data informada. Sem `--data`, o comando DEVE usar a data de hoje no fuso local do processo, e não a data de referência de uma carga anterior. A atualização DEVE executar a análise de mercado da data antes da análise fundamentalista, de modo a preservar Preço Típico e os fallbacks de cotação e extremos. Os resultados DEVEM ser gravados no histórico de fundamentos e o marcador da última carga DEVE ser registrado. Sem `last_tickers`, o comando DEVE falhar com erro estruturado. Quando a data não for um dia útil, a análise de mercado NÃO DEVE requisitar negociação nem tratar a ausência de dados como erro.

#### Scenario: Atualização com watchlist carregada

- **WHEN** existe `last_tickers` e o usuário executa `flowscope atualizar fundamentos --data 2026-10-14`
- **THEN** a análise de mercado e a análise fundamentalista DEVEM ser executadas para a data, o histórico DEVE ser gravado e o marcador da última carga DEVE registrar `2026-10-14`

#### Scenario: Sem `--data` usa a data de hoje

- **WHEN** existe `last_tickers` e o usuário executa `flowscope atualizar fundamentos` sem `--data`
- **THEN** a atualização DEVE usar a data local de hoje, independentemente da data de referência da última carga

#### Scenario: Data em dia não útil

- **WHEN** a data informada não é um dia útil (por exemplo, feriado)
- **THEN** a análise de mercado NÃO DEVE requisitar negociação e a ausência de dados de mercado NÃO DEVE ser tratada como erro

### Requirement: Atualizar os documentos dos tickers da watchlist

O sistema DEVE aceitar `flowscope atualizar documentos [<ticker>] [--data <AAAA-MM-DD>]` e adquirir os documentos para a data informada; sem `--data`, DEVE usar a data de hoje no fuso local do processo. Com `<ticker>`, o ticker DEVE pertencer a `last_tickers`; um ticker fora da watchlist DEVE ser recusado com erro estruturado. Sem `<ticker>`, o comando DEVE iterar a watchlist carregada (`last_tickers`) e atualizar os documentos de todos os tickers; sem `last_tickers`, DEVE falhar com erro estruturado. A aquisição DEVE reusar o comportamento da aquisição de documentos por tipo de ativo e o housekeeping de deduplicação, e o resultado DEVE distinguir, por ticker, falha de ausência de novidades.

#### Scenario: Ticker na watchlist

- **WHEN** `PETR4` está em `last_tickers` e o usuário executa `flowscope atualizar documentos PETR4`
- **THEN** os documentos de `PETR4` DEVEM ser adquiridos e deduplicados

#### Scenario: Sem `--data` usa a data de hoje

- **WHEN** o usuário executa `flowscope atualizar documentos` sem `--data`
- **THEN** os documentos DEVEM ser adquiridos para a data local de hoje

#### Scenario: Ticker fora da watchlist

- **WHEN** o ticker informado não está em `last_tickers`
- **THEN** o comando DEVE falhar com erro estruturado, sem adquirir documentos

#### Scenario: Sem ticker itera a watchlist

- **WHEN** o usuário executa `flowscope atualizar documentos` sem ticker e `last_tickers` contém vários tickers
- **THEN** os documentos de cada ticker da watchlist DEVEM ser adquiridos e o resultado DEVEM reportar o desfecho por ticker

#### Scenario: Falha parcial não aborta o lote

- **WHEN** a aquisição falha para um ticker e conclui para os demais
- **THEN** os documentos dos demais tickers DEVEM ser adquiridos, o resultado DEVE distinguir o ticker com falha dos demais e o processo DEVE encerrar com código 1

#### Scenario: Sem watchlist carregada

- **WHEN** o usuário executa `flowscope atualizar documentos` sem ticker e não há `last_tickers`
- **THEN** o comando DEVE falhar com erro estruturado, sem adquirir documentos

### Requirement: Atualizar as notícias

O sistema DEVE aceitar `flowscope atualizar noticias [--data <AAAA-MM-DD>]` e executar a aquisição incremental das notícias do Plantão B3 para a data informada; sem `--data`, DEVE usar a data de hoje no fuso local do processo. A aquisição DEVE reusar o housekeeping de deduplicação.

#### Scenario: Atualização de notícias

- **WHEN** o usuário executa `flowscope atualizar noticias`
- **THEN** a carga incremental das notícias DEVE ser executada para a data local de hoje e o resultado DEVE ser impresso em JSON

#### Scenario: Data explícita

- **WHEN** o usuário executa `flowscope atualizar noticias --data 2026-10-14`
- **THEN** a carga incremental das notícias DEVE ser executada para `2026-10-14`

### Requirement: Resumir pendentes de documentos de um ticker

O sistema DEVE aceitar `flowscope resumir documentos <ticker>` e processar os documentos pendentes do ticker — os que carecem de resumo e os Relatórios Gerenciais já resumidos pendentes de avaliação de guidance — reusando o mesmo processamento em lote da interface gráfica, incluindo a extração de texto e a avaliação de guidance. O ticker DEVE pertencer a `last_tickers`. A saída DEVE manter o formato agregado com as chaves `pendentes`, `sem_texto`, `nao_conclusivos` e `apontadores`, sem o envelope `resultados` usado no processamento de toda a watchlist.

#### Scenario: Pendentes processados

- **WHEN** o ticker tem documentos pendentes de resumo e o usuário executa `flowscope resumir documentos <ticker>`
- **THEN** os resumos DEVEM ser gerados e persistidos e os RGs pendentes DEVEM ter a avaliação de guidance registrada

#### Scenario: Sem pendentes

- **WHEN** o ticker não tem documentos pendentes
- **THEN** o comando DEVE concluir sem erro e informar zero itens processados

#### Scenario: Formato agregado preservado

- **WHEN** o usuário executa `flowscope resumir documentos PETR4` com o ticker na watchlist
- **THEN** a saída DEVE conter `pendentes`, `sem_texto`, `nao_conclusivos` e `apontadores`, e NÃO DEVE conter `resultados`

## ADDED Requirements

### Requirement: Resumir pendentes de documentos da watchlist

O sistema DEVE aceitar `flowscope resumir documentos` sem ticker e processar os documentos pendentes de todos os tickers de `last_tickers`, reusando o mesmo processamento em lote, a extração de texto e a avaliação de guidance de `flowscope resumir documentos <ticker>`. A checagem de LLM DEVE ocorrer uma única vez, antes de processar qualquer ticker. O resultado DEVE distinguir o desfecho por ticker no formato `{"resultados": {<ticker>: <desfecho>}, "falha": <bool>}`. Para um ticker concluído, `<desfecho>` DEVE conter as contagens `pendentes`, `sem_texto`, `nao_conclusivos` e `apontadores`. Para um ticker que falha, `<desfecho>` DEVE ser `{"erro": {"motivo": "falha_resumo", "detalhe": "..."}}`. A falha de um ticker NÃO DEVE abortar o lote: os demais tickers DEVEM ser processados, `falha` DEVE ser `true` e o processo DEVE encerrar com código 1. Itens não conclusivos de extração DEVEM ser reportados nas contagens e NÃO DEVEM, por si só, configurar falha do ticker. Sem `last_tickers`, o comando DEVE falhar com erro estruturado, sem resumir documentos. Sem provedor de LLM configurado, o comando DEVE falhar com erro estruturado `llm_nao_configurada` antes de processar qualquer ticker.

#### Scenario: Sem ticker itera a watchlist

- **WHEN** o usuário executa `flowscope resumir documentos` e `last_tickers` contém vários tickers
- **THEN** os documentos pendentes de cada ticker DEVEM ser processados e o resultado DEVE reportar o desfecho por ticker

#### Scenario: Formato de sucesso por ticker

- **WHEN** o usuário executa `flowscope resumir documentos` e todos os tickers concluem sem falha
- **THEN** cada valor de `resultados` DEVE conter `pendentes`, `sem_texto`, `nao_conclusivos` e `apontadores`, e `falha` DEVE ser `false`

#### Scenario: Falha parcial não aborta o lote

- **WHEN** o processamento falha para um ticker e conclui para os demais
- **THEN** os documentos dos demais tickers DEVEM ser processados, o valor do ticker com falha DEVE ser `{"erro": {"motivo": "falha_resumo", "detalhe": "..."}}`, `falha` DEVE ser `true` e o processo DEVE encerrar com código 1

#### Scenario: Sem watchlist carregada

- **WHEN** o usuário executa `flowscope resumir documentos` sem ticker e não há `last_tickers`
- **THEN** o comando DEVE falhar com erro estruturado, sem resumir documentos

#### Scenario: Sem LLM configurada

- **WHEN** o usuário executa `flowscope resumir documentos` sem ticker e nenhum provedor de LLM está configurado
- **THEN** o comando DEVE falhar com erro estruturado `llm_nao_configurada` antes de processar qualquer ticker
