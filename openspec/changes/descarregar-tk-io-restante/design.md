## Context

Ver `proposal.md - Why`. Restaram três pontos síncronos na thread do Tk, já mapeados após `background-job-manager`/B/C/`cache-prompt-chat`:

- `DocumentFlowMixin._iniciar_preview` (`document_flow_mixin.py:152`): antes de `_preview_background().submit`, lê o cache persistente (`_texto_cacheado` → `_text_store.obter`, `:98`), avalia `_summary.precisa_resumo` e `_precisa_guidance`, tudo na thread do Tk.
- `ActionsMixin._copy_chart` (`app_actions.py:290`): chama `ClipboardImageAdapter.copy_image`, que faz `figure.savefig` e `subprocess.run` (`xclip`/PowerShell/osascript) de forma síncrona, sob `presenter.busy()`.
- `NoticiasActionsMixin._finalizar_noticias`/`_reagendar_remontagem` (`noticias_actions.py:79`): após cancelar, agenda `self.after(100, ...)` consultando `thread.is_alive()` por até 300 tentativas (~30s) na thread do Tk.

O `BackgroundManager` (com token por job, `Politica.LATEST_WINS` e eventos tipados `Resultado`/`Erro`/`Termino`) e o `JobContext` já existem em `presentation/gui/background`. O manager de preview já é local ao painel (`_preview_background`, `document_flow_mixin.py:179`), a cópia pode usar um manager local, e o job de notícias roda no manager global.

## Goals / Non-Goals

**Goals:**
- Tirar da thread do Tk a leitura de cache e a avaliação de resumo/guidance da pré-visualização.
- Tirar da thread do Tk o `subprocess` de transferência ao clipboard.
- Substituir o polling de cancelamento das notícias pelo término do job.
- Manter o comportamento observável (texto exibido, feedback de status, precedência de carga nova) e os orçamentos de UI (`reduzir-testes-ui`).

**Non-Goals:**
- Alterar as portas `ClipboardPort`, `DocumentTextStore` ou `LLMPort`.
- Mover o rendering matplotlib da figura para fora da thread do Tk (risco de concorrência com o backend); só o `subprocess` sai.
- Reduzir congelamentos de I/O curto (preferências, atalho, `xdg-open`) — custo desprezível.

## Decisions

### Decisão 1: Pré-visualização — só a memória de sessão fica no Tk

**Escolha**: `_iniciar_preview` deixa de ler o store persistente e de avaliar resumo/guidance. Ele apenas publica o estado de carregamento e submete o trabalho. O worker `_trabalhar` calcula `texto` (memo de sessão ou store), se o resumo é necessário e o resumo; o resultado (`texto`, `precisa_resumo`, `resumo`) volta por `Resultado` e é aplicado na thread do Tk.

**Alternativas**: manter o caminho rápido "cache de sessão + `long_summary` em memória → exibe direto" na thread do Tk.

**Razão**: o caminho rápido toca a memória de sessão (barato), mas a decisão de resumo depende do store/guidance em disco. Um único caminho pelo worker é mais simples e garante que nenhuma leitura de disco fique no Tk. O trade-off é que o primeiro acesso a um documento já resumido passa por um job curto (mostrando "Carregando…" em vez de exibir instantâneo); aceito em troca de nunca bloquear.

### Decisão 2: Cópia de gráfico — rendering no Tk, transferência no worker

**Escolha**: `_copy_chart` salva a figura em PNG na thread do Tk e submete apenas a **transferência** para o sistema ao `BackgroundManager` (grupo `"clipboard"`, `Politica.LATEST_WINS`). O feedback de sucesso/erro e o `presenter.busy()` continuam vindo dos eventos do job.

**Alternativas**: (a) rodar `copy_image(figure)` inteiro no worker; (b) manter tudo síncrono.

**Razão**: o backend Agg do matplotlib não é seguro contra `savefig` concorrente com o desenho dos charts, então o rendering permanece na thread do Tk; o custo que motivou a change é o `subprocess`, que passa a rodar no worker. A infraestrutura separa `salvar_png(figure) -> Path` de `transferir_png(path)`, mantendo a porta `ClipboardPort` intacta.

### Decisão 3: Notícias — término do job, sem laço de `after`

**Escolha**: removem-se `_reagendar_remontagem` e `_LIMITE_REMONTAGEM`. No `ao_termino` do job de aquisição, a remontagem é agendada com `after(0, self._remontar_noticias)`, de modo que roda depois de o manager finalizar o job; `_remontar_noticias` só remonta se não houver job de aquisição ativo (`not background.tem_ativo(GRUPO)`), preservando a precedência de uma carga nova.

**Alternativas**: continuar consultando `thread.is_alive()` no Tk.

**Razão**: o manager já sabe quando o worker termina; quando `ao_termino` dispara, a função de trabalho já retornou (as gravações de índice do item corrente terminaram). O `after(0)` garante que a verificação de "job ativo" enxergue o estado pós-`_finalizar` (o job antigo removido e um eventual novo ativo), que é exatamente o critério que o polling atual tenta reproduzir.

### Decisão 4: Testes headless

**Escolha**: os três fluxos são verificados com fakes de `JobContext`/manager, sem `tk.Tk`, conforme `presentation-test-coverage` (de `reduzir-testes-ui`). Ficam sob UI apenas a aplicação do preview na caixa, o estado de botões e o feedback de status.

**Razão**: é orquestração de job, não comportamento de widget; evita consumir o teto de `@needs_display`.

## Risks / Trade-offs

- **[Risco]** `savefig` no Tk ainda custar para figuras grandes → **Mitigação**: mantém a interface responsiva ao transferir no worker; se o rendering se mostrar custoso, avaliar cópia do `Figure` para um `FigureCanvasAgg` fora da thread em change futura.
- **[Risco]** O preview agora sempre passa por um job, adicionando latência mínima a documentos já resumidos → **Trade-off** aceito; a interface nunca bloqueia.
- **[Risco]** A remontagem via `after(0)` não capturar um job que inicie no mesmo tick do término → **Mitigação**: a checagem `tem_ativo(GRUPO)` no `_remontar_noticias` mantém a precedência; coberta por teste.
- **[Risco]** Erro no worker de clipboard deixar a barra de status sem feedback → **Mitigação**: `ao_erro`/`ao_resultado` publicam status e sempre passam por `presenter.exit()` (via listeners de ciclo de vida).

## Migration Plan

1. Separar rendering e transferência em `clipboard_image.py` e portar `_copy_chart` para o manager, com testes headless e verificação do estado ocupado.
2. Mover a leitura de cache/avaliação do preview para `_trabalhar`, ajustando o resultado do job, com testes headless.
3. Substituir `_reagendar_remontagem` pelo término do job, com teste de precedência.
4. Rodar a suíte de apresentação, o guardrail de teto de UI, complexidade e fronteiras. Rollback = reverter o commit (sem migração de dados).
