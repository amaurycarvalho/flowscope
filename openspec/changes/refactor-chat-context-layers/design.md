## Context

Ver `proposal.md` — Why, e o contrato em
`openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md`.
Estado atual relevante:

- `presentation/gui/chat/chat_panel.py` concentra a montagem do contexto
  (`_montar_contexto`), a coleta de fontes adicionais
  (`_preparar_fontes_adicionais`), o escalonamento (`_preparar_texto`) e o gate
  de confirmação (`_confirmar_leitura`), além do widget, da thread/fila e da
  sessão.
- `presentation/gui/chat/fundamentos.py` é puro e já depende de
  `application.fundamental`; `conhecimento.py` monta o bloco institucional a
  partir de `TAB_CONTENT` e das constantes de `about_panel`.
- `presentation/gui/chat/documentos.py` contém `CascataDocumentos`
  (recuperação/orçamento) e depende de `presentation/gui/charts/document_preview`
  para extrair texto; `noticias.py` contém `FonteNoticias`, que usa o mesmo
  `document_preview`.
- `application/chat/consultar.py` já orquestra a consulta e monta o prompt; o
  `ContextoChat` já é um tipo de aplicação. A montagem do `ContextoChat`, no
  entanto, vive na UI.
- `application/noticias/fonte_chat.py` já monta o índice de notícias (regra de
  aplicação); `FonteNoticias` apenas injeta catálogo/store e formata a segunda
  camada.
- Testes existentes: `test_chat_fundamentos.py`, `test_chat_documentos.py`,
  `test_chat_conhecimento.py` e `test_noticias_chat_context.py` cobrem lógica
  pura, mas residem em `tests/test_presentation`.
- A allowlist de fronteira tem 3 entradas legadas sem relação com esta fatia.

## Goals / Non-Goals

**Goals:**

- Colocar a montagem do contexto do chat (conhecimento, fundamentos, documentos
  e fontes adicionais) em `application/chat`, com escalonamento e gate.
- Deixar `presentation` com widget, thread/fila, sessão, diálogo de confirmação,
  cópia/limpeza e os textos de interface.
- Mover a extração de texto de documentos para `application`, sem acoplar a
  aplicação à apresentação.
- Migrar os testes puros para `tests/test_application`, sem `DISPLAY`.

**Non-Goals:**

- Não mover a orquestração da consulta (`ConsultarChatUseCase`) nem o
  `ContextoChat`/`ContextoDocumental`, já em `application`.
- Não alterar o protocolo `LLMPort`, os prompts, a ordem das seções do prompt
  nem os textos enviados.
- Não alterar a allowlist (a fatia não tem violação `presentation -> infrastructure`).
- Não redesenhar o painel, os diálogos ou os rótulos.

## Decisions

### D1 — Fundamentos e notícias do chat em `application/chat`

`fundamentos.py` move inteiro para `application/chat/fundamentos.py`.
`FonteNoticias`/`TITULO_FONTE`/`SEM_DOCUMENTO` movem de
`presentation/gui/chat/noticias.py` para `application/chat/noticias.py`.
Alternativa: manter ambos na apresentação. Rejeitada por serem serialização e
recuperação de contexto, não desenho.

### D2 — Cascata de documentos em `application/chat`

`CascataDocumentos`, `DocumentoEscopo`, `faixa_confirmacao`, as faixas e os
tetos movem para `application/chat/documentos.py`. O gate de confirmação
continua recebendo um callback (`ConfirmaAlvos`), com o diálogo Tk permanecendo
na apresentação. Alternativa: manter a cascata em `presentation`. Rejeitada por
misturar recuperação/orçamento com a UI.

### D3 — Extração de texto em `application/document_preview.py`

`texto_preview`, `tem_texto`, `SEM_TEXTO`, `texto_de_html` e `texto_de_pdf`
saem de `presentation/gui/charts/document_preview.py` para
`application/document_preview.py`, e os importadores existentes
(`document_flow_mixin`, `noticias_panel`, `resumos_job`, testes) passam a
consumir de `application`. Alternativa: injetar a extração na cascata via
callback. Rejeitada por manter parsing dentro de `presentation`, contrariando o
contrato de localização ("`infrastructure`/parsing fora de `presentation`").
Observação: o parse de HTML/PDF é I/O; a fatia o coloca em `application` por ser
o ponto compartilhado já consumido pela apresentação, sem criar nova porta.

### D4 — Bloco de conhecimento montado na aplicação, com textos injetados

`montar_bloco_conhecimento` vai para `application/chat/conhecimento.py` e passa
a receber os textos de interface como parâmetros (a seção de orientação das
sub-abas derivada de `TAB_CONTENT` e os dados institucionais de `about_panel`),
em vez de importar `presentation`. A apresentação fornece `TAB_CONTENT` e as
constantes; a aplicação decide cabeçalhos e ordem. Alternativa: mover os textos
para `application`. Rejeitada por serem conteúdo de interface compartilhado com
a aba "Sobre".

### D5 — Montador de contexto em `application/chat/contexto.py`

Cria-se um montador que substitui `chat_panel._montar_contexto` e os auxiliares
`_preparar_fontes_adicionais`, `_preparar_texto` e `_confirmar_leitura`:
recebe conhecimento, fundamentos, watchlist, a cascata e as fontes adicionais;
produz o `ContextoChat` com `ContextoDocumental` (resumos + `preparar_texto` +
`confirmar`) e aplica o escalonamento somando documentos e fontes. O diálogo de
confirmação entra como callback (`confirmar`), preservando o comportamento no
Tk. Alternativa: manter a montagem no painel. Rejeitada por ser o núcleo do
"que entra no prompt".

### D6 — Testes puros migrados, não reescritos

`test_chat_fundamentos.py`, `test_chat_documentos.py`,
`test_chat_conhecimento.py` e as classes puras de `test_noticias_chat_context.py`
migam para `tests/test_application`, apontando para os novos módulos; a parte de
escalonamento do painel passa a testar o montador de `application`. Os testes de
wiring/estado/thread permanecem em `tests/test_presentation`. Alternativa:
manter testes de lógica em `test_presentation`. Rejeitada por violar o orçamento
de testes de UI e a meta de cobertura (`fail_under = 85`).

## Risks / Trade-offs

- [Migrar `document_preview` toca painéis de documentos] → mover com atualização
  mecânica de imports e rodar `make test`/`make complexity` para confirmar
  paridade; os testes do painel de documentos já cobrem a extração.
- [Mudança de assinatura do bloco de conhecimento] → manter os mesmos textos e
  ordem; cobrir com teste de aplicação e preservar o teste da aba "Sobre".
- [Escalonamento com duas fontes] → preservar a soma de documentos e fontes no
  gate e na resolução, com testes puros do montador.
- [Testes de UI sensíveis a import] → atualizar os imports dos testes mantendo
  os mesmos cenários e asserções.
- [Ciclos de import ao mover] → mover no sentido
  `presentation -> application -> domain`; o guardrail acusa regressões.

## Migration Plan

1. Mover `document_preview` para `application` e atualizar importadores.
2. Criar `application/chat/{fundamentos,conhecimento,documentos,noticias}.py`.
3. Criar o montador de contexto em `application/chat/contexto.py`.
4. Atualizar `chat_panel.py`/`envio.py` para consumir o montador e manter só
   widget/thread/sessão/diálogo.
5. Migrar os testes puros para `tests/test_application`.
6. Rodar `make test` e `make quality-gate` (guardrail de fronteira incluso).

Rollback: reverter o change restaura os módulos na apresentação; comportamento
idêntico.

## Open Questions

- Nome do montador (`MontarContextoChatUseCase` vs `ContextoChatBuilder`) e a
  divisão de arquivos em `application/chat/`: decidir na implementação, sem
  impacto no contrato.
