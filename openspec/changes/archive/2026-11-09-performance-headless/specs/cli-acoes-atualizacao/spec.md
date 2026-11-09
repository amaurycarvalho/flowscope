# Spec Delta

## ADDED Requirements

### Requirement: Atualizar a Performance da watchlist

O sistema DEVE aceitar `flowscope atualizar performance [--data <AAAA-MM-DD>]` e calcular a Performance da watchlist carregada (`last_tickers`) para a data informada, sem interface gráfica. Sem `--data`, DEVE usar a data local de hoje. O comando DEVE resolver a data pelo calendário, usar a configuração headless padrão e gravar o cache e o snapshot, imprimindo JSON com data resolvida, tickers e benchmarks.

#### Scenario: Atualização com watchlist carregada

- **WHEN** existe `last_tickers` e o usuário executa `flowscope atualizar performance --data 2026-11-07`
- **THEN** a Performance DEVE ser calculada para os benchmarks elegíveis, o cache e o snapshot DEVEM ser gravados e o JSON DEVE informar a data resolvida e os benchmarks

#### Scenario: Sem `--data` usa a data de hoje

- **WHEN** existe `last_tickers` e o usuário executa `flowscope atualizar performance` sem `--data`
- **THEN** o cálculo DEVE usar a data local de hoje resolvida pelo calendário

#### Scenario: Sem watchlist carregada

- **WHEN** o usuário executa `flowscope atualizar performance` sem `last_tickers`
- **THEN** o comando DEVE falhar com erro estruturado, sem calcular nem gravar snapshot

#### Scenario: Data em dia não útil

- **WHEN** a data informada não é um dia útil
- **THEN** o cálculo DEVE usar a data de referência resolvida pelo calendário, sem tratar a ausência de negociação como erro

### Requirement: Desfechos da atualização de Performance

A atualização de Performance DEVE distinguir falhas duras de falhas recuperáveis. Falta de watchlist, data inválida ou indisponibilidade do lock DEVEM abortar com erro estruturado e código de saída 1. Índice indisponível, nenhum benchmark elegível ou falha isolada de um benchmark NÃO DEVEM abortar os demais; o resultado DEVE registrar o desfecho e o processo DEVE concluir com sucesso, deixando o snapshot utilizável.

#### Scenario: Falha recuperável de índice

- **WHEN** a série de um índice não pode ser obtida e os demais benchmarks são calculáveis
- **THEN** o comando DEVE concluir com os demais resultados, registrar o benchmark indisponível e não abortar o snapshot

#### Scenario: Nenhum ticker elegível

- **WHEN** a watchlist não tem FII nem ação
- **THEN** o comando DEVE concluir com sucesso, gravar o snapshot com a configuração e registrar que não houve benchmark elegível

#### Scenario: Falha ao gravar o snapshot

- **WHEN** a gravação do snapshot falha por erro de I/O
- **THEN** o comando DEVE registrar `WARNING` com contexto e informar o desfecho, mantendo o resultado em memória e sem derrubar os demais benchmarks

#### Scenario: Lock indisponível

- **WHEN** outra operação de escrita mantém o lock global além de `--esperar`
- **THEN** o comando DEVE falhar com erro estruturado `operacao_em_andamento` e código de saída 1
