## Why

Tooltips da classe `ToolTip` às vezes ficam presos na tela até o usuário fechar a aplicação. Isso ocorre quando duas exibições são agendadas/disparadas antes de um `<Leave>`: `_enter` sobrescreve o `after` pendente sem cancelá-lo e `_show` sobrescreve `_tip_window` sem destruir o anterior, de modo que a janela antiga fica órfã e nada mais a destrói. O sintoma já foi reproduzido de forma determinística no nível da classe.

## What Changes

- Endurecer `widgets/tooltip.py` para que nunca haja mais de uma janela de tooltip viva por instância: cancelar o `after` pendente no `_enter`, destruir a janela existente no `_show`, zerar `_after_id` quando `_show` dispara e proteger `after_cancel` contra `TclError`.
- Estender a cobertura de tooltips: adicionar dicas descritivas a todos os botões da aplicação que ainda não as possuíam (barra superior, barra de status, painéis de Notícias/Documentos, chat, diálogo de configuração de I.A. e aba Sobre), reutilizando a classe `ToolTip` endurecida. Não altera os textos/aparência dos botões nem os tooltips já existentes.
- Adicionar testes unitários do ciclo de vida do `ToolTip` que comprovem que uma segunda exibição sem `_leave` não deixa janela órfã.

## Capabilities

### New Capabilities
<!-- Nenhuma. -->

### Modified Capabilities
- `ui-polish`: novo requisito sobre o ciclo de vida dos tooltips, garantindo que nenhuma janela de tooltip sobreviva sem um `<Leave>` correspondente; e novo requisito de cobertura, garantindo que todo botão da aplicação exponha um tooltip.

## Impact

- **Apresentação (endurecimento)**: `presentation/gui/widgets/tooltip.py` (única classe de comportamento afetada).
- **Apresentação (cobertura)**: pontos de uso que ganharam dica em `presentation/gui/app_layout.py`, `presentation/gui/charts/noticias_panel.py`, `presentation/gui/charts/document_tree_panel.py`, `presentation/gui/chat/chat_panel.py`, `presentation/gui/llm/config_dialog.py` e `presentation/gui/widgets/about_panel.py`.
- **Testes**: novos testes unitários do widget.
- **Sem dependências novas** e sem mudança de comportamento visível esperado além da correção do travamento e das novas dicas.
