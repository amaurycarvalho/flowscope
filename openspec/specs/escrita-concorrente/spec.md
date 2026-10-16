# escrita-concorrente Specification

## Purpose

Garantir que escritas no cache local sejam seguras quando a CLI e a GUI, ou múltiplas execuções da CLI, acessam os mesmos arquivos ao mesmo tempo, sem corromper arquivos nem perder gravações.

## Requirements

### Requirement: Escrita atômica segura entre processos

Toda gravação atômica do cache DEVE usar um arquivo temporário com nome único por escrita e DEVE promover o destino com substituição atômica que sobrescreve o arquivo existente. O nome do temporário NÃO DEVE ser compartilhado entre escritas concorrentes do mesmo arquivo.

#### Scenario: Escritas concorrentes do mesmo arquivo

- **WHEN** dois processos gravam o mesmo arquivo de cache ao mesmo tempo
- **THEN** cada um DEVE usar um temporário distinto e o destino final DEVE conter uma das versões completas, sem conteúdo parcial e sem falha por temporário ausente

#### Scenario: Sobrescrita de arquivo existente

- **WHEN** uma gravação atômica substitui um arquivo de cache existente
- **THEN** a substituição DEVE sobrescrever o destino, preservando o comportamento em todos os sistemas operacionais suportados

### Requirement: Lock global de ação na CLI

Cada subcomando CLI que escreve no cache DEVE adquirir um lock global de ação antes de iniciar e liberá-lo ao terminar. O lock DEVE ser baseado em bloqueio de arquivo do sistema operacional, de modo que seja liberado automaticamente quando o processo termina, sem locks órfãos. Quando o lock já estiver em uso, o comando DEVE respeitar a política escolhida — esperar por um tempo limitado informado por opção ou falhar rapidamente com erro estruturado `operacao_em_andamento`.

#### Scenario: Duas execuções concorrentes

- **WHEN** um subcomando de ação é executado enquanto outro mantém o lock global
- **THEN** o segundo comando DEVE aguardar conforme a opção informada ou DEVE falhar com erro estruturado `operacao_em_andamento`, sem escrever no cache

#### Scenario: Liberação após conclusão

- **WHEN** um subcomando de ação termina, com sucesso ou erro
- **THEN** o lock global DEVE ser liberado

#### Scenario: Processo encerrado abruptamente

- **WHEN** o processo que detém o lock é encerrado sem liberá-lo explicitamente
- **THEN** o sistema operacional DEVE liberar o lock e uma nova execução DEVE poder adquiri-lo

#### Scenario: Ações somente-leitura não tomam o lock

- **WHEN** um comando somente-leitura (por exemplo, `flowscope nav obter`) é executado
- **THEN** o lock global NÃO DEVE ser adquirido

### Requirement: Participação da GUI no lock de escrita

A interface gráfica DEVE participar do mesmo lock global de ação durante as fases de gravação no cache, de modo que uma ação de escrita da GUI e uma execução da CLI não gravem concorrentemente. A aquisição DEVE ocorrer nas fases de escrita, sem manter o lock durante toda a sessão da GUI.

#### Scenario: GUI e CLI não gravam ao mesmo tempo

- **WHEN** a GUI está executando uma fase de gravação no cache e uma ação da CLI tenta adquirir o lock
- **THEN** a CLI DEVE aguardar ou falhar conforme a política, e as gravações NÃO DEVEM ocorrer em paralelo

#### Scenario: GUI com sessão aberta não bloqueia leitura

- **WHEN** a GUI está aberta, mas fora de uma fase de gravação
- **THEN** o lock NÃO DEVE estar retido e ações da CLI DEVEM poder ser executadas

### Requirement: Escrita concorrente de `config.json`

As gravações de `config.json` DEVEM ser atômicas e DEVEM ocorrer sob o mesmo lock global de ação, tanto pela CLI quanto pela GUI. A gravação DEVE preservar as demais chaves do arquivo no *read-modify-write*, de modo que gravações concorrentes não percam `last_fundamentals`, `last_tickers`, `last_ticker_file` nem blocos de outros módulos, como `llm`.

#### Scenario: CLI e GUI gravam ao mesmo tempo

- **WHEN** a CLI e a GUI gravam `config.json` concorrentemente
- **THEN** as gravações DEVEM ser serializadas pelo lock global e o arquivo final DEVE conter as chaves de ambas, sem corrupção

#### Scenario: Chaves preservadas no read-modify-write

- **WHEN** uma gravação da CLI atualiza `last_fundamentals`
- **THEN** as demais chaves existentes (`last_tickers`, `llm`, preferências da GUI) DEVEM permanecer no arquivo

#### Scenario: Escrita atômica do config

- **WHEN** uma gravação de `config.json` é interrompida
- **THEN** o arquivo DEVE conter a versão anterior ou a nova completa, nunca conteúdo parcial
