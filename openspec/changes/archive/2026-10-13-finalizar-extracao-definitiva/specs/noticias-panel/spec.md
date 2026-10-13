## ADDED Requirements

### Requirement: Confirmação de finalização ao término do lote de notícias

Ao término normal do lote de resumos das notícias — não cancelado, não interrompido por erro e não abortado por cota da LLM —, quando restarem itens de extração não conclusiva (`PARCIAL`, `FALHA` ou `PROTEGIDO`), o sistema DEVE exibir, na thread do Tk e após a remontagem da árvore, a confirmação descrita na capability `finalizacao-extracao-definitiva`: informar a quantidade e perguntar se o usuário quer tentar novamente e, em caso negativo, se quer marcar os itens como definitivos. Itens de notícia "Geral" cujo corpo é um apontador para documento vinculado não resolvido NÃO DEVEM integrar a lista de extração não conclusiva. Um documento vinculado protegido por senha É um item `PROTEGIDO` e segue a rota manual de senha: a pré-coleta de senha DEVE ocorrer na thread do Tk apenas quando o usuário confirma "tentar novamente", e sem senha informada o item DEVE permanecer pendente. A confirmação NÃO DEVE ser exibida quando o período apresentado tiver mudado.

#### Scenario: Confirmação ao término com itens não conclusivos
- **WHEN** o lote de notícias termina normalmente e restam itens `PARCIAL`, `FALHA` ou `PROTEGIDO`
- **THEN** o sistema DEVE informar a quantidade e perguntar se o usuário quer tentar novamente

#### Scenario: Recusa leva à pergunta de finalização
- **WHEN** o usuário recusa tentar novamente
- **THEN** o sistema DEVE perguntar se deseja marcar os itens como definitivos

#### Scenario: Apontador não resolvido fica fora da lista
- **WHEN** uma notícia "Geral" tem o corpo como apontador para documento vinculado não resolvido
- **THEN** ela NÃO DEVE integrar a lista de extração não conclusiva da confirmação

#### Scenario: Sem confirmação em término anormal
- **WHEN** o lote de notícias é cancelado, interrompido por erro, abortado por cota da LLM, ou o período apresentado mudou
- **THEN** a confirmação NÃO DEVE ser exibida

#### Scenario: Pré-coleta de senha no reprocessamento
- **WHEN** o usuário confirma tentar novamente e a lista contém item protegido
- **THEN** o sistema DEVE solicitar a senha antes de iniciar o reprocessamento, mantendo pendente o item cuja senha não for informada

#### Scenario: Itens marcados como definitivos saem dos pendentes
- **WHEN** o usuário marca os itens como definitivos
- **THEN** eles DEVEM sair dos pendentes e não DEVEM ser reprocessados pelos lotes seguintes
