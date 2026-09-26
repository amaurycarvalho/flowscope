## Why

A aba "Chat AI" monta o contexto da LLM dentro de `presentation`:
`chat_panel._montar_contexto` e os auxiliares de escalonamento
(`_preparar_texto`/`_confirmar_leitura`), a serialização de fundamentos
(`chat/fundamentos.py`), o bloco de conhecimento (`chat/conhecimento.py`), a
cascata de documentos (`chat/documentos.py`) e a fonte de notícias
(`chat/noticias.py`). Como consequência, a UI decide o que entra no prompt e
reinterpreta regras de recuperação/orçamento, e essas funções puras só são
testadas sob `tests/test_presentation`. Esta fatia move a montagem do contexto
para `application`, deixando o painel apenas exibir e orquestrar a thread.

## What Changes

- `chat/fundamentos.py` (`tickers_do_escopo`, `serializar_fundamentos`,
  `montar_contexto_fundamentos`, `ORIENTACAO_SEM_DADOS`) sai de `presentation`
  para `application/chat/`.
- `chat/conhecimento.py` passa a ser montado em `application/chat/`, com a
  montagem do bloco (cabeçalhos e ordem) na aplicação e os textos de interface
  (`TAB_CONTENT`, `APRESENTACAO`, `LICENCA`, `REPOSITORIO_URL`) fornecidos pela
  apresentação como entrada.
- `chat/documentos.py` (`CascataDocumentos`, `DocumentoEscopo`,
  `faixa_confirmacao`, faixas e tetos) sai para `application/chat/`.
- `chat/noticias.py` (`FonteNoticias`, `TITULO_FONTE`) sai para
  `application/chat/`.
- A extração de texto de documentos (`texto_preview`, `tem_texto`, `SEM_TEXTO`,
  `texto_de_html`, `texto_de_pdf`) sai de
  `presentation/gui/charts/document_preview.py` para
  `application/document_preview.py`: é extração/parsing, não desenho, e é
  consumida pela cascata e pela fonte de notícias sem acoplar `application` à
  apresentação.
- Criação de um montador de contexto em `application/chat/` (substituindo
  `chat_panel._montar_contexto`, `_preparar_fontes_adicionais`,
  `_preparar_texto` e `_confirmar_leitura`): reúne conhecimento, fundamentos,
  cascata de documentos e fontes adicionais em um `ContextoChat`, aplicando o
  escalonamento e o gate de confirmação (delegando o diálogo a um callback).
- `chat_panel.py` e `envio.py` passam a consumir o montador de `application` e
  mantêm apenas widget, sessão, thread/fila, cancelamento, cópia/limpeza e o
  diálogo de confirmação.
- Testes puros de contexto migram para `tests/test_application`; os testes de
  `tests/test_presentation` ficam restritos a wiring, estado de widget e
  thread/queue.
- Sem alteração da allowlist de fronteira: a fatia não importa `infrastructure`.

## Capabilities

### New Capabilities

### Modified Capabilities

Opta por não alterar specs (`skip_specs: true`): refatoração que preserva o
comportamento observável, implementando o contrato `layer-boundaries` do change
`clean-architecture-layering`.

## Impact

- **Depende de**: `add-layer-architecture-guardrails` (allowlist e teste de
  fronteira) e do padrão de view-model/contexto já aplicado em
  `refactor-documentos-layers`/`refactor-noticias-layers` e no
  `application/noticias/fonte_chat.py`.
- **Código movido**: `presentation/gui/chat/{fundamentos,conhecimento,documentos,noticias}.py`,
  a montagem de `chat_panel._montar_contexto`/auxiliares e
  `presentation/gui/charts/document_preview.py`.
- **Novos módulos/tipos**: `application/chat/` (contexto, fundamentos,
  conhecimento, documentos, notícias) e `application/document_preview.py`.
- **Testes**: `test_chat_fundamentos`, `test_chat_documentos`,
  `test_chat_conhecimento` e parte de `test_noticias_chat_context` migram para
  `tests/test_application`; `test_chat_panel`/`test_chat_integration` permanecem
  como testes de UI.
- **Sem alteração de comportamento**: o prompt enviado à LLM (seções, ordem,
  textos, orçamentos e chaves), o diálogo de confirmação, os rótulos e as
  mensagens permanecem idênticos.
