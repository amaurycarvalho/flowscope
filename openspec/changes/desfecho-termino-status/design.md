## Context

O `BackgroundManager` (`presentation/gui/background/manager.py`) é o mecanismo único de jobs assíncronos: executa o trabalho fora da thread do Tk, publica eventos por fila e drena tudo num único ponto agendado. O worker comunica-se apenas por um `JobContext` (`background/context.py`) com `progress`, `resultado` e `erro`; o ciclo termina publicando `Termino(cancelado: bool)` (`background/events.py`).

Três lacunas do contrato atual moldam o desenho:

1. **Término não carrega desfecho.** `Termino` só tem `cancelado`. A mensagem de interrupção é decidida em `FlowScopePresenter.exit()` (`presenter.py:184`) lendo o token global `_cancel_token` — que **nenhum job recebe** (é estado vestigial só para a mensagem).
2. **`Erro` está semanticamente sobrecarregado.** É falha fatal em `controller_data.py:203,206`, `fundamental_job.py:51` e `chat/envio.py:180,182,184`; e é sinal de item (control-flow) em `resumos_job.py:107,170`. Portanto o desfecho **não pode** ser inferido da presença de `Erro`.
3. **Falhas recuperadas no worker não têm canal de desfecho.** `AnalyzeTickersUseCase` recupera por ticker (via `ProgressReporter`), `FundamentalAnalysisUseCase` marca `houve_falha_recuperavel` e publica `Resultado(falhou=True)`, e a aquisição de documentos/notícias é tolerante por contrato (`documentos_aquisicao.py:5-6`, `noticias_carga.py:77`). Essas falhas não devem virar erro de status.

O `presenter` mantém a autoridade única de estado ocupado (`enter`/`exit` com contagem), alimentada pelos listeners globais em `app_wiring.py:224-234`. Chat (`chat/envio.py:38`) e preview (`charts/document_flow_mixin.py:199`) usam managers **locais** com status próprio — o contrato novo não pode assumir um presenter global. Ver `proposal.md` para a motivação.

## Goals / Non-Goals

**Goals:**
- Tornar o desfecho terminal do job um fato explícito do mecanismo (`SUCESSO`/`FALHA`/`CANCELADO`/`ABORTADO`), declarado pelo worker e com default por exceção que escapa.
- Garantir que todo término não-cancelado e não-sucedido produza aviso na barra de status, sem sobrescrever mensagens específicas já exibidas.
- Distinguir cancelamento do usuário de encerramento involuntário pelo watchdog.
- Remover o token global vestigial do presenter como fonte de verdade do cancelamento.
- Corrigir mensagens de conclusão de documentos/notícias e a falha de pré-visualização presa em carregamento.

**Non-Goals:**
- Alterar o contrato de `domain`/`application` (o desfecho é conceito de apresentação).
- Centralizar todas as mensagens de erro no presenter (as mensagens ricas por feature permanecem).
- Classificar falha por fonte na aquisição tolerante de documentos/notícias.
- Introduzir métricas/observabilidade de desfecho além do necessário à barra de status.

## Decisions

**D1 — Desfecho explícito, não inferido.** `Outcome = SUCESSO | FALHA | CANCELADO | ABORTADO` em `background/events.py`; `Termino` carrega `outcome` e `cancelado` vira propriedade derivada (`outcome is CANCELADO`) para compatibilidade. O desfecho é declarado pelo worker; nunca derivado de "apareceu um `Erro`". Alternativa rejeitada: inferir por contagem de eventos — quebraria `resumos`, que publica `Erro` por item sem falhar.

**D2 — `PARCIAL` fica fora do `Outcome`.** Falha de item recuperada permanece nos canais existentes (`Resultado(falhou=True)`, contagem no `ProgressReporter`, resumo do lote). Alternativa considerada: `PARCIAL` no mecanismo com fallback uniforme — rejeitada por duplicar mensagem com o canal do feature e arriscar falso positivo.

**D3 — Declaração via `JobContext.falhar(exc)`.** `ctx.erro` passa a significar falha de item/diagnóstico (publica `Erro(fatal=False)`, não altera desfecho). `ctx.falhar(exc)` publica `Erro(fatal=True)` e marca `FALHA`. Os 6 sítios fatais migram para `ctx.falhar`; os 2 de `resumos` permanecem em `ctx.erro`. Alternativa: derivar falha de `ctx.erro` — rejeitada pela sobrecarga em D1.

**D4 — Defaults por escape e no `finally`.** Em `manager._trabalhar`: retorno normal sem `falhar` → `SUCESSO`; `OperacaoCancelada` → `CANCELADO`; `Exception` não tratada → `ctx.falhar` (`FALHA`); `finally` marca `FALHA` se o desfecho continuar indefinido (cobre `BaseException` e `trabalho=None`). **Não** capturar `BaseException` para reclassificar: preserva a semântica de interrupção e evita mascarar erros catastróficos. Complemento: instalar `threading.excepthook` para registrar no logger do app as exceções que escapam do worker.

**D5 — Watchdog aborta, não cancela.** `_aplicar_watchdog` passa a encerrar com `ABORTADO` (thread morta/fila vazia e inatividade), deixando de reusar `cancelado=True`. Remove o estado global como fonte da mensagem e dá canal honesto ao encerramento involuntário.

**D6 — Rede de segurança "fallback só se não reportado".** O manager registra, ao despachar uma falha fatal, se o callback de erro existia e executou sem exceção (`_invocar` passa a retornar `bool`; `handle.falha_reportada`). `Termino.falha_reportada` leva o flag. No presenter, ao zerar a contagem, o desfecho agregado escolhe a mensagem com precedência `falha_nao_reportada > cancelado > abortado`; `FALHA` já reportada e `SUCESSO` não escrevem nada. Alternativa rejeitada: presenter sempre escrever o desfecho genérico último — sobrescreveria mensagens ricas (`on_technical_error`, portfólio, resumos).

**D7 — Remover o token global do presenter.** `exit()` deixa de ler `_cancel_token`; `request_cancel()` passa a delegar apenas a `background.cancel_all()`. Elimina a segunda fonte de verdade de "foi cancelado" (I4). Se a entrega for incremental, o token sai na task final, com a task anterior já deixando de lê-lo.

**D8 — Mensagem de conclusão honesta (documentos/notícias).** Manter a aquisição tolerante (`SUCESSO`), mas tornar a mensagem dependente de quantidade: `adquirir(...)` retorna a contagem de itens persistidos (mudança aditiva de retorno) e o desfecho escolhe "atualizados" vs. mensagem neutra. Alternativa rejeitada: classificar "fonte indisponível" na infra — espalha semântica de falha pela porta e não é necessária ao status.

**D9 — Fallback de pré-visualização no feature.** A falha da leitura assíncrona/preview é tratada no próprio painel via `ao_erro`, com o guard de seleção (`_arquivo_selecionado() is arquivo`) e o vocabulário existente (`_summary.mensagem_indisponivel()`), não pelo presenter global. Managers locais permanecem com status próprio.

## Risks / Trade-offs

- **Falsos positivos de erro em lote que se recupera** → mitigado por D1/D2 (desfecho declarado; `PARCIAL` fora) e pelos defaults de D4.
- **Sobrescrita de mensagem específica por fallback genérico** → mitigado por D6 (`falha_reportada` só é verdadeiro se o callback executou).
- **Agregação ambígua com jobs sobrepostos** → escrita do desfecho só na transição para ocioso, com precedência explícita; jobs substituídos seguem o fluxo `SUBSTITUIR` que mantém a contagem acima de zero.
- **Mudança de assinatura de `Termino`/`exit` quebra testes** → campos com default e `cancelado` derivado preservam a maior parte; testes que fixam o token são atualizados para verificar o desfecho.
- **Encolher a contagem de itens adquiridos pode exigir tocar a infra** → manter a mudança aditiva (`None` → `int`) e, se indisponível no momento, usar mensagem neutra (não afirmar) como fallback de menor custo.
- **`BaseException` que escapa ainda imprime traceback no stderr** → aceito; `threading.excepthook` leva o registro ao log do app e a UI é avisada via fallback.

## Migration Plan

1. Introduzir `Outcome`, `Erro(fatal)`, `Termino(outcome, falha_reportada)` e `JobContext.falhar` (aditivo, sem mudar comportamento observável).
2. Migrar os 6 sítios fatais para `ctx.falhar`; ajustar `manager._trabalhar`/`_finalizar`/watchdog para declarar desfecho.
3. Ligar o desfecho ao presenter (`app_wiring`), implementar a precedência de fallback e parar de ler `_cancel_token`.
4. Ajustar painéis: mensagem honesta de documentos/notícias (D8) e fallback de preview (D9).
5. Remover `_cancel_token` e atualizar testes (presenter, cancelamento, startup gate, carga, painéis).
6. `openspec validate`, lint e suíte (ver `tasks.md`).

Rollback: cada passo é reversível isoladamente; o passo 1 é aditivo e não altera comportamento, permitindo reverter sem deixar a interface em estado inconsistente.

## Open Questions

Nenhuma pendente que altere specs, abordagem ou tasks.
