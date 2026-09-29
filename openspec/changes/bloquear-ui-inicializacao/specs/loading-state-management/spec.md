## ADDED Requirements

### Requirement: Bloqueio de entrada durante a inicialização

O sistema DEVE bloquear toda a entrada do usuário — botões, abas de notebook, painéis e atalhos globais — desde o fim da construção da janela (antes de o `mainloop` processar eventos) até que a restauração inicial de abas/painéis conclua. O bloqueio DEVE valer para qualquer widget, independentemente de o toolkit oferecer ou não estado desabilitado para abas, e NÃO DEVE depender de o painel inicial expor seus botões. O estado ocupado (controles e cursor) DEVE ser governado pela autoridade única de estado, e o bloqueio DEVE ser removido antes de restaurar os controles e o cursor, de modo que o snapshot de cursor não capture o próprio bloqueio.

#### Scenario: Janela mapeada não aceita interação durante a inicialização

- **WHEN** a janela já está mapeada e a construção inicial ainda está em andamento
- **THEN** cliques sobre botões, abas ou painéis NÃO DEVEM disparar nenhum handler

#### Scenario: Abas bloqueadas sem depender do toolkit

- **WHEN** o usuário tenta trocar de aba durante a inicialização
- **THEN** a troca NÃO DEVE ocorrer, ainda que o toolkit não suporte desabilitar abas individualmente

#### Scenario: Painel inicial sem `all_buttons` permanece bloqueado

- **WHEN** a aba inicial restaurada é "Chat AI" ou "Sobre", cujos botões não são cobertos pelo bloqueio global de botões
- **THEN** os controles dessa aba NÃO DEVEM aceitar interação durante a inicialização

#### Scenario: Atalhos globais bloqueados

- **WHEN** o usuário pressiona `F5`, `Return` ou `Ctrl+Shift+C` durante a inicialização
- **THEN** o atalho NÃO DEVE disparar a ação correspondente

#### Scenario: Liberação após a restauração inicial

- **WHEN** a restauração inicial de abas/painéis conclui
- **THEN** o bloqueio DEVE ser removido e os controles, abas, atalhos e cursor DEVEM voltar aos estados anteriores

#### Scenario: Cursor consistente sem vazamento

- **WHEN** a inicialização termina
- **THEN** o cursor de espera DEVE ser removido de todos os widgets, sem deixar hourglass preso, mesmo que cliques tenham sido enfileirados durante o bloqueio

#### Scenario: Erro na restauração inicial ainda libera o gate

- **WHEN** a restauração inicial de abas/painéis falha
- **THEN** o bloqueio DEVE ser removido e os controles DEVEM ser restaurados, sem prender a interface

#### Scenario: Estado ocupado contabilizado como uma operação

- **WHEN** o bloqueio de inicialização está ativo e outra operação em background é iniciada
- **THEN** a autoridade única DEVE contabilizar as operações e restaurar controles e cursor somente quando a última concluir
