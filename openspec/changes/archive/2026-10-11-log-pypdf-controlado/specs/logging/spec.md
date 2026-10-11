## ADDED Requirements

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
