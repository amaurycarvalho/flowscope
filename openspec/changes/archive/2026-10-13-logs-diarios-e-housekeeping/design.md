## Context

Ver `proposal.md` — Why. Os pontos do estado atual que moldam a solução:

- `_configure_logging()` (`presentation/main.py:178`) instala hoje um único
  `RotatingFileHandler(maxBytes=1_000_000, backupCount=3)` sobre
  `~/.flowscope/logs/flowscope.log`, mais handlers de plataforma (syslog/Event
  Log), com `_CommunicationAwareFormatter`.
- O caminho do log é neutro e centralizado em `flowscope/log_paths.py`
  (`log_file_path()`), importável por todas as camadas.
- O processo filho da extração (`application/extracao_orcada.py:_configurar_log_pypdf`)
  grava `ERROR`+ do `pypdf` com um `FileHandler` simples em
  `log_file_path()`, sem herdar a configuração do processo principal.
- As preferências da GUI vivem em `~/.flowscope/config.json`, gravado em
  *read-modify-write* preservando blocos alheios (`app.py`,
  `infrastructure/llm/config.py`).
- A extração devolve `StatusExtracao`
  (`OK`/`PARCIAL`/`SEM_TEXTO`/`FALHA`/`PROTEGIDO`) e as duas sub-abas convergem
  para `DocumentFlowMixin.preparar_texto()`, que só converte em *cache miss*;
  "Notícias" sobrescreve `_texto_do_arquivo`.

## Goals / Non-Goals

**Goals:**
- Um arquivo por dia: ativo `flowscope.log` + backups datados, com rolagem na
  virada e no reinício após a virada.
- Housekeeping por idade na inicialização da GUI, com retenção configurável
  (`log_retention_days`, padrão 7) mantendo hoje + 7 anteriores.
- Botão "Abrir log" abre o diretório de logs.
- `WARNING` curto para documento parcial/sem texto nas duas sub-abas.

**Non-Goals:**
- Controle de retenção na interface; formatos/níveis de log inalterados.
- Rotação dos handlers de plataforma (syslog/Event Log).
- Apagar arquivos de log que não sigam o padrão datado (ex.: antigos `.1/.2/.3`
  do `RotatingFileHandler`).
- Deduplicação dos avisos de parcial entre reprocessamentos.
- Alterar a classificação de `StatusExtracao` ou o silenciamento do `pypdf`.

## Decisions

### 1. `TimedRotatingFileHandler` + pré-passo de rolagem na inicialização

Usar `TimedRotatingFileHandler(when="midnight", interval=1, backupCount=0,
encoding="utf-8")`. O `backupCount=0` desliga a exclusão por contagem do handler;
a retenção passa a ter uma única fonte de verdade (o housekeeping da
inicialização). Como o handler calcula a rolagem a partir do instante de
construção, e não da idade do arquivo, `_configure_logging()` executa antes de
criar o handler:

1. `mkdir` do diretório de logs.
2. Se `flowscope.log` existir com data de modificação anterior a hoje, renomeá-lo
   para `flowscope-YYYY-MM-DD.log` (data da modificação). Se o destino já existir,
   concatenar o conteúdo ao destino e remover o ativo (evita perda de registros).
3. Apagar backups datados com data anterior a `hoje - N`.
4. Construir o handler diário.

*Alternativas:* subclasse de `TimedRotatingFileHandler` que chama `doRollover()`
no `__init__` (rejeitada — mais código de handler, mesmo ganho); confiar no
`backupCount` do handler (rejeitada — exclui na rotação por contagem, não por
idade, e não na inicialização).

### 2. Arquivo ativo mantido, arquivados datados

O arquivo ativo permanece `flowscope.log`; a rotação gera
`flowscope-YYYY-MM-DD.log` (data local no formato `%Y-%m-%d`). Como o
`TimedRotatingFileHandler` nomeia o arquivo rotacionado como
`flowscope.log.YYYY-MM-DD`, o handler recebe um `namer`
(`renomear_backup`) que reescreve esse nome padrão para o formato datado. Isso
mantém o processo filho do `pypdf` inalterado, pois ele sempre abre o caminho
fixo `log_file_path()` — que resolve para o arquivo ativo.

*Alternativa:* datar o arquivo ativo (`flowscope-YYYY-MM-DD.log`), rejeitada por
exigir que o filho calcule a data e por não trazer benefício ao usuário.

### 3. Retenção configurável em módulo neutro de infraestrutura

`~/.flowscope/config.json` ganha a chave de topo `log_retention_days` (padrão 7).
A leitura/validação vive em `src/flowscope/infrastructure/logging/` (leitor +
rotina de limpeza), importável pela apresentação. `_configure_logging()` roda
antes de a GUI carregar as preferências, então o valor é lido diretamente do
arquivo. A limpeza roda só no modo GUI, pois é lá que o logging é configurado.

*Alternativas:* constante em `log_paths.py` (rejeitada — não parametrizável);
adicionar a `DEFAULT_CONFIG` da GUI (rejeitada — `main.py` leria antes da GUI,
acoplando apresentação de setup e de janela).

Critério de exclusão: data embutida no **nome** do arquivo arquivado
(`flowscope-YYYY-MM-DD.log`), não `mtime` — casa com "um arquivo por dia" e o
pré-passo já data o arquivo por `mtime`. Arquivos fora do padrão são ignorados.
O ativo nunca é apagado; falhas de `OSError` (ex.: arquivo em uso) são toleradas
sem interromper a inicialização.

### 4. Botão abre o diretório de logs

Adicionar `log_dir()` a `log_paths.py` (mantendo `log_file_path()` para o filho
do `pypdf`). `_abrir_log_flowscope` verifica a existência do **diretório** e o
abre com `abrir_no_aplicativo` (que já funciona para diretórios nos três SOs).
O rótulo/tooltip do `about_panel.py` e a mensagem de erro técnico do
`presenter.py` passam a apontar para `~/.flowscope/logs`.

### 5. Warnings no seam compartilhado das sub-abas

Registrar em `DocumentFlowMixin.preparar_texto()`, imediatamente após
`_texto_do_arquivo()` e somente no *cache miss*:

- `PARCIAL` → `logger.warning("Extração parcial (%d página(s) com falha): %s/%s", resultado.paginas_com_falha, arquivo.ticker, arquivo.nome)`
- `SEM_TEXTO` → `logger.warning("Documento sem texto extraível: %s/%s", arquivo.ticker, arquivo.nome)`

Esse método é o ponto único das duas sub-abas, tanto na pré-visualização quanto
no lote, e tem a identidade do documento (`ticker`/`nome`). Como o nível padrão é
`WARNING`, os registros são gravados. `FALHA`/`PROTEGIDO` ficam de fora (o
`FALHA` já registra traceback na extração). Sem deduplicação: `SEM_TEXTO` é
cacheado e avisa uma vez; `PARCIAL` não é cacheado e pode avisar a cada
reprocessamento (aceito).

*Alternativas:* `application/document_preview.py` (rejeitada — cobriria
chamadores fora das sub-abas e o identificador útil não está ali);
`resumos_job` (rejeitada — não cobre a pré-visualização).

## Risks / Trade-offs

- **Escritas concorrentes no mesmo arquivo** (filho com `FileHandler` simples +
  pai com `TimedRotatingFileHandler`) → corrida de rotação é improvável (meia-noite
  e filho efêmero); o filho sempre reabre o caminho ativo. Aceito.
- **Limpeza/rotação em Windows com arquivo aberto** → `OSError` é capturado e a
  inicialização prossegue; a limpeza tenta novamente na próxima execução.
- **Backups antigos `.1/.2/.3` do `RotatingFileHandler`** e arquivos no formato
  intermediário `flowscope.log.YYYY-MM-DD` não seguem o padrão datado adotado
  (`flowscope-YYYY-MM-DD.log`) e não são limpos automaticamente → permanecem;
  documentado como migração manual opcional.
- **Arquivo ativo sem data no nome** pode confundir qual é "o de hoje" → arquivos
  arquivados datados e tooltip/rótulo da pasta mitigam.
- **Testes existentes** que mockam `RotatingFileHandler`/`log_file_path` e o
  texto da mensagem técnica precisam ser atualizados → incluído no plano de
  tarefas.

## Migration Plan

Sem migração de dados. Na primeira execução, se o `flowscope.log` existente for
de um dia anterior, ele é rotacionado para a data da última modificação; caso
contrário, permanece. Rollback: reverter para o handler de arquivo único; os
backups datados continuam legíveis e podem ser removidos manualmente.
