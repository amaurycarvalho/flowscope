# cli-audit-logging Specification

## Purpose

Registrar cada invocação da linha de comando do FlowScope no log da aplicação, de modo que um agendador externo (cron, systemd, CI) possa auditar o que foi executado, quando e com qual desfecho, sem comprometer o contrato de saída de cada comando.

## Requirements

### Requirement: Auditoria de toda invocação da CLI

O sistema DEVE registrar no log da aplicação um registro por invocação da linha de comando, contendo ao menos o comando acionado, os argumentos permitidos, os instantes de início e de término, a duração e o código de saída. O registro DEVE reusar o formato e a rotação diária do log da aplicação. A auditoria NÃO DEVE escrever no `stdout` do processo, que permanece reservado ao contrato de cada comando (JSON das ações e JSON-RPC do servidor MCP). O registro NÃO DEVE conter segredos, como chaves de API.

#### Scenario: Invocação bem-sucedida registrada

- **WHEN** qualquer subcomando da CLI é executado com sucesso
- **THEN** um registro de auditoria DEVE ser gravado no log com o comando, os argumentos permitidos, a duração e o código de saída zero
- **AND** o `stdout` DEVE conter apenas a saída do contrato daquele comando

#### Scenario: Invocação com falha registrada

- **WHEN** um subcomando da CLI encerra com erro
- **THEN** o registro de auditoria DEVE ser gravado com o código de saída diferente de zero

#### Scenario: Segredos omitidos

- **WHEN** os argumentos ou a configuração do usuário contêm um segredo, como uma chave de API
- **THEN** o registro de auditoria NÃO DEVE conter esse valor

#### Scenario: Canal `stdout` preservado no modo MCP

- **WHEN** o subcomando `mcp` é iniciado
- **THEN** nenhum registro de auditoria DEVE aparecer no `stdout` e o canal JSON-RPC DEVE permanecer íntegro
