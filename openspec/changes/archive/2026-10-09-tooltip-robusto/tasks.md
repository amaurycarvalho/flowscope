## 1. Endurecimento da classe

- [x] 1.1 Em `widgets/tooltip.py`, fazer `_enter` cancelar um `_after_id` pendente antes de reagendar; verificar com teste unitário que dois `<Enter>` sem `<Leave>` resultam em uma única janela
- [x] 1.2 Fazer `_show` zerar `_after_id` e destruir `_tip_window` existente antes de criar a nova; verificar com teste que não resta janela órfã após `Enter`, `Enter`, `Leave`
- [x] 1.3 Em `_leave`, proteger `after_cancel` contra `tk.TclError`; verificar com teste que a saída durante o atraso não exibe a dica

## 2. Testes

- [x] 2.1 Adicionar testes do ciclo de vida do `ToolTip` (headless, sem `needs_display`, para respeitar o teto de testes de UI) em `tests/test_presentation`; verificar com `python -m pytest tests/test_presentation/test_tooltip.py`

## 3. Verificação integrada

- [x] 3.1 Executar `make test` (cobertura ≥ 85%) e `make lint` sem erros
- [x] 3.2 Confirmar manualmente que hover, clique e troca de modelo/configuração não deixam tooltips presos na tela

## 4. Cobertura de tooltips nos botões

- [x] 4.1 Adicionar dica ao botão de atalho no desktop e ao botão de parada em `app_layout.py`
- [x] 4.2 Adicionar dicas a "Atualizar", "Abrir" e "Resumir pendentes" em `charts/noticias_panel.py`
- [x] 4.3 Adicionar dicas a "Atualizar", "Abrir documento" e "Resumir pendentes" em `charts/document_tree_panel.py`
- [x] 4.4 Adicionar dicas a "Copiar chat", "Limpar", "Enviar" e "Cancelar" em `chat/chat_panel.py`
- [x] 4.5 Adicionar dicas a "Salvar", "Cancelar" e "Testar" em `llm/config_dialog.py`
- [x] 4.6 Adicionar dicas aos botões do GitHub, do log e da release em `widgets/about_panel.py`
- [x] 4.7 Rodar `make lint` e `make complexity` sem erros
- [x] 4.8 Verificar manualmente que todos os botões exibem a dica esperada (a cargo do usuário)
