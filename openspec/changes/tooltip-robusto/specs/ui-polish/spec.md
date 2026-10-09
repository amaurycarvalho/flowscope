## ADDED Requirements

### Requirement: Ciclo de vida dos tooltips

Um tooltip DEVE manter no máximo uma janela viva por instância. Ao exibir uma dica, qualquer janela anterior da mesma instância DEVE ser destruída antes de a nova ser criada; ao agendar a exibição, um agendamento pendente anterior DEVE ser cancelado, de modo que exista no máximo um agendamento pendente. Nenhuma janela de tooltip DEVE permanecer visível após o ponteiro sair do widget associado nem após um clique no widget, mesmo que eventos de entrada se repitam sem uma saída intermediária.

#### Scenario: Entradas repetidas sem saída não deixam janela órfã
- **WHEN** o widget associado recebe duas entradas do ponteiro sem uma saída entre elas
- **THEN** o sistema DEVE exibir apenas uma janela de tooltip e não DEVE deixar nenhuma janela órfã

#### Scenario: Sair do widget oculta a janela
- **WHEN** o ponteiro sai do widget associado após a dica estar visível
- **THEN** a janela de tooltip DEVE ser destruída

#### Scenario: Clique oculta a janela
- **WHEN** o usuário clica no widget associado após a dica estar visível
- **THEN** a janela de tooltip DEVE ser destruída

#### Scenario: Saída durante o atraso não exibe a dica
- **WHEN** o ponteiro sai do widget antes de decorrido o atraso de exibição
- **THEN** o agendamento DEVE ser cancelado e a dica NÃO DEVE ser exibida
