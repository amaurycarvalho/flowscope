## Why

A extração de texto de PDF hoje usa um `except Exception` genérico que devolve string vazia e, em seguida, `preparar_texto` grava o marcador de ausência de forma **permanente**. Assim, uma falha transitória do `pypdf` (dependência ausente, limite de processamento, arquivo ainda incompleto) vira "documento sem texto" para sempre, um PDF protegido por senha é descartado sem tentativa de recuperação e um texto extraído parcialmente (uma página ilegível) é tratado como completo. Além disso, a lógica de extração está duplicada em dois módulos e o marcador de ausência em dois, com risco de divergência.

## What Changes

- Extrator de PDF único e resiliente na camada de aplicação, com resultado tipado (`OK`, `PARCIAL`, `SEM_TEXTO`, `FALHA`, `PROTEGIDO`) e **tolerância por página** (texto parcial é preservado quando uma página falha).
- Tentativa automática de `decrypt("")` para PDFs criptografados antes de marcá-los como protegidos.
- Extração autenticada opcional por senha, para o fluxo interativo.
- **Semântica de cache**: apenas resultados definitivos (`OK` completo e `SEM_TEXTO`) são persistidos; `PARCIAL`, `FALHA` e `PROTEGIDO` NÃO são gravados, permitindo nova tentativa.
- **Diálogo de senha** no preview interativo, tanto para **Documentos** quanto para o **documento vinculado das Notícias** (CVM RAD/FNET): quando o PDF está protegido e não abre com senha vazia, o sistema pede a senha e tenta de novo; o texto obtido é gravado no cache e a senha nunca é persistida. O limite de tentativas é **3 por documento/seleção**, parametrizável. O fluxo não interativo ("Resumir pendentes") nunca abre diálogo.
- **Texto parcial anotado e retentado automaticamente**: no preview, um resultado parcial exibe uma anotação indicando as páginas não extraídas; o texto parcial não é cacheado nem resumido e a extração é retentada automaticamente quando o documento é selecionado/clicado de novo ou incluído em "Resumir pendentes".
- Unificação da extração duplicada: `infrastructure/b3/bdr/text.extrair_texto` passa a delegar ao extrator único, mantendo a assinatura `bytes -> str`.
- Unificação do marcador de ausência (`SEM_TEXTO`/`tem_texto`) em `domain/documents/texto.py`, com re-export para os importadores atuais.

## Capabilities

### New Capabilities
- `extracao-texto-pdf`: extração resiliente de texto de PDF com status tipado (`OK`/`PARCIAL`/`SEM_TEXTO`/`FALHA`/`PROTEGIDO`), tolerância por página, tentativa de senha vazia e autenticação opcional por senha.

### Modified Capabilities
- `documento-texto-cache`: passa a não persistir resultado parcial, de falha ou protegido, permitindo nova tentativa; só persiste texto completo (`OK`) ou ausência definitiva (`SEM_TEXTO`).
- `documentos-ticker-panel`: a pré-visualização passa a solicitar senha em PDF protegido (até 3 tentativas), anotar texto parcial e retentá-lo automaticamente ao re-selecionar o documento ou ao processar os pendentes.
- `noticias-panel`: a pré-visualização do documento vinculado passa a solicitar senha em PDF protegido (até 3 tentativas), anotar texto parcial e retentá-lo automaticamente ao re-selecionar a notícia ou ao processar os pendentes.

## Impact

- Código: `application/document_preview.py`, `infrastructure/b3/bdr/text.py`, `infrastructure/b3/noticias_vinculo.py`, `presentation/gui/charts/document_flow_mixin.py`, `presentation/gui/charts/document_tree_panel.py`, `presentation/gui/charts/noticias_panel.py`, `presentation/gui/app_wiring.py`, `domain/documents/texto.py`.
- Testes: `test_document_preview`, `test_bdr`, `test_document_flow`, `test_document_tree_panel`, `test_noticias_panel`, `test_noticias_vinculo`, além de novos testes de PDF criptografado, falha por página, anotação/retry de parcial e limite de tentativas.
- Sem novas dependências (`pypdf>=4` já é base). Sem mudança na porta `DocumentTextStore` nem no schema do cache.
- `llm-chat-rag` (task 4.2) passa a ter um único ponto de extração para reusar.
