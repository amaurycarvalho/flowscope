## Context

A janela usa um `tk.PanedWindow` horizontal (`_main_pw`) como divisor esquerda/direita, com `stretch="always"` no painel esquerdo e `stretch="never"` no direito (`app_layout.py:139-175`). Existe também uma `_left_pw` vertical que recebe **um único** painel (`app_layout.py:144-150`) — não tem sash, então `sash_coord(0)` levanta `TclError: invalid sash index` (confirmado em reprodução com `xvfb`).

O salvamento (`app.py:211-221`) monta `positions = [main_x, main_y, left_x, left_y]`, mas a chamada da `_left_pw` levanta antes da atribuição de `_prefs["sash_positions"]`; logo o valor nunca é atualizado e o arquivo mantém um resíduo antigo (`[856, 1, 1, 554]` no `~/.flowscope/config.json` atual). A restauração (`app_layout.py:196-202`, `app_tab_layout.py:273-279`) exige `len >= 4` e usa `positions[1]` para o painel esquerdo (índice trocado). Como o `stretch` deriva o sash da largura do painel direito, guardar o x absoluto é frágil a mudança de resolução.

No cursor, `StatusMixin` (`app_status.py`) faz snapshot de todos os widgets na entrada do estado ocupado, força `watch`, e usa um hook global de `<Motion>` para reafirmar `watch` sobre o widget sob o ponteiro. `_clear_wait_cursor` só restaura widgets presentes em `_cursor_states`; widgets criados depois do snapshot que recebem `<Motion>` ficam com `watch` preso (reproduzido). O hook é removido com `unbind_all("<Motion>")` (`app_status.py:162`) e não consulta o estado de ocupado.

O estado ocupado tem autoridade única no `FlowScopePresenter` (`enter`/`exit` com contagem) e é alimentado pelos listeners do `BackgroundManager` global (`app_wiring.py:224-234`). Managers locais (chat, preview de documentos, resumos) não mexem no cursor global.

## Goals / Non-Goals

**Goals:**
- Persistir a largura do painel direito e restaurá-la fielmente, inclusive entre resoluções diferentes.
- Eliminar o vazamento do cursor de espera em widgets criados durante a operação e tornar o `watch` auto-curável quando não há operação ativa.

**Non-Goals:**
- Fazer managers locais (chat, documentos, resumos) acionarem o cursor global.
- Forçar o cursor em todos os widgets internos de diálogos (o hover cobre).
- Redesenhar o layout de painéis ou o sistema de abas.

## Decisions

**D1 — Persistir largura, não posição absoluta.** Salvar `largura_direita = _main_pw.winfo_width() - _main_pw.sash_coord(0)[0]`. Alternativa (a): guardar x absoluto — rejeitada porque o `stretch` reancora o sash pela largura do painel direito, então x não se transporta entre resoluções.

**D2 — Restaurar após a janela estar no tamanho final.** Aplicar `sash_place(0, x, 0)` com `x = largura_atual - largura_direita`, agendado para o primeiro `<Map>`/`<Configure>` em que a janela já tenha a geometria aplicada (não em `after(100)` fixo), com clamp de x a um mínimo que preserve o painel esquerdo. Alternativa: manter `after(100)` — rejeitada por perder a corrida com o WM em resoluções grandes/PyInstaller.

**D3 — Remover a `_left_pw` morta.** Substituir a estrutura de painel único, adicionando `_main_notebook` diretamente ao `_main_pw`, e apagar o branch de restauração do segundo sash. Alternativa: manter e ignorar — rejeitada por manter código morto e uma fonte de `TclError`.

**D4 — Migrar/descartar formato legado.** Aceitar apenas o novo formato (largura numérica). Um `sash_positions` legado (lista de 4) é ignorado e o layout padrão é aplicado. Evita restaurar coordenadas inválidas.

**D5 — Registrar o repouso no toque.** Em `_on_busy_motion`, antes de forçar `watch`, se o widget sob o ponteiro não estiver em `_cursor_states`, gravar o cursor de repouso normalizado (`_cursor_de_repouso`) dele. Garante restauração de widgets criados após o snapshot.

**D6 — Auto-limpeza guiada por estado.** O hook de `<Motion>` consulta um acessor público de "ocupado" (nova propriedade no presenter, agregando operações ativas; opcionalmente `_background` global). Se ocioso, chama `_clear_wait_cursor` (ou equivalente) e desinstala o hook em vez de reafirmar `watch`. Alternativa: confiar apenas no `exit` balanceado — rejeitada porque um `exit` perdido prende o cursor.

**D7 — Remover apenas o binding específico.** Trocar `unbind_all("<Motion>")` por `unbind` do callback no tag/instância corretos, para não apagar outros bindings globais de `<Motion>`.

**D8 — Escopo de cursor.** Diálogos/`Toplevel` seguem por hover (D5); managers locais permanecem fora do cursor global (consistente com `chat/envio.py:1-8`).

## Risks / Trade-offs

- [A `_left_pw` pode ter outro papel não mapeado] → remover apenas após confirmar que `_main_notebook` pode ser filho direto de `_main_pw` sem regressão de layout; validar com teste de construção da janela.
- [Clamp do painel direito] → escolher mínimo/máximo; se a resolução salva for menor, priorizar não colapsar o painel esquerdo.
- [Acessor de "ocupado" divergir da autoridade] → derivar do próprio presenter/count para manter uma única fonte de verdade.
- [Custo do hook em todo movimento] → o trabalho é O(1) e só toca o widget sob o ponteiro; aceitável.
- [Cursores transitórios de sash/separador] → manter `_CURSORES_TRANSITORIOS` como baseline e reaplicar `watch` enquanto ocupado.

## Migration Plan

1. Novo formato de `sash_positions` (largura). Valor legado descartado na leitura; primeira sessão usa o posicionamento padrão e passa a gravar a largura.
2. Sem rollback de dados necessário: o campo é uma preferência não-crítica; um valor desconhecido cai no padrão.

## Open Questions

- Nenhuma que altere specs/abordagem; a correlação observada com PyInstaller/resolução alta é consistente com a corrida de geometria (D2) e não muda o desenho.
