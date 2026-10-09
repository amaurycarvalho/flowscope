## 1. Endurecimento da classe

- [ ] 1.1 Em `widgets/tooltip.py`, fazer `_enter` cancelar um `_after_id` pendente antes de reagendar; verificar com teste unitário que dois `<Enter>` sem `<Leave>` resultam em uma única janela
- [ ] 1.2 Fazer `_show` zerar `_after_id` e destruir `_tip_window` existente antes de criar a nova; verificar com teste que não resta janela órfã após `Enter`, `Enter`, `Leave`
- [ ] 1.3 Em `_leave`, proteger `after_cancel` contra `tk.TclError`; verificar com teste que a saída durante o atraso não exibe a dica

## 2. Testes

- [ ] 2.1 Adicionar testes do ciclo de vida do `ToolTip` (marcados com `needs_display`) em `tests/test_presentation`; verificar com `python -m pytest tests/test_presentation -k tooltip` sob display (ex.: `xvfb-run -a python -m pytest ... -k tooltip`)

## 3. Verificação integrada

- [ ] 3.1 Executar `make test` (cobertura ≥ 85%) e `make lint` sem erros
- [ ] 3.2 Confirmar manualmente que hover, clique e troca de modelo/configuração não deixam tooltips presos na tela
