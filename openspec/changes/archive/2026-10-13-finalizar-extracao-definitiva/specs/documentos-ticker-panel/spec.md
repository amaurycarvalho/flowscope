## ADDED Requirements

### Requirement: Confirmação de finalização ao término do lote de documentos

Ao término normal do lote de resumos dos documentos — não cancelado, não interrompido por erro e não abortado por cota da LLM —, quando restarem documentos de extração não conclusiva (`PARCIAL`, `FALHA` ou `PROTEGIDO`), o sistema DEVE exibir, na thread do Tk e após a remontagem da árvore, a confirmação descrita na capability `finalizacao-extracao-definitiva`: informar a quantidade e perguntar se o usuário quer tentar novamente e, em caso negativo, se quer marcar os documentos como definitivos. O lote NÃO DEVE solicitar senha durante o processamento; a pré-coleta de senha dos documentos protegidos DEVE ocorrer na thread do Tk apenas quando o usuário confirma "tentar novamente". Documentos protegidos seguem a rota manual de senha e, quando a senha não for informada, DEVEM permanecer pendentes. A confirmação NÃO DEVE ser exibida quando o ticker apresentado tiver mudado.

#### Scenario: Confirmação ao término com documentos não conclusivos
- **WHEN** o lote de documentos termina normalmente e restam documentos `PARCIAL`, `FALHA` ou `PROTEGIDO`
- **THEN** o sistema DEVE informar a quantidade e perguntar se o usuário quer tentar novamente

#### Scenario: Recusa leva à pergunta de finalização
- **WHEN** o usuário recusa tentar novamente
- **THEN** o sistema DEVE perguntar se deseja marcar os documentos como definitivos

#### Scenario: Sem confirmação em término anormal
- **WHEN** o lote de documentos é cancelado, interrompido por erro, abortado por cota da LLM, ou o ticker apresentado mudou
- **THEN** a confirmação NÃO DEVE ser exibida

#### Scenario: Pré-coleta de senha no reprocessamento
- **WHEN** o usuário confirma tentar novamente e a lista contém documento protegido
- **THEN** o sistema DEVE solicitar a senha antes de iniciar o reprocessamento, mantendo pendente o documento cuja senha não for informada

#### Scenario: Documentos marcados como definitivos saem dos pendentes
- **WHEN** o usuário marca os documentos como definitivos
- **THEN** eles DEVEM sair dos pendentes e não DEVEM ser reextraídos pelos lotes seguintes
