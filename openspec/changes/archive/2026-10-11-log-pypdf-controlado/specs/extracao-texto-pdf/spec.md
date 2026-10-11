## ADDED Requirements

### Requirement: Ruído de log da biblioteca não vaza do processo de extração

A extração de PDF DEVE aplicar o controle de log da biblioteca (`logging`)
tanto no processo corrente quanto no processo separado do orçamento de tempo.
Como o worker separado não herda a configuração de logging do processo
principal, ele DEVE configurar o logger `pypdf` por conta própria: suprimir
`WARNING`/`INFO`/`DEBUG` e gravar `ERROR` ou acima no arquivo de log da
aplicação, sem escrever no `stderr`/console.

#### Scenario: PDF malformado não inunda o terminal

- **WHEN** o worker separado da extração lê um PDF cujo `xref` é inválido e o `pypdf` emite avisos de autorreparo
- **THEN** o worker NÃO DEVE escrever esses avisos no `stderr`/console herdado

#### Scenario: Erro da biblioteca fica auditável

- **WHEN** o `pypdf` emite um `ERROR` no worker separado da extração
- **THEN** o registro DEVE ser gravado no arquivo de log da aplicação, preservando a auditoria

#### Scenario: Extração normal inalterada

- **WHEN** um PDF legível é extraído
- **THEN** o resultado da extração e o tempo de processamento DEVEM permanecer inalterados pelo controle de log
