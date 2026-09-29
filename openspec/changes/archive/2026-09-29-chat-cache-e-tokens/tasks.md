## 1. Porta de LLM com uso de tokens

- [x] 1.1 Criar `LLMUsage` (entrada, saida) e `LLMResposta` (texto, uso) no domínio e alterar `LLMPort.complete` para devolvê-los; verificar com `tests/test_domain/test_llm/test_ports.py`.
- [x] 1.2 Extrair `response.usage` (prompt/completion tokens) no `LiteLLMChatAdapter`, tolerando ausência; verificar com `tests/test_infrastructure/test_llm/test_adapter.py`.
- [x] 1.3 Atualizar os 4 consumidores da porta (`application/chat/consultar.py`, `application/resumo_documento.py`, `application/avaliar_guidance.py`, `presentation/gui/llm/config_dialog.py`) para usar `.texto`; verificar `make test`.

## 2. Documentos somente-leitura de cache

- [x] 2.1 Remover a geração de resumo de `CascataDocumentos.preparar_resumo`/`montar_resumos`, lendo apenas resumos cacheados e omitindo pendentes; verificar `tests/test_application/test_chat_documentos.py` com um caso de cache frio sem chamada de LLM.
- [x] 2.2 Remover a extração sob demanda de `preparar_texto`/`_preparar_texto_documento`, servindo apenas o `text_store`; verificar teste que garante ausência de escrita/extração no miss.

## 3. Notícias somente-leitura de cache, filtro e gate

- [x] 3.1 Restringir o índice a itens recuperáveis (resumo ou texto em cache) e remover `texto_preview` de `_conteudo`/`preparar_texto`; verificar `tests/test_application/test_noticias_chat_context.py`.
- [x] 3.2 Implementar o pré-filtro determinístico por regex dos termos da pergunta (tickers e palavras-chave) sobre título/metadados; verificar testes de filtro com ticker e palavra-chave.
- [x] 3.3 Adicionar o gate de confirmação quando o índice filtrado exceder `LIMITE_ENVIO_NOTICIAS` (default ~600 tokens estimados por `len//4`), reusando o canal `ctx.confirmar`/`_confirmar_no_tk`; verificar teste que confirma e teste que recusa (omite a seção).
- [x] 3.4 Omitir a seção de notícias quando o filtro não casar nada; verificar teste dedicado.

## 4. Orquestração da cascata em duas rodadas

- [x] 4.1 Remover o reenvio das fontes voláteis (índice de notícias) no sufixo da escalada em `ConsultarChatUseCase._montar_sufixo`; verificar `tests/test_application/test_consultar_chat.py`.
- [x] 4.2 Confirmar que a cascata permanece em no máximo duas chamadas (resumos cacheados em bloco e, depois, texto integral cacheado); verificar teste de contagem de chamadas.

## 5. Contador de tokens e rótulo persistente

- [x] 5.1 Acumular tokens por sessão no `ChatPanel` (soma das completions do envio, incluindo a cascata), zerando em `limpar()` e `__init__`; expor `ao_uso` na consulta e publicar `Progresso`; verificar testes do painel.
- [x] 5.2 Criar o rótulo de tokens na barra de status (`StatusMixin`/`_status_frame`) com callback do painel e visibilidade alternada em `_on_tab_changed` (somente aba "Chat AI"); verificar testes de visibilidade.
- [x] 5.3 Formatar os valores em `K` com 1 casa (ex.: `5540 -> 5.5K`, `340 -> 0.3K`) e cobrir os limites (0, <1000, >=1000, arredondamento) com teste unitário.

## 6. Envio longo e watchdog

- [x] 6.1 Manter o job do chat vivo durante chamadas longas e a espera da confirmação (heartbeat via `ctx.progress`), sem acionar o watchdog; verificar teste com provider bloqueante além do limite de inatividade.
- [x] 6.2 Marcar o estado "enviando" antes de `_registrar` em `_enviar` para que `_processando` nunca seja falso entre registrar e submeter; verificar teste dos estados dos botões na transição.

## 7. Regressão e documentação de interface

- [x] 7.1 Revisar o texto de orientação da aba "Chat AI" em `TAB_CONTENT` para refletir o contexto cache-only e a omissão de pendentes; verificar `tests/test_application/test_chat_conhecimento.py`.
- [x] 7.2 Rodar `make test` e `make lint` e garantir a suíte verde.
