## Purpose

Descreve o fluxo compartilhado pelas sub-abas "Documentos" e "Notícias", ao término do lote "Resumir pendentes", que oferece reprocessar ou marcar como definitivos os itens de extração não conclusiva, persistindo o texto definitivo com a nota de limitação e gerando o resumo correspondente.

## ADDED Requirements

### Requirement: Detecção de itens de extração não conclusiva ao término do lote

Ao término normal do lote, o sistema DEVE identificar, entre os itens processados, os de extração não conclusiva: `PARCIAL` (texto parcial), `FALHA` (erro crítico, sem texto) e `PROTEGIDO` (PDF protegido por senha). Itens em `SEM_TEXTO` (ausência definitiva de texto) e itens de notícia cujo corpo é um apontador para documento vinculado não resolvido NÃO DEVEM ser considerados de extração não conclusiva.

#### Scenario: Itens parciais, com falha e protegidos são reportados
- **WHEN** o lote termina e restam itens em `PARCIAL`, `FALHA` ou `PROTEGIDO`
- **THEN** o sistema DEVE considerá-los itens de extração não conclusiva

#### Scenario: Ausência definitiva de texto fica de fora
- **WHEN** um item foi lido sem produzir texto (`SEM_TEXTO`) e persistido como ausência
- **THEN** ele NÃO DEVE ser considerado item de extração não conclusiva

#### Scenario: Apontador não resolvido de notícia fica de fora
- **WHEN** o corpo de uma notícia "Geral" é um apontador para documento vinculado ainda não resolvido
- **THEN** ele NÃO DEVE ser considerado item de extração não conclusiva

### Requirement: Confirmação de reprocessamento e finalização

Quando houver itens de extração não conclusiva ao término do lote, o sistema DEVE informar a quantidade e perguntar ao usuário se deseja tentar reprocessá-los; se o usuário recusar, DEVE perguntar se deseja marcá-los como definitivos; se também recusar, DEVE encerrar sem alterar os itens. A pergunta de finalização DEVE alcançar apenas itens efetivamente processados no lote e classificados como não conclusivos; itens pendentes ainda não processados NÃO DEVEM ser marcados como definitivos. A confirmação NÃO DEVE ser exibida quando o lote for cancelado pelo usuário, interrompido por erro fatal, abortado por cota da LLM, ou quando o escopo apresentado (ticker de documentos ou período de notícias) tiver mudado. Um encerramento por timeout/inatividade DEVE ser registrado no log e DEVE exibir o fluxo de reprocessamento; nesse caso, o retry DEVE reconsiderar o lote interrompido (itens que permanecem pendentes), sem oferecer finalização dos não processados. Ao confirmar o reprocessamento, os timeouts correntes (orçamento de extração e limite de inatividade) DEVEM crescer 30% em memória, sempre relativos ao valor em memória anterior, sem persistir nem marcar itens como definitivos.

#### Scenario: Confirmação ao término com não conclusivos
- **WHEN** o lote termina normalmente e restam itens de extração não conclusiva
- **THEN** o sistema DEVE informar a quantidade e perguntar se o usuário quer tentar reprocessá-los

#### Scenario: Recusa do reprocessamento leva à finalização
- **WHEN** o usuário recusa reprocessar
- **THEN** o sistema DEVE perguntar se deseja marcar os itens como definitivos

#### Scenario: Dupla recusa encerra sem alterações
- **WHEN** o usuário recusa reprocessar e recusa marcar como definitivo
- **THEN** o processamento DEVE encerrar sem alterar os itens

#### Scenario: Sem confirmação em término anormal
- **WHEN** o lote é cancelado pelo usuário, interrompido por erro fatal, abortado por cota da LLM, ou o escopo apresentado mudou
- **THEN** a confirmação NÃO DEVE ser exibida

#### Scenario: Timeout é registrado e oferece retry
- **WHEN** o lote é encerrado por timeout/inatividade
- **THEN** o evento DEVE ser registrado no log e o fluxo de reprocessamento DEVE ser exibido para reconsiderar o lote interrompido

#### Scenario: Retry confirmado escala os timeouts em 30%
- **WHEN** o usuário confirma reprocessar após um timeout
- **THEN** os timeouts correntes DEVEM crescer 30% em memória, relativos ao valor anterior, sem persistência

#### Scenario: Itens não processados ficam fora da finalização
- **WHEN** o lote é interrompido antes de processar alguns itens
- **THEN** os itens não processados NÃO DEVEM ser oferecidos para marcação como definitivos, embora possam ser reprocessados

### Requirement: Reprocessamento interativo dos itens não conclusivos

Ao confirmar o reprocessamento, o sistema DEVE reprocessar apenas os itens da lista. Para os itens `PROTEGIDO`, a senha DEVE ser pré-coletada junto ao usuário (rota manual) antes de iniciar o reprocessamento; itens cuja senha não for informada, ou cuja extração permanecer não conclusiva, DEVEM permanecer pendentes e elegíveis à confirmação seguinte. A pré-coleta DEVE ocorrer na thread da interface e o lote NÃO DEVE solicitar senha durante o processamento.

#### Scenario: Reprocessa apenas a lista
- **WHEN** o usuário confirma reprocessar
- **THEN** o sistema DEVE reprocessar apenas os itens de extração não conclusiva listados

#### Scenario: Pré-coleta de senha dos protegidos
- **WHEN** a lista contém item `PROTEGIDO` e o usuário confirma reprocessar
- **THEN** o sistema DEVE solicitar a senha do item antes de iniciar o reprocessamento

#### Scenario: Senha ausente mantém pendente
- **WHEN** o usuário não informa a senha de um item protegido ou a extração segue não conclusiva
- **THEN** o item DEVE permanecer pendente e reaparecer na confirmação seguinte

#### Scenario: Lote não pede senha durante a execução
- **WHEN** o reprocessamento está em andamento
- **THEN** o lote NÃO DEVE solicitar senha durante o processamento

### Requirement: Finalização definitiva dos itens não conclusivos

Ao confirmar marcar como definitivo, o sistema DEVE, fora da thread da interface, por item: em `PARCIAL`, persistir o texto parcial acrescido da nota de extração parcial e gerar o resumo via LLM; em `FALHA`, persistir apenas a nota de erro crítico de extração e gerar resumo determinístico; em `PROTEGIDO`, persistir apenas a nota de PDF protegido por senha e gerar resumo determinístico. Após a finalização, o item DEVE sair dos pendentes e não DEVE ser reextraído pelo lote. A avaliação de guidance do Relatório Gerencial DEVE ocorrer quando o item for da categoria `Relatorio` e houver texto.

#### Scenario: Parcial finalizado gera resumo via LLM
- **WHEN** um item `PARCIAL` é marcado como definitivo
- **THEN** o sistema DEVE persistir o texto parcial com a nota e gerar o resumo pela LLM

#### Scenario: Falha finalizada gera resumo determinístico
- **WHEN** um item `FALHA` é marcado como definitivo
- **THEN** o sistema DEVE persistir apenas a nota de erro crítico e gerar o resumo sem chamar a LLM

#### Scenario: Protegido finalizado gera resumo determinístico
- **WHEN** um item `PROTEGIDO` é marcado como definitivo
- **THEN** o sistema DEVE persistir apenas a nota de PDF protegido e gerar o resumo sem chamar a LLM

#### Scenario: Item finalizado não é reextraído
- **WHEN** um item foi marcado como definitivo
- **THEN** ele NÃO DEVE integrar os pendentes nem ser reextraído em lotes seguintes

### Requirement: Nota de extração embutida no texto

A nota de extração DEVE ser embutida no próprio texto persistido do item — ao final do texto parcial ou como único conteúdo quando não houver texto — instruindo que a limitação (extração parcial, erro crítico ou proteção por senha) seja citada nos resumos. A nota DEVE distinguir os três casos e, no caso parcial, indicar a quantidade de páginas não extraídas. Uma vez persistido o texto definitivo, a leitura do cache DEVE reutilizá-lo sem reconverter o arquivo.

#### Scenario: Nota do parcial informa a quantidade de páginas
- **WHEN** um item `PARCIAL` é finalizado
- **THEN** a nota embutida DEVE indicar que o texto foi extraído parcialmente e a quantidade de páginas não extraídas

#### Scenario: Nota de falha sem texto
- **WHEN** um item `FALHA` é finalizado
- **THEN** o texto persistido DEVE conter apenas a nota de erro crítico de extração

#### Scenario: Leitura reutiliza o texto finalizado
- **WHEN** o item finalizado é lido novamente
- **THEN** o texto persistido DEVE ser reutilizado, sem nova conversão

### Requirement: Resumo determinístico para extração sem texto

Para `FALHA` e `PROTEGIDO`, o resumo DEVE ser determinado sem chamada à LLM, com uma mensagem fixa que informe a impossibilidade de extrair o texto e de resumi-lo, terminando em pontuação final para ser considerada íntegra. Para `PARCIAL`, o resumo DEVE ser gerado pela LLM a partir do texto parcial com a nota, e o resumo resultante DEVE mencionar a limitação da extração.

#### Scenario: Falha e protegido não chamam a LLM
- **WHEN** um item `FALHA` ou `PROTEGIDO` é finalizado
- **THEN** nenhuma chamada à LLM DEVE ser realizada e o resumo DEVE ser determinístico

#### Scenario: Resumo determinístico é íntegro
- **WHEN** um resumo determinístico é persistido
- **THEN** ele DEVE terminar em pontuação final e ser considerado íntegro

#### Scenario: Resumo do parcial cita a limitação
- **WHEN** um item `PARCIAL` é finalizado
- **THEN** o resumo gerado DEVE mencionar que o texto foi extraído parcialmente
