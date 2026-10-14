## Purpose

Expor as ações de atualização do FlowScope como subcomandos de linha de comando, permitindo que um agendador externo (cron, systemd, CI) mantenha os caches atualizados sem abrir a interface gráfica.

## ADDED Requirements

### Requirement: Subcomandos de ação e convenções de saída

O sistema DEVE aceitar um grupo de subcomandos de ação com a forma verbo-primeiro: `flowscope carregar ...`, `flowscope atualizar ...` e `flowscope resumir ...`. A saída padrão DEVE ser JSON estruturado em `stdout`, com a flag opcional `--pretty` formatando para leitura humana; mensagens de progresso e diagnóstico DEVEM ir para `stderr`. Erros de domínio recuperáveis DEVEM ser impressos como JSON estruturado em `stdout` e o processo DEVE encerrar com código 1. As ações de escrita NÃO DEVEM exigir interface gráfica.

#### Scenario: Saída JSON padrão

- **WHEN** qualquer subcomando de ação termina com sucesso
- **THEN** o resultado estruturado DEVE ser impresso em `stdout` como JSON, e o progresso DEVE ir para `stderr`

#### Scenario: Erro de domínio

- **WHEN** um subcomando de ação falha de forma recuperável (por exemplo, ticker fora da watchlist)
- **THEN** o erro estruturado DEVE ser impresso em `stdout` com motivo e detalhe, o diagnóstico DEVE ir para `stderr` e o processo DEVE encerrar com código 1

### Requirement: Carregar a watchlist de um arquivo

O sistema DEVE aceitar `flowscope carregar watchlist <arquivo>`, lendo um ticker por linha, normalizando com `strip().upper()` e descartando linhas vazias. O arquivo DEVE existir e conter ao menos um ticker; caso contrário, o comando DEVE falhar com erro estruturado. Em sucesso, a watchlist DEVE ser persistida em `last_tickers` e o resultado DEVE listar os tickers carregados.

#### Scenario: Arquivo válido

- **WHEN** o usuário executa `flowscope carregar watchlist tickers.txt` com um arquivo contendo tickers
- **THEN** a watchlist DEVE ser persistida em `last_tickers` e o JSON DEVE listar os tickers normalizados

#### Scenario: Arquivo inexistente ou vazio

- **WHEN** o arquivo informado não existe ou não contém nenhum ticker
- **THEN** o comando DEVE falhar com erro estruturado, sem alterar `last_tickers`

### Requirement: Atualizar os fundamentos da watchlist carregada

O sistema DEVE aceitar `flowscope atualizar fundamentos --data <AAAA-MM-DD>` e atualizar os fundamentos dos tickers da watchlist carregada (`last_tickers`) para a data de referência. A atualização DEVE executar a análise de mercado da data antes da análise fundamentalista, de modo a preservar Preço Típico e os fallbacks de cotação e extremos. Os resultados DEVEM ser gravados no histórico de fundamentos e o marcador da última carga DEVE ser registrado. Sem `last_tickers`, o comando DEVE falhar com erro estruturado.

#### Scenario: Atualização com watchlist carregada

- **WHEN** existe `last_tickers` e o usuário executa `flowscope atualizar fundamentos --data 2026-10-14`
- **THEN** a análise de mercado e a análise fundamentalista DEVEM ser executadas para a data, o histórico DEVE ser gravado e o marcador da última carga DEVE registrar `2026-10-14`

### Requirement: Atualizar os documentos de um ticker da watchlist

O sistema DEVE aceitar `flowscope atualizar documentos <ticker>` e adquirir os documentos do ticker para a data de referência. O ticker DEVE pertencer a `last_tickers`; um ticker fora da watchlist DEVE ser recusado com erro estruturado. A aquisição DEVE reusar o comportamento da aquisição de documentos por tipo de ativo e o housekeeping de deduplicação.

#### Scenario: Ticker na watchlist

- **WHEN** `PETR4` está em `last_tickers` e o usuário executa `flowscope atualizar documentos PETR4`
- **THEN** os documentos de `PETR4` DEVEM ser adquiridos e deduplicados

#### Scenario: Ticker fora da watchlist

- **WHEN** o ticker informado não está em `last_tickers`
- **THEN** o comando DEVE falhar com erro estruturado, sem adquirir documentos

### Requirement: Atualizar as notícias

O sistema DEVE aceitar `flowscope atualizar noticias` e executar a aquisição incremental das notícias do Plantão B3 para a data de referência, reusando o housekeeping de deduplicação.

#### Scenario: Atualização de notícias

- **WHEN** o usuário executa `flowscope atualizar noticias`
- **THEN** a carga incremental das notícias DEVE ser executada e o resultado DEVE ser impresso em JSON

### Requirement: Resumir pendentes de documentos de um ticker

O sistema DEVE aceitar `flowscope resumir documentos <ticker>` e processar os documentos pendentes do ticker — os que carecem de resumo e os Relatórios Gerenciais já resumidos pendentes de avaliação de guidance — reusando o mesmo processamento em lote da interface gráfica, incluindo a extração de texto e a avaliação de guidance. O ticker DEVE pertencer a `last_tickers`.

#### Scenario: Pendentes processados

- **WHEN** o ticker tem documentos pendentes de resumo e o usuário executa `flowscope resumir documentos <ticker>`
- **THEN** os resumos DEVEM ser gerados e persistidos e os RGs pendentes DEVEM ter a avaliação de guidance registrada

#### Scenario: Sem pendentes

- **WHEN** o ticker não tem documentos pendentes
- **THEN** o comando DEVE concluir sem erro e informar zero itens processados

### Requirement: Resumir pendentes de notícias

O sistema DEVE aceitar `flowscope resumir noticias` e processar as notícias pendentes de resumo em lote, reusando o mesmo processamento da interface gráfica.

#### Scenario: Notícias pendentes processadas

- **WHEN** existem notícias pendentes de resumo
- **THEN** os resumos DEVEM ser gerados e persistidos, respeitando a ordem determinística de processamento

### Requirement: Atualizar fundamentos e resumir exigem LLM configurada

As ações que dependem de LLM (`resumir`) DEVEM falhar com erro estruturado quando nenhum provedor estiver configurado, sem executar chamadas de rede.

#### Scenario: Provedor não configurado

- **WHEN** `flowscope resumir noticias` é executado sem provedor de LLM configurado
- **THEN** o comando DEVE devolver erro estruturado informando a indisponibilidade, sem gerar resumos
