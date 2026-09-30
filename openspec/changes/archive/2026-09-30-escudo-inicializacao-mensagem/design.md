## Context

Ver `proposal.md - Why`. O escudo é criado por `StartupGateMixin.colocar_escudo` (`startup_gate.py`) como um `tk.Frame(self, cursor="watch")` colocado com `place(x=0, y=0, relwidth=1, relheight=1)` e `lift()`, sem conteúdo. A barra superior (`_build_top_bar` em `app_layout.py`) é um `tk.Frame(self)` empacotado no topo, contendo o rótulo "Data de referência", o `DateEntry` e os botões/comboboxes. O `DateEntry` do `tkcalendar` mantém um calendário num `Toplevel` próprio (`overrideredirect(True)`), e cada `ToolTip` cria seu próprio `Toplevel`.

Estado verificado: com o gate ativo, `winfo_containing` sobre o rótulo "Data de referência" e sobre a entrada de data retorna o próprio escudo — o frame cobre a barra superior em condições normais. O relato de não cobertura é coerente com cenários em que o empilhamento se perde ou com popups auxiliares (Toplevels) que escapam ao escudo, já que Toplevels não são cobertos por um frame filho do toplevel principal.

## Goals / Non-Goals

**Goals:**
- Tornar o bloqueio autoexplicativo com uma mensagem de espera dentro do escudo.
- Garantir, de forma verificável, que a barra superior de data permaneça coberta enquanto o gate está ativo.
- Impedir que popups auxiliares (tooltip da data, calendário do `DateEntry`) apareçam acima do escudo.
- Manter o escudo durante toda a inicialização, liberando-o só quando a carga inicial em background conclui.

**Non-Goals:**
- Redesenhar a barra superior ou a ordem de construção dos widgets.
- Introduzir transparência/opacidade (Tk não suporta no `tk.Frame`).

## Decisions

### Decisão 1: Mensagem como `tk.Label` centralizado dentro do escudo

**Escolha**: o escudo passa a ser um contêiner com um `tk.Label` posicionado via `place(relx=0.5, rely=0.5, anchor="center")`, com texto fixo de espera (ex.: "Aguarde a inicialização da aplicação…") e fonte um pouco maior que a padrão.

**Alternativas**: mudar a barra de status em vez do escudo; usar um `Toplevel` de splash separado.

**Razão**: mantém a mensagem dentro do próprio escudo (requisito), sem introduzir uma janela extra que precisaria ser fechada/empilhada. A barra de status continua visível abaixo do escudo e não substitui a indicação central.

### Decisão 2: Garantir o empilhamento sobre a barra superior

**Escolha**: manter `place(relwidth=1, relheight=1)` cobrindo todo o toplevel e reafirmar o empilhamento com `lift()` após a colocação. Como o escudo é filho do toplevel principal, o `place` com dimensões relativas cobre a barra superior (que também é filha do toplevel); o `lift()` garante que fique acima dos irmãos.

**Alternativas**: percorrer a árvore e desabilitar/ocultar cada widget da barra superior; reorganizar a barra para dentro de um contêiner comum.

**Razão**: uma única operação cobre qualquer widget, inclusive os que não expõem `all_buttons()`, sem duplicar a lógica de bloqueio já existente. A cobertura passa a ser verificada por teste de UI sobre o rótulo/entrada de data.

### Decisão 3: Popups auxiliares já são impedidos pelos controles desabilitados

**Escolha**: não adicionar guardas novos a `ToolTip`/`DateEntry`; aproveitar que o gate desabilita a entrada de data (`_disable_all_buttons`) e que o escudo intercepta eventos de ponteiro. Assim, o tooltip (acionado por `<Enter>`) e o calendário (acionado por clique) não são disparados enquanto o gate está ativo.

**Alternativas**: adicionar um flag global consultado pelo `ToolTip`; interceptar bindings do `DateEntry`.

**Razão**: evita acoplar widgets genéricos ao estado de inicialização e não aumenta o orçamento de testes de UI. A garantia é coberta pelo cenário correspondente no spec.

### Decisão 4: Escudo colocado antes da construção e liberado quando ocioso

**Escolha**: `FlowScopeGUI.__init__` coloca o escudo logo após configurar a janela, antes de `_build_top_bar`/painéis, e o reergue ao fim de cada etapa de construção e no `iniciar_gate`. A liberação não acontece mais no fim de `_restore_tabs`: `StartupGate.finalizar` apenas decrementa a operação do gate, e o escudo é removido quando a autoridade de estado (`FlowScopePresenter`) volta a ociosa, via callback `ao_ficar_ocioso`. Um release de segurança por timeout cobre o caso de a restauração inicial não executar.

**Alternativas**: manter a remoção no fim de `_restore_tabs`; manter um `after` de polling sobre o contador de operações.

**Razão**: a primeira pintura da janela passa a sair coberta (o gate é colocado antes dos widgets) e o usuário vê a mensagem durante toda a carga inicial em background, não apenas por um instante. O callback na transição para ocioso reutiliza a autoridade única de estado, sem polling nem estado paralelo.

### Decisão 5: Rótulo "Data de referência" oculto até o release

**Escolha**: o rótulo "Data de referência" é criado sem `pack`; `StartupGateMixin.remover_escudo` chama `_mostrar_data_referencia`, que o insere antes da entrada de data no release.

**Alternativas**: manter o rótulo visível e confiar apenas na cobertura do escudo.

**Razão**: em ambientes que pintam a janela durante a construção, o rótulo podia aparecer mesmo sob o escudo; nascer oculto garante que ele só exista visualmente quando a aplicação está pronta.

## Risks / Trade-offs

- **[Risco]** A mensagem atrasar a percepção de "tela cinza" em vez de melhorá-la → **Mitigação**: texto curto e centralizado, deixando claro que a aplicação está inicializando.
- **[Risco]** Um popup auxiliar escapar se uma operação reabilitar a entrada de data antes da liberação do escudo → **Mitigação**: a entrada só é restaurada por `presenter.exit()` na liberação do gate; o cenário de popups no spec documenta o contrato.
- **[Trade-off]** Um `tk.Label` a mais na árvore de widgets → **Benefício**: indicação explícita de espera durante o bloqueio.

## Migration Plan

1. Adicionar a mensagem ao `colocar_escudo` e reafirmar o empilhamento.
2. Atualizar os testes de UI do escudo (presença da mensagem e cobertura do rótulo de data), sem aumentar o contador do orçamento de testes de UI (reaproveitar testes existentes).
3. Rodar a suíte de apresentação e os guardrails de testes de UI e fronteiras. Rollback = reverter o commit (sem migração de dados).
