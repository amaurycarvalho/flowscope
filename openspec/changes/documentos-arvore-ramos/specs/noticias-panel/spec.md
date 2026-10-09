## ADDED Requirements

### Requirement: Remontagem da árvore de notícias após o lote de resumos

Ao término do processamento de "Resumir pendentes" na sub-aba "Notícias" — conclusão ou interrupção —, o sistema DEVE remontar a árvore a partir do cache atualizado, refletindo os novos resumos, fora da thread da interface, e preservando o item selecionado quando ele ainda existir.

#### Scenario: Árvore remontada ao término do lote
- **WHEN** o lote de resumos das notícias termina
- **THEN** a árvore DEVE ser remontada a partir do cache atualizado, refletindo os novos resumos

#### Scenario: Seleção preservada
- **WHEN** o lote termina e o item selecionado continua no catálogo
- **THEN** o sistema DEVE manter o item selecionado e reexibir o seu conteúdo
