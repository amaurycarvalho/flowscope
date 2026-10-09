## Why

Tooltips da classe `ToolTip` às vezes ficam presos na tela até o usuário fechar a aplicação. Isso ocorre quando duas exibições são agendadas/disparadas antes de um `<Leave>`: `_enter` sobrescreve o `after` pendente sem cancelá-lo e `_show` sobrescreve `_tip_window` sem destruir o anterior, de modo que a janela antiga fica órfã e nada mais a destrói. O sintoma já foi reproduzido de forma determinística no nível da classe.

## What Changes

- Endurecer `widgets/tooltip.py` para que nunca haja mais de uma janela de tooltip viva por instância: cancelar o `after` pendente no `_enter`, destruir a janela existente no `_show`, zerar `_after_id` quando `_show` dispara e proteger `after_cancel` contra `TclError`.
- Não altera textos, atraso, posicionamento, aparência nem os pontos de uso.
- Adicionar testes unitários do ciclo de vida do `ToolTip` que comprovem que uma segunda exibição sem `_leave` não deixa janela órfã.

## Capabilities

### New Capabilities
<!-- Nenhuma. -->

### Modified Capabilities
- `ui-polish`: novo requisito sobre o ciclo de vida dos tooltips, garantindo que nenhuma janela de tooltip sobreviva sem um `<Leave>` correspondente.

## Impact

- **Apresentação**: `presentation/gui/widgets/tooltip.py` (única classe afetada; todos os tooltips da aplicação se beneficiam).
- **Testes**: novos testes unitários do widget.
- **Sem dependências novas** e sem mudança de comportamento visível esperado além da correção do travamento.
