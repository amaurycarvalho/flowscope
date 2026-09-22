## Context

Ver `proposal.md - Why`. O estado ocupado hoje tem duas fontes de verdade e quatro entradas:

- `FlowScopePresenter._operacoes_ativas` (`presenter.py:97`) é a política, mas só é exercida por `on_operation_*`/`on_fundamental_*`.
- `StatusMixin._cursor_states` (`app_status.py:46-67`) é o memento dos cursores, mantido na view.
- `controller.on_ticker_edit` (`controller.py:73,79`) e `actions._copy_chart` (`app_actions.py:240,247`) chamam `_set/_clear_wait_cursor` diretamente, sem passar pela contagem.

O snapshot captura `widget.cget("cursor")` para todos os widgets em `_iter_widgets()` (`app_status.py:51`). O Tk, porém, altera cursores por conta própria durante `<Motion>`: `ttk::treeview::Motion` (`/usr/share/tcltk/tk8.6/ttk/treeview.tcl:104`) grava o cursor "do usuário" em `State(userConfCursor)` — variável de namespace compartilhada por todos os `Treeview` — e troca para `hresize` sobre separadores de coluna; `PanedWindow` faz o análogo com `sb_*` sobre sashes. Se o snapshot capturar um desses cursores transitórios, a restauração os devolve e o `State(userConfCursor)` pode ressuscitar o `watch` anterior em um único grid — explicando o sintoma intermitente e a dessincronização entre as colunas congeladas e o grid rolável da tabela de Fundamentos.

O job fundamentalista já tem resiliência (drenagem por mensagem, watchdog `_job_travado` em `controller_fundamental.py:114`, encerramento garantido). O job de documentos (`documentos_job.py`) publica término em `finally`, mas a drenagem (`app_actions.py:184-210`) não trata exceções por mensagem nem tem watchdog de inatividade.

## Goals / Non-Goals

**Goals:**
- Uma única autoridade de estado ocupado, com contagem de referência e transições `IDLE <-> BUSY` balanceadas, mesmo em exceção.
- Snapshot de cursor imune a cursores transitórios do toolkit e reafirmado enquanto ocupado.
- Restauração garantida em todos os caminhos (início/publicação de job com falha, aquisição de documentos travada/morta).
- Sincronização verificável entre os dois `Treeview` da tabela de Fundamentos.

**Non-Goals:**
- Cancelar threads de jobs substituídos/travados (elas terminam sozinhas; mensagens são descartadas por geração).
- Tornar a carga histórica assíncrona ou alterar o `OperationGuard`.
- Mudar domínio/aplicação, formato das mensagens dos jobs ou a API pública do protocolo `GUIView` além do necessário.
- Introduzir um objeto Observer dedicado (a reafirmação em `<Motion>` é o mecanismo de reparo; não há necessidade de notificação desacoplada).

## Decisions

### 1. Autoridade única de estado ocupado no presenter (contagem de referência + context manager)

Substituir o par `_operacoes_ativas` + métodos públicos `set/clear_wait_cursor` por um estado `IDLE | BUSY` com contagem de referência no presenter. `enter()` incrementa e, na transição 0->1, chama `view.disable_all_buttons()` + `view.enter_busy()`; `exit()` decrementa e, na transição 1->0, chama `view.restore_all_buttons()` + `view.exit_busy()` + `view.clear_progress()` + `_sincronizar_copy_button()`. Expor `busy()` como `@contextmanager` para que todos os caminhos usem `with presenter.busy():`, garantindo saída no `finally`.

- **Alternativa descartada**: manter os métodos `on_operation_started/finished` e apenas documentar o balanceamento — não impede desbalanceamento por exceção.
- **Alternativa descartada**: contador no controller — o controller já é múltiplo (mixins) e não vê a view; a política pertence ao presenter.

### 2. Presenter = política; view = mecanismo (memento)

O presenter decide *quando* entrar/sair do estado ocupado; a view decide *como* capturar/restaurar cursores e reafirmar. O protocolo `GUIView` troca `set_wait_cursor`/`clear_wait_cursor` por `enter_busy()`/`exit_busy()` (ou mantém os nomes atuais com semântica de transição). A view continua sendo a única que conhece widgets.

- **Alternativa descartada**: mover o snapshot para o presenter — exigiria expor a árvore de widgets ao presenter, quebrando a separação.

### 3. Normalizar o snapshot (ignorar cursores transitórios do toolkit)

Ao capturar, registrar o cursor anterior apenas se ele **não** for um cursor transitório de toolkit (`hresize`, `sb_h_double_arrow`, `sb_v_double_arrow` e correlatos de redimensionamento de separadores/sashes); nesses casos, registrar o valor de repouso (`""`) como baseline. Alternativamente/adicionalmente, reafirmar o cursor após a captura. Assim a restauração nunca devolve `hresize`/`sb_*` e o `State(userConfCursor)` não reintroduz o `watch`.

- **Alternativa descartada**: restaurar o valor exato sempre — é justamente o que propaga o cursor transitório e dispara a ressuscitação do `watch`.
- **Alternativa descartada**: mexer em `ttk::treeview::State` diretamente via Tcl — frágil e dependente de detalhes internos do toolkit.

### 4. Reafirmar o cursor em `<Motion>` enquanto ocupado

Enquanto a contagem estiver ativa, instalar um hook global (`bind_all("<Motion>")`) que reaplica o cursor de espera ao widget sob o ponteiro; ao sair do estado ocupado, removê-lo e restaurar o baseline. Como a ordem de bindings do Tk é widget -> classe -> toplevel -> **all**, o hook roda depois de `ttk::treeview::Motion` e de qualquer cursor de separador/sash, sobrepondo-os. Isso repara a dessincronização entre grids: qualquer grid que o ponteiro entre é reafirmado para `watch` durante a operação e para o baseline ao final.

- **Alternativa descartada**: usar o padrão Observer para notificar mudanças de estado e então reparar — o Observer só notifica; o reparo exige um enforcer ligado a `<Motion>`. Modelar o estado como observável adicionaria indireção sem ganho.
- **Risco de performance**: `<Motion>` é frequente; o hook deve ser O(1) (um `config` condicional) e só existir enquanto ocupado.

### 5. Balancear o job fundamentalista em falhas de início/publicação

Em `_iniciar_analise_fundamental`, contabilizar o início e garantir o término correspondente mesmo se `job.iniciar()` ou `on_progress` falharem, seja com `try/except` que chama o término em falha, seja movendo o incremento para depois do job iniciado com sucesso. Como a chamada ocorre dentro do `try` de `on_load_data`/`on_index_clicked`, a exceção hoje só decrementa a operação de carga e deixa a operação fundamental contabilizada para sempre.

- **Alternativa descartada**: depender apenas do `except` de `on_load_data` — ele não conhece a operação fundamental já contabilizada.

### 6. Watchdog e tratamento por mensagem no job de documentos

Espelhar no fluxo de documentos o que já existe no fundamentalista: envolver o tratamento de cada mensagem em `try/except` (registrar no log e continuar) e encerrar o job quando a thread morrer sem publicar término ou quando passar o limite de inatividade, sempre chamando o término da operação. `DocumentosJob` já publica término em `finally` (`documentos_job.py:60`), mas o watchdog cobre travamento dentro de `adquirir`.

- **Alternativa descartada**: tratar apenas `queue.Empty` — não cobre exceção de renderização nem thread travada.

### 7. Eliminar caminhos diretos de cursor

`controller.on_ticker_edit` e `actions._copy_chart` passam a usar `with presenter.busy():` em vez de `_set/_clear_wait_cursor` diretos. `_copy_data` (atalho Ctrl+Shift+C) passa a ser envolvido no mesmo contexto, dando feedback consistente e integrando-se ao bloqueio.

- **Alternativa descartada**: manter os caminhos diretos e apenas torná-los ref-counted na view — duplicaria a política em dois lugares.

### 8. Testes

- Presenter: transições 0->1->0 chamam `enter_busy`/`exit_busy` uma vez; operações sobrepostas só restauram na última; `busy()` restaura em exceção.
- Controller: falha em `job.iniciar()`/`on_progress` não deixa contagem presa; `on_ticker_edit`/`_copy_chart` usam o contexto.
- Documentos: erro ao tratar mensagem, thread morta e inatividade encerram o job e liberam cursor.
- GUI (requer `DISPLAY`): baseline com separador de coluna não restaura `hresize`; `<Motion>` sobre separador/sash mantém `watch`; os dois `Treeview` da tabela de Fundamentos apresentam o mesmo cursor antes/depois.
- Cobertura: teste que enumera as abas/sub-abas construídas e verifica que os widgets estáticos são cobertos pelo estado ocupado.

## Risks / Trade-offs

- **[Hook global de `<Motion>` com custo]** → só ativo enquanto ocupado e O(1); desinstalado na transição 1->0.
- **[Normalização apagar um cursor intencional igual a `hresize`/`sb_*`]** → nenhum widget da aplicação define esses cursores intencionalmente; a lista de normalização é restrita aos transitórios de separador/sash.
- **[Reafirmação global interferir em diálogos modais abertos durante operação]** → os controles ficam desabilitados durante o estado ocupado; se um diálogo precisar de cursor próprio, ele deve suspender a reafirmação (documentar).
- **[Mudança de API do protocolo `GUIView`]** → atualizar mocks/testes existentes que usam `set_wait_cursor`/`clear_wait_cursor`.
- **[Watchdog de documentos encerrar aquisição legítima longa]** → o limite é de inatividade (sem progresso), não de duração total, espelhando `_LIMITE_INATIVIDADE_S`.

## Migration Plan

Sem migração de dados. A troca de API do protocolo é interna à camada de apresentação. Rollback = reverter a change.

## Open Questions

- Nenhuma.
