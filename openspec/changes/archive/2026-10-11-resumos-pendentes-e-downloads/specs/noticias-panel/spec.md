## MODIFIED Requirements

### Requirement: Ordem do resumo em lote das notícias

Ao acionar "Resumir pendentes" na sub-aba "Notícias", o sistema DEVE processar os itens que necessitam de resumo, agrupados pela categoria de topo na ordem "Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição de Ações" e "Geral" e, dentro de cada grupo, da notícia mais recente para a mais antiga segundo a data de publicação. Um item necessita de resumo quando não tem `long_summary` íntegro, considerando desatualizado o resumo persistido que não termina em pontuação final (mesma regra de regeneração aplicada à sub-aba "Documentos"). Um item cuja ausência de texto foi conclusivamente determinada e persistida (corpo apenas em branco ou marcador de ausência de texto) NÃO DEVE ser considerado pendente; um item cujo corpo é um apontador para documento vinculado ainda não resolvido DEVE permanecer pendente para nova tentativa. Datas ausentes ou empatadas DEVEM ter desempate determinista, de modo que a ordem do lote seja estável entre execuções.

#### Scenario: Grupos processados na ordem definida
- **WHEN** há notícias pendentes em mais de uma categoria de topo
- **THEN** o lote DEVE concluir todos os pendentes de "Censuras Públicas" antes de "Condições Excepcionais", depois "Programas de Aquisição de Ações" e, por último, "Geral"

#### Scenario: Notícias mais recentes primeiro no grupo
- **WHEN** um grupo tem notícias pendentes publicadas em datas distintas
- **THEN** os resumos DEVEM ser gerados da data de publicação mais recente para a mais antiga

#### Scenario: Data ausente ou empatada tem ordem estável
- **WHEN** duas notícias do mesmo grupo têm a mesma data de publicação ou data ausente
- **THEN** a ordem entre elas DEVE ser determinista e repetível entre execuções

#### Scenario: Resumo truncado é regerado
- **WHEN** o lote processa uma notícia cujo `long_summary` persistido não termina em pontuação final
- **THEN** o resumo DEVE ser refeito e regravado, como no lote de documentos

#### Scenario: Resumo íntegro não é regerado
- **WHEN** o `long_summary` persistido termina em pontuação final
- **THEN** a notícia NÃO DEVE ser reprocessada pelo lote por esse critério

#### Scenario: Item sem texto conclusivo não é pendente
- **WHEN** o corpo indexado de uma notícia não produz texto algum (apenas espaços em branco) e não há resumo
- **THEN** a notícia NÃO DEVE integrar a lista de pendentes do lote

#### Scenario: Apontador não resolvido permanece pendente
- **WHEN** o corpo de uma notícia "Geral" é um apontador para documento vinculado ainda não resolvido e não há resumo
- **THEN** a notícia DEVE permanecer na lista de pendentes para nova tentativa
