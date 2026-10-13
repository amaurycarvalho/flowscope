## Why

O lote "Resumir pendentes" (sub-abas "Documentos" e "Notícias") deixa pendentes os itens cuja extração não foi conclusiva — texto parcial, falha crítica de leitura e PDF protegido por senha. Esses itens são retentados indefinidamente a cada lote, mantendo o botão habilitado sem progresso, e nunca recebem resumo. O usuário não tem como aceitar o que foi extraído (ou a impossibilidade de extrair) como estado definitivo e encerrar o ciclo.

## What Changes

- Ao término do lote, quando restarem itens não conclusivos (parcial + falha + protegido), o sistema informa a quantidade e pergunta se o usuário quer tentá-los novamente; em caso negativo, pergunta se quer marcá-los como definitivos.
- "Tentar novamente" reprocessa apenas os itens da lista. Para os protegidos, a senha é pré-coletada (rota manual) antes do reprocessamento; sem senha informada, o item permanece pendente.
- "Marcar como definitivo" persiste o texto definitivo do item — `PARCIAL`: o texto parcial acrescido de uma nota; `FALHA`/`PROTEGIDO`: apenas a nota — e gera o resumo citando a limitação: via LLM no parcial e determinístico (sem LLM) na falha e no protegido. A partir daí o item sai dos pendentes e não é mais reextraído no lote.
- A nota de extração é embutida no próprio texto persistido, de modo que resumos futuros a citem (modifica o invariante do cache de texto, com exceção de finalização explícita).
- Escopo: extração parcial, falha crítica e PDF protegido. Ausência definitiva de texto (`SEM_TEXTO`) e apontador de notícia "Geral" não resolvido ficam fora.

## Capabilities

### New Capabilities
- `finalizacao-extracao-definitiva`: fluxo de confirmação ao término do lote (retry interativo com pré-coleta de senha + marcar como definitivo), montagem da nota de extração e resumo determinístico para extração não conclusiva, compartilhado pelas sub-abas "Documentos" e "Notícias".

### Modified Capabilities
- `documento-texto-cache`: exceção de finalização explícita — persistir texto parcial, de falha ou de PDF protegido (com a nota de extração) e deixar de retentá-los.
- `documentos-ticker-panel`: dispara a confirmação de finalização ao término do lote de documentos.
- `noticias-panel`: dispara a confirmação de finalização ao término do lote de notícias.

## Impact

- Apresentação: `src/flowscope/presentation/gui/app_resumos_actions.py`, `resumos_job.py`, `charts/document_flow_mixin.py`, `charts/document_tree_panel.py`, `charts/noticias_panel.py`.
- Contrato do job de lote passa a reportar os conjuntos de itens parciais, com falha e protegidos (hoje devolve só uma contagem).
- Persistência de texto (`documento-texto-cache`) e geração de resumo (caminho determinístico).
- Sem novas dependências externas.
