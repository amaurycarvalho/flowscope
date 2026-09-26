## 1. Extração de texto para a aplicação

- [ ] 1.1 Mover `texto_preview`/`tem_texto`/`SEM_TEXTO`/`texto_de_html`/`texto_de_pdf` de `presentation/gui/charts/document_preview.py` para `application/document_preview.py` e atualizar os importadores (`document_flow_mixin`, `noticias_panel`, `resumos_job`, chat e testes); verificar com os testes existentes de extração/pré-visualização

## 2. Contexto do chat na aplicação

- [ ] 2.1 Mover `fundamentos.py` de `presentation/gui/chat/` para `application/chat/fundamentos.py`; verificar com testes puros de escopo e serialização
- [ ] 2.2 Mover o bloco de conhecimento para `application/chat/conhecimento.py`, recebendo os textos de interface como parâmetros; verificar com testes puros de conteúdo e ordem
- [ ] 2.3 Mover `CascataDocumentos`/`DocumentoEscopo`/`faixa_confirmacao` de `presentation/gui/chat/documentos.py` para `application/chat/documentos.py`; verificar com testes puros de resumos, escalonamento, gate e orçamento
- [ ] 2.4 Mover `FonteNoticias` de `presentation/gui/chat/noticias.py` para `application/chat/noticias.py`; verificar com testes puros do índice e do conteúdo integral
- [ ] 2.5 Criar o montador de contexto em `application/chat/contexto.py` (conhecimento, fundamentos, documentos e fontes; escalonamento e gate) e verificar com testes puros de montagem e de confirmação

## 3. Apresentação — painel só exibe

- [ ] 3.1 Atualizar `chat_panel.py`/`envio.py` para consumir o montador de `application/chat` e manter apenas widget, sessão, thread/fila, cancelamento, cópia/limpeza e o diálogo de confirmação; verificar o painel com fakes e paridade de contexto/prompt

## 4. Testes e verificação

- [ ] 4.1 Migrar `test_chat_fundamentos.py`, `test_chat_documentos.py`, `test_chat_conhecimento.py` e as classes puras de `test_noticias_chat_context.py` para `tests/test_application`, sem `DISPLAY`; verificar ausência de `DISPLAY` e cobertura das funções
- [ ] 4.2 Rodar `make test` e `make complexity` e confirmar tudo verde com paridade de comportamento, incluindo o guardrail de fronteira
