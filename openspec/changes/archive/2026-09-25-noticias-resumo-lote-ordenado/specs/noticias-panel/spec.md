## ADDED Requirements

### Requirement: Ordem do resumo em lote das notícias

Ao acionar "Resumir pendentes" na sub-aba "Notícias", o sistema DEVE processar os itens sem `long_summary` agrupados pela categoria de topo na ordem "Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição de Ações" e "Geral" e, dentro de cada grupo, da notícia mais recente para a mais antiga segundo a data de publicação. Datas ausentes ou empatadas DEVEM ter desempate determinista, de modo que a ordem do lote seja estável entre execuções.

#### Scenario: Grupos processados na ordem definida
- **WHEN** há notícias pendentes em mais de uma categoria de topo
- **THEN** o lote DEVE concluir todos os pendentes de "Censuras Públicas" antes de "Condições Excepcionais", depois "Programas de Aquisição de Ações" e, por último, "Geral"

#### Scenario: Notícias mais recentes primeiro no grupo
- **WHEN** um grupo tem notícias pendentes publicadas em datas distintas
- **THEN** os resumos DEVEM ser gerados da data de publicação mais recente para a mais antiga

#### Scenario: Data ausente ou empatada tem ordem estável
- **WHEN** duas notícias do mesmo grupo têm a mesma data de publicação ou data ausente
- **THEN** a ordem entre elas DEVE ser determinista e repetível entre execuções

### Requirement: Persistência imediata do resumo em lote das notícias

Cada resumo gerado no lote das notícias DEVE ser gravado no cache persistente imediatamente após a sua geração, antes de processar a próxima notícia, de modo que uma interrupção — cancelamento, fechamento do aplicativo ou falha — preserve todos os resumos já gerados e perca no máximo a notícia em processamento. Gravações concorrentes entre o lote e a geração individual de resumo NÃO DEVEM perder nenhum resumo já gravado.

#### Scenario: Persistência imediata por notícia
- **WHEN** o lote gera o resumo de uma notícia e avança para a próxima
- **THEN** o resumo da notícia anterior já DEVE estar gravado no cache persistente, antes da geração da próxima

#### Scenario: Interrupção preserva os resumos já gerados
- **WHEN** o lote é cancelado, o aplicativo é fechado ou falha após gerar resumos de algumas notícias
- **THEN** os resumos já gerados DEVEM estar gravados no cache persistente

#### Scenario: Gravação concorrente não perde resumos
- **WHEN** o lote e a geração individual de resumo gravam resumos do mesmo escopo de notícias em paralelo
- **THEN** nenhum resumo já gravado DEVE ser perdido
