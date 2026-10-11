## Context

Ver `proposal.md` — Why. O `pypdf` em modo não-estrito valida cada entrada do
`xref` e chama `logger_warning(...)` (`pypdf/_reader.py:731-751` →
`pypdf/_utils.py:487`), que usa `logging.getLogger("pypdf._reader").warning(...)`.
O processo principal configura logging só para arquivo/syslog
(`presentation/main.py:_configure_logging`), sem handler de console; o worker
separado da extração (`application/extracao_orcada.py:_extrair_pdf_filho`,
iniciado com `spawn`) não herda essa configuração, então os `WARNING` caem no
`logging.lastResort` e vão para o `stderr` herdado. Caso observado:
`AGRO3/2025/10/assembleia/1434760.pdf` (1422 avisos), extração conclui `OK`.

## Goals / Non-Goals

**Goals:**
- Suprimir `WARNING`/`INFO`/`DEBUG` do `pypdf` em toda a aplicação e no worker.
- Preservar `ERROR`+ do `pypdf` no arquivo `flowscope.log`, sem console.
- Não alterar resultado nem tempo da extração.

**Non-Goals:**
- Corrigir o `xref` dos PDFs ou desligar o autorreparo do `pypdf`.
- Mudar `WARNING`/`INFO`/`DEBUG` de outros loggers da aplicação.

## Decisions

### 1. Nível `ERROR` no logger pai `pypdf`

Configurar `logging.getLogger("pypdf").setLevel(logging.ERROR)`. Como os
loggers filhos (`pypdf._reader`, `pypdf._cmap`, …) não têm nível próprio, eles
herdam o nível efetivo e os `WARNING` são descartados na origem. Alternativa:
um `logging.Filter` por handler — desnecessário, pois o nível já corta antes da
formatação.

### 2. O worker configura o próprio logging

O processo filho do extrator (`extracao_orcada._extrair_pdf_filho`) configura o
logger `pypdf` por conta própria: nível `ERROR` e um `FileHandler` apontando para
o log da aplicação, com `propagate=False` para não vazar para o root (sem
handlers no filho, isso cairia no `lastResort`/stderr). A configuração é
idempotente (não duplica handler em chamadas repetidas). Alternativa: usar
`fork` para herdar os handlers do pai — rejeitada, pois `fork` é inseguro em
processo com threads (já decidido na change `limite-tempo-extracao-pdf`).

### 3. Caminho de log em módulo neutro

Mover `presentation/log_paths.py` para `flowscope/log_paths.py` (raiz do
pacote). A camada de aplicação não pode importar `presentation` (guarda de
fronteiras), e o extrator precisa do caminho do log do app. Um módulo de raiz
não pertence a nenhuma camada e é importável por todas. Alternativa: passar o
caminho do log pela API de `extrair_arquivo_com_orcamento` — rejeitada por
acoplar cada ponto de chamada a um detalhe de logging. Os imports em
`presentation/main.py` e `presentation/gui/app_about_actions.py` são atualizados;
em `app_about_actions` mantém-se o nome importado (`from flowscope.log_paths
import log_file_path`) para preservar o alvo de `patch` dos testes.

### 4. Mesmo formato do app no handler do worker

O `FileHandler` do worker usa o mesmo `format`/`datefmt` de
`_configure_logging` (`timestamp | level | logger | mensagem`), mantendo a
consistência exigida pela capability `logging`.

## Risks / Trade-offs

- [Escrita concorrente no mesmo arquivo de log (pai com `RotatingFileHandler`,
  filho com `FileHandler`)] → Aceitável: as escritas de linha são pequenas e a
  rotação é rara; `ERROR` do `pypdf` é excepcional. Alternativa (arquivo
  separado) foi descartada para manter a auditoria num único lugar.
- [Mover `log_paths` quebra o alvo de `patch` dos testes] → Mitigação: manter
  `from flowscope.log_paths import log_file_path` em `app_about_actions`, de modo
  que `app_about_actions.log_file_path` continue existindo.
- [Duplicar o handler a cada chamada] → Mitigação: configuração idempotente
  (verifica handlers já instalados).
- [`ERROR` do `pypdf` silenciado indevidamente] → Não ocorre: só
  `WARNING`/`INFO`/`DEBUG` são suprimidos; `ERROR`+ é gravado no log.

## Migration Plan

Sem migração de dados. Rollout: mover o módulo de caminhos e atualizar imports;
aplicar o silenciamento no app e no worker. Rollback: reverter os pontos de
chamada e restaurar `presentation/log_paths.py`.

## Open Questions

Nenhuma pendente.
