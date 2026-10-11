## Purpose

Define the logging behavior of FlowScope, ensuring log records written to `flowscope.log` are consistently formatted and configured across all handlers.

## Requirements

### Requirement: Log records include timestamp

The system SHALL include a timestamp with date and time in every log record written to the `flowscope.log` file.

#### Scenario: Log record contains timestamp
- **WHEN** any log record is written to `flowscope.log`
- **THEN** the record line SHALL start with a timestamp in ISO 8601 format (YYYY-MM-DD HH:MM:SS,mmm) including milliseconds

### Requirement: Timestamp format configured globally

The timestamp format SHALL be configured via the `format`/`datefmt` arguments of `logging.basicConfig`, applying to all log handlers used by the application.

#### Scenario: Format applies to all handlers
- **WHEN** the application configures logging in `_configure_logging()`
- **THEN** the single format string defined for `logging.basicConfig` is used by the rotating file handler and any platform-specific handlers (syslog, NT Event Log)

### Requirement: Falhas de comunicação registradas sem traceback

Ao registrar uma falha de comunicação prevista e tolerada — exceção de rede/HTTP (`requests.RequestException`, direta ou encadeada como causa/contexto) — o sistema DEVE escrever uma única linha, contendo o tipo e a mensagem da exceção, e NÃO DEVE incluir o call stack completo. Exceções que não sejam de comunicação DEVEM continuar sendo registradas com o traceback completo, preservando o rastreio de defeitos inesperados.

#### Scenario: Timeout de rede não gera traceback

- **WHEN** um handler de aquisição registra uma `requests.RequestException` (por exemplo, `ReadTimeout`) com `exc_info`
- **THEN** o `flowscope.log` DEVE conter uma única linha de `WARNING` com o tipo (`ReadTimeout`) e a mensagem da falha
- **AND** a linha NÃO DEVE conter `Traceback`

#### Scenario: Causa encadeada de comunicação não gera traceback

- **WHEN** um handler registra uma exceção de domínio cuja causa/contexto é uma `requests.RequestException`
- **THEN** a linha DEVE ser registrada sem traceback, com o tipo e a mensagem da exceção encadeada

#### Scenario: Exceção inesperada mantém o traceback

- **WHEN** um handler registra uma exceção que não deriva de comunicação (ex.: erro de parsing ou `ValueError`)
- **THEN** o registro DEVE incluir o traceback completo

#### Scenario: Registro em memória preserva a exceção

- **WHEN** uma falha de comunicação é registrada
- **THEN** o objeto de `LogRecord` DEVE manter `exc_info` preenchido, de modo que testes e depuradores ainda acessem a exceção, mesmo que a renderização omita o traceback

### Requirement: Log de bibliotecas de terceiros controlado

O sistema DEVE configurar o logger da biblioteca de PDF (`pypdf`, abrangendo
seus loggers filhos, como `pypdf._reader`) com nível `ERROR`, de modo que
registros `WARNING`, `INFO` e `DEBUG` NÃO sejam emitidos — em especial os avisos
de autorreparo de PDFs malformados ("Ignoring wrong pointing object …").
Registros de `ERROR` ou acima DEVEM ser gravados no arquivo de log da aplicação
(`flowscope.log`), com o formato já usado pelos demais registros, e NÃO DEVEM
ser escritos no console (`stderr`/`stdout`).

#### Scenario: Avisos do pypdf não poluem o console

- **WHEN** um PDF com `xref` inválido é processado e o `pypdf` emite avisos de autorreparo em nível `WARNING`
- **THEN** nenhum registro do `pypdf` em `WARNING`/`INFO`/`DEBUG` DEVE ser escrito no console

#### Scenario: Erro do pypdf registrado no log do app

- **WHEN** o `pypdf` emite um registro de nível `ERROR` durante a extração
- **THEN** o registro DEVE ser gravado no arquivo `flowscope.log`, e NÃO DEVE ir para o console

#### Scenario: Formato consistente do registro

- **WHEN** um registro de `ERROR` do `pypdf` é gravado no `flowscope.log`
- **THEN** a linha DEVE seguir o mesmo formato (`timestamp | level | logger | mensagem`) dos demais registros do app
