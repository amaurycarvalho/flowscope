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

### Requirement: Arquivos de log diários

O sistema DEVE organizar o log da aplicação em arquivos diários. O arquivo ativo
`~/.flowscope/logs/flowscope.log` DEVE reunir os registros do dia local corrente
e, na virada da meia-noite, DEVE ser rotacionado para
`~/.flowscope/logs/flowscope-YYYY-MM-DD.log`, correspondente ao dia encerrado, e
um novo arquivo ativo DEVE ser aberto para os registros seguintes. A data usada
na rotação DEVE ser a data local.

#### Scenario: Virada de meia-noite rotaciona o arquivo

- **WHEN** a aplicação está em execução e a data local muda para o dia seguinte
- **THEN** o `flowscope.log` do dia encerrado DEVE ser renomeado para `flowscope-YYYY-MM-DD.log`
- **AND** um novo `flowscope.log` DEVE passar a receber os registros do novo dia

#### Scenario: Registros do mesmo dia no mesmo arquivo

- **WHEN** vários registros são emitidos no mesmo dia local, em uma ou mais execuções com o app aberto
- **THEN** todos DEVEM ser gravados no mesmo arquivo diário, sem serem misturados com os de outros dias

### Requirement: Rolagem de arquivo obsoleto na inicialização

Na inicialização, se o arquivo ativo `flowscope.log` tiver data de modificação
anterior ao dia local corrente, o sistema DEVE renomeá-lo para
`flowscope-YYYY-MM-DD.log`, usando a data da última modificação, antes de abrir o
handler de log, de modo que dias distintos não compartilhem o mesmo arquivo.
Quando o arquivo ativo não existir ou já pertencer ao dia corrente, nenhuma
rotação DEVE ocorrer.

#### Scenario: App reaberto em outro dia

- **WHEN** a aplicação é iniciada e o `flowscope.log` ativo foi modificado pela última vez em um dia anterior
- **THEN** o arquivo DEVE ser renomeado para `flowscope-YYYY-MM-DD.log` com a data da última modificação
- **AND** os novos registros DEVEM ser gravados em um `flowscope.log` recém-aberto

#### Scenario: Reinício no mesmo dia não rotaciona

- **WHEN** a aplicação é reiniciada no mesmo dia e o `flowscope.log` ativo já pertence ao dia corrente
- **THEN** o arquivo NÃO DEVE ser renomeado
- **AND** os novos registros DEVEM continuar no mesmo arquivo ativo

### Requirement: Housekeeping de logs com retenção configurável

Na inicialização do modo gráfico, o sistema DEVE apagar os arquivos de backup
datados cuja data seja anterior a `hoje - N` dias, preservando o dia corrente e
os `N` dias anteriores. O número `N` de dias de retenção DEVE ser lido de
`~/.flowscope/config.json` na chave `log_retention_days`, cujo padrão DEVE ser
`7`; valores ausentes, não inteiros ou menores que `1` DEVEM cair no padrão. O
arquivo ativo `flowscope.log` NUNCA DEVE ser apagado, e o sistema NÃO DEVE
apagar arquivos que não sigam o padrão de backup datado
(`flowscope-YYYY-MM-DD.log`).

#### Scenario: Backups mais antigos que a retenção são apagados

- **WHEN** a aplicação inicia e existem backups datados com data anterior a hoje menos 7 dias
- **THEN** esses backups DEVEM ser apagados

#### Scenario: Backup no limite da retenção é preservado

- **WHEN** um backup datado tem exatamente `hoje - N` dias
- **THEN** ele NÃO DEVE ser apagado

#### Scenario: Retenção customizada

- **WHEN** `log_retention_days` é `3` no `config.json`
- **THEN** backups com data anterior a hoje menos 3 dias DEVEM ser apagados, e os de até 3 dias DEVEM ser mantidos

#### Scenario: Arquivo ativo é preservado

- **WHEN** a limpeza de logs é executada
- **THEN** o arquivo ativo `flowscope.log` NÃO DEVE ser apagado

#### Scenario: Retenção inválida usa o padrão

- **WHEN** `log_retention_days` está ausente, não é um inteiro ou é menor que `1`
- **THEN** o sistema DEVE usar `7` dias de retenção

### Requirement: Documentos parciais ou sem texto registrados em WARNING

Ao processar (extração de texto) um documento das sub-abas "Documentos" ou
"Notícias", o sistema DEVE registrar um `WARNING` curto quando o resultado for
parcial ou ausência de texto. Para resultado parcial (`PARCIAL`, incluindo
interrupção por orçamento com texto parcial), o aviso DEVE identificar o
documento pelo ticker e nome e informar a quantidade de páginas com falha. Para
ausência de texto (`SEM_TEXTO`), o aviso DEVE identificar o documento pelo
ticker e nome. Os avisos DEVEM seguir o formato de log da aplicação e DEVEM ser
emitidos apenas na extração efetiva (isto é, não no reuso do texto em cache).
Resultados `FALHA` e `PROTEGIDO` NÃO DEVEM gerar estes avisos.

#### Scenario: Extração parcial gera warning

- **WHEN** um documento das sub-abas é extraído com ao menos uma página falhando (estado `PARCIAL`)
- **THEN** uma linha de `WARNING` com o ticker, o nome do documento e a contagem de páginas com falha DEVE ser registrada

#### Scenario: Documento sem texto gera warning

- **WHEN** um documento das sub-abas é lido e nenhuma página produz texto (estado `SEM_TEXTO`)
- **THEN** uma linha de `WARNING` com o ticker e o nome do documento DEVE ser registrada

#### Scenario: Reuso de cache não registra aviso

- **WHEN** o texto de um documento já processado é lido do cache de texto
- **THEN** nenhum aviso de extração parcial ou sem texto DEVE ser registrado

#### Scenario: Falha e documento protegido não geram estes avisos

- **WHEN** a extração resulta em `FALHA` ou `PROTEGIDO`
- **THEN** nenhum aviso de parcial ou sem texto DEVE ser registrado por esta regra
