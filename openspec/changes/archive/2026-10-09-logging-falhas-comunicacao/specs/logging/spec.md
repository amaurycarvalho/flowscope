## ADDED Requirements

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
