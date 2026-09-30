## MODIFIED Requirements

### Requirement: Bloqueio de entrada durante a inicialização

O sistema DEVE bloquear toda a entrada do usuário — botões, abas de notebook, painéis e atalhos globais — desde o início da construção da janela até que a inicialização em background conclua. O bloqueio DEVE valer para qualquer widget, independentemente de o toolkit oferecer ou não estado desabilitado para abas, e NÃO DEVE depender de o painel inicial expor seus botões. O estado ocupado (controles e cursor) DEVE ser governado pela autoridade única de estado, que também determina o fim da inicialização: o escudo DEVE ser removido quando a autoridade voltar a ociosa (todas as operações da carga inicial terminarem), com um release de segurança caso a restauração inicial de abas/painéis não execute.

O escudo de bloqueio DEVE ser visível e apresentar, dentro dele, uma mensagem informando que a aplicação está inicializando, de modo que o usuário saiba aguardar. O escudo DEVE ser colocado antes de construir a barra superior e os painéis, para que qualquer pintura da janela durante a inicialização já saia coberta, e DEVE cobrir toda a extensão da janela — incluindo a barra superior com o rótulo "Data de referência", a entrada de data, os botões e os comboboxes. O rótulo "Data de referência" DEVE nascer oculto e só ser exibido após o escudo ser removido. Enquanto o escudo estiver ativo, nenhum popup auxiliar associado a controles da janela (por exemplo, o tooltip da data ou o calendário do `DateEntry`) DEVE ser exibido acima do escudo.

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

#### Scenario: Mensagem de espera exibida durante a inicialização

- **WHEN** o bloqueio de inicialização está ativo
- **THEN** o escudo DEVE estar visível e exibir uma mensagem informando que a aplicação está inicializando

#### Scenario: Escudo cobre a barra superior de data

- **WHEN** o bloqueio de inicialização está ativo e o ponteiro está sobre o rótulo "Data de referência" ou sobre a entrada de data
- **THEN** o widget sob o ponteiro DEVE ser o escudo, e não o rótulo nem a entrada de data

#### Scenario: Rótulo de data oculto até o release

- **WHEN** o bloqueio de inicialização está ativo
- **THEN** o rótulo "Data de referência" NÃO DEVE estar exibido, passando a ser exibido somente após o escudo ser removido

#### Scenario: Popups auxiliares não aparecem sobre o escudo

- **WHEN** o bloqueio de inicialização está ativo e o usuário interage com a entrada de data
- **THEN** o tooltip da data e o calendário do `DateEntry` NÃO DEVEM ser exibidos acima do escudo

#### Scenario: Liberação quando a inicialização em background conclui

- **WHEN** a restauração inicial de abas/painéis conclui e não há mais operações de carga em background
- **THEN** o bloqueio DEVE ser removido e os controles, abas, atalhos e cursor DEVEM voltar aos estados anteriores

#### Scenario: Escudo permanece enquanto a carga inicial roda

- **WHEN** a restauração inicial de abas/painéis conclui, mas ainda há operações de carga em background
- **THEN** o escudo DEVE permanecer exibido até a última operação terminar

#### Scenario: Liberação após a restauração inicial

- **WHEN** a restauração inicial de abas/painéis conclui e não há mais operações de carga em background
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
