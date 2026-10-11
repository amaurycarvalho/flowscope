## Why

A extração de PDF passou a rodar em um processo separado (`extracao-texto-pdf`),
mas esse processo filho não configura logging. Quando o `pypdf` lê um PDF com a
tabela `xref` inválida (ex.: `AGRO3/2025/10/assembleia/1434760.pdf`, cujo
`startxref` aponta para `xref 0 0`), ele se autorrepara em modo não-estrito e
registra um `WARNING` por objeto descartado no logger `pypdf._reader`
("Ignoring wrong pointing object …"). Sem handlers, esses registros caem no
`logging.lastResort` e vão direto para o `stderr` herdado — poluindo o terminal
do `flowscope` com 1422 linhas, ainda que a extração conclua com sucesso. No
processo principal o log é configurado apenas para arquivo/syslog, então o
problema se limita ao worker. Além disso, `WARNING`/`INFO`/`DEBUG` do `pypdf`
são ruído de autorreparo; só `ERROR` merece ser preservado.

## What Changes

- **Silenciar `pypdf` abaixo de `ERROR`**: o logger `pypdf` (e seus filhos, como
  `pypdf._reader` e `pypdf._cmap`) passa a ter nível `ERROR`, suprimindo
  `WARNING`/`INFO`/`DEBUG` — tanto na configuração do app
  (`_configure_logging`) quanto no processo filho da extração.
- **`ERROR` do `pypdf` para o log do app**: no processo filho, os registros de
  `ERROR` ou acima do `pypdf` são gravados no arquivo `flowscope.log` (com o
  mesmo formato do app), permanecendo auditáveis e **sem** cair no `stderr`/console.
- **Caminho de log em módulo neutro**: o módulo de caminhos de log sai de
  `presentation` para `flowscope/log_paths.py`, permitindo que a camada de
  aplicação (o extrator) referencie o arquivo de log do app sem violar as
  fronteiras de camadas.
- **Não muda** o conteúdo dos PDFs nem o comportamento de autorreparo do
  `pypdf`: a extração continua tolerante e resiliente.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `logging`: novo requisito de controle do log de bibliotecas de terceiros
  (`pypdf`) — `WARNING`/`INFO`/`DEBUG` suprimidos; `ERROR`+ gravado no
  `flowscope.log`; nada de ruído no console.
- `extracao-texto-pdf`: o processo de extração (incluindo o worker separado)
  DEVE aplicar esse controle, de modo que um PDF malformado não polua o
  terminal e eventuais erros fiquem registrados no log do app.

## Impact

- Código: novo `src/flowscope/log_paths.py` (movido de `presentation/log_paths.py`,
  com imports atualizados em `presentation/main.py` e
  `presentation/gui/app_about_actions.py`); `presentation/main.py`
  (`_configure_logging`) silencia o `pypdf`; `application/extracao_orcada.py`
  (processo filho) silencia o `pypdf` e grava `ERROR`+ no log do app.
- Comportamento observável: o CLI deixa de ser inundado por avisos do `pypdf`;
  erros reais da biblioteca continuam registrados em `flowscope.log`.
- Sem alteração de contrato de dados, dependências ou API pública.
