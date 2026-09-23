## Context

Ver `proposal.md - Why`. O estado atual que molda o desenho:

- O botão é sempre visível e seu estado é derivado em `DocumentTreePanel.refresh_resumir_button()` (`document_flow_mixin.py:48-55`): `habilitado = _summary.disponivel() and ha_pendentes`.
- `refresh_resumir_button()` é chamado de vários pontos: `update()` (`document_tree_panel.py:182`), `_atualizar_resumo()` disparado por `aplicar_resumo()` do lote (`document_flow_mixin.py:199-208`), pelo resumo individual (`_aplicar_preview`), e pelo `on_saved` do diálogo de I.A. (`app_actions.py:81`).
- O lote é orquestrado no app-layer por `ResumosActionsMixin`, que guarda o job ativo em `_resumos_job` (`app_resumos_actions.py:35,43,174-175`). A cada resultado, o poll chama `painel.aplicar_resumo(...)` na thread do Tk (`app_resumos_actions.py:143-154`), que reavalia o botão ainda com pendentes e o reabilita.
- O bloqueio global (`presenter.enter()` → `disable_all_buttons`) desabilita o botão no início, mas o `refresh_resumir_button()` subsequente sobrescreve esse estado.
- O painel já recebe callbacks injetados a partir de `app_tab_layout.py` (`resumir_callback`, `ia_callback`, `acquire_callback`), que servem de padrão para expor informação do app-layer sem o painel conhecer a view global.

## Goals / Non-Goals

**Goals:**
- Fazer o estado derivado do botão considerar "lote em andamento" para permanecer desabilitado durante todo o processamento.
- Manter a reavaliação correta ao término: habilitado se houver pendentes e LLM, desabilitado caso contrário.
- Preservar o contrato existente do painel quando usado isoladamente (sem callback injetado).

**Non-Goals:**
- Alterar fases, progresso, mensagens ou interrupção do lote.
- Alterar o bloqueio global de botões ou o comportamento do botão "Abrir documento".
- Impedir a seleção na árvore ou resumos individuais concorrentes (o lote continua não cancelando a seleção).

## Decisions

### 1. Incorporar "lote em andamento" ao estado derivado (em vez de suprimir a reavaliação)

`refresh_resumir_button()` passa a calcular `habilitado = not lote_ativo and _summary.disponivel() and ha_pendentes`. A reavaliação continua acontecendo em todos os pontos; o que muda é a condição.

- **Por quê:** a reavaliação é disparada por múltiplos caminhos (resultado do lote, resumo individual concorrente, `update()` ao trocar ticker, salvamento da config). Corrigir apenas `aplicar_resumo` deixaria os outros caminhos reabilitando o botão no meio do lote.
- **Alternativas:** suprimir a reavaliação em `aplicar_resumo` durante o lote (rejeitado: incompleto nos demais caminhos); confiar só no bloqueio global (rejeitado: é exatamente o que o refresh sobrescreve hoje).

### 2. Fonte de verdade no app-layer via callback injetado

O painel recebe um `resumir_ativo_callback: Callable[[], bool] | None`; o app injeta `_resumos_em_andamento`, que retorna `_resumos_job is not None`. Quando o callback é `None`, o painel assume `False`.

- **Por quê:** `_resumos_job` é a única fonte de verdade do lote; um predicado evita desincronização entre app e painel e segue o padrão de callbacks já usado (`resumir_callback`/`ia_callback`). Mantém a leitura na thread do Tk (o job é criado/limpo apenas nela).
- **Alternativas:** flag booleana no painel setada/limpa pelo app (rejeitado: exige acertar todos os caminhos de início, falha na partida e término, com risco de estado preso); consultar o estado ocupado do presenter (rejeitado: acoplaria camadas e o resumo individual não passa pelo `busy()`).

### 3. Ordem de término já garante a reavaliação correta

`_finalizar_resumos_job` zera `_resumos_job` antes de `presenter.exit()` (`app_resumos_actions.py:174-176`); assim o `_restore_all_buttons` reavalia com o lote já inativo. No caminho de falha ao iniciar, o job também é zerado antes do `exit()` (`app_resumos_actions.py:57-62`).

- **Por quê:** não é necessário reordenar nada; a reabilitação reflete pendentes remanescentes (interrupção) ou ausência deles (conclusão).
- **Alternativas:** reavaliar explicitamente só no fim do poll (rejeitado: o `refresh_resumir_button()` de `_restore_all_buttons`/`update()` continua sendo o ponto único correto).

## Risks / Trade-offs

- **[Callback não injetado em testes/uso isolado]** → o painel trata `None` como "sem lote ativo", preservando o comportamento atual sem o callback.
- **[Troca de ticker durante o lote]** → `update()` reavalia com o predicado ainda ativo, mantendo o botão desabilitado até o término; correto em relação ao requisito.
- **[Resumo individual concorrente durante o lote]** → quando ele grava `long_summary`, a reavaliação permanece desabilitada pelo predicado; ao término, o estado reflete as pendências reais.
- **[Sobrecarga de wiring]** → aditivo e restrito ao caminho de construção do painel; rollback é remover o parâmetro e a condição.

## Migration Plan

- Aditivo: novo parâmetro opcional e uma condição no estado derivado; sem migração de dados.
- Rollback: remover o callback e voltar a condição para `disponivel() and ha_pendentes`.
