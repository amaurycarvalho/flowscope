## 1. Escudo com mensagem e cobertura

- [x] 1.1 Adicionar ao `colocar_escudo` (`startup_gate.py`) um `tk.Label` centralizado dentro do frame com a mensagem de espera ("Aguarde a inicialização da aplicação…"), usando `place(relx=0.5, rely=0.5, anchor="center")`; verificar com teste de UI que o rótulo existe e contém a mensagem enquanto o escudo está ativo
- [x] 1.2 Reafirmar o empilhamento do escudo sobre a barra superior (`escudo.lift()` após a colocação e dimensões relativas ao toplevel) e verificar com teste de UI herdando o host existente que `winfo_containing` sobre o rótulo "Data de referência" e sobre a `DateEntry` retorna o escudo enquanto ativo
- [x] 1.3 Garantir que `remover_escudo` destrói também o rótulo/mensagem junto do frame; verificar no teste de UI existente que `_escudo` volta a `None` e não sobra widget órfão

## 2. Contratos e orçamento

- [x] 2.1 Estender os testes de UI existentes em `tests/test_presentation/test_startup_gate.py` (classe `TestEscudoUI`, já decorada com `@needs_display`) em vez de criar nova declaração decorada, mantendo o contador do orçamento de testes de UI inalterado; verificar com `pytest tests/architecture/test_ui_test_budget.py`
- [x] 2.2 Confirmar que os cenários "Mensagem de espera exibida", "Escudo cobre a barra superior de data" e "Popups auxiliares não aparecem sobre o escudo" são cobertos (UI/headless conforme o caso) e que o `DateEntry` permanece desabilitado durante o gate; verificar com `pytest tests/test_presentation/test_startup_gate.py`

## 3. Liberação na ociosidade e rótulo de data

- [x] 3.1 Colocar o escudo no início de `FlowScopeGUI.__init__` (antes de `_build_top_bar`/painéis) e reerguê-lo ao fim de cada etapa de construção, para a primeira pintura já sair coberta; verificar que a janela mapeada mostra o escudo cobrindo a barra superior
- [x] 3.2 Inverter a ordem em `StartupGate.iniciar` (escudo antes de `enter`) e adicionar `FlowScopePresenter.ao_ficar_ocioso`, registrando a remoção do escudo na transição para ocioso; verificar com testes headless que o escudo permanece enquanto há job ativo e some quando o último termina
- [x] 3.3 Manter o release de segurança por timeout cobrindo o caso de `_restore_tabs` não executar, sem remover o escudo enquanto a carga inicial ainda roda; verificar com os testes de `TestStartupGateMixin`
- [x] 3.4 Criar o rótulo "Data de referência" oculto (sem `pack`) e exibi-lo, antes da entrada de data, apenas quando o escudo for removido; verificar que o rótulo não está mapeado durante o gate e passa a mapeado após o release

## 4. Verificação final

- [x] 4.1 Validar o change com `openspec validate escudo-inicializacao-mensagem` (convenção do projeto; specs em português emitem apenas o aviso RFC 2119 esperado, sem erro)
- [x] 4.2 Rodar a suíte de apresentação e os guardrails de testes de UI, complexidade e fronteiras, confirmando que não há vazamento de hourglass e que a contagem de `@needs_display` não aumentou
