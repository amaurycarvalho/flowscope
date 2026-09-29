## Why

A aba "Chat AI" hoje executa trabalho que não é dela — extrai texto e gera resumos sob demanda (`CascataDocumentos.preparar_resumo`/`_preparar_texto_documento`) — e reenvia o índice inteiro de notícias em todo turno como sufixo volátil (até 32.000 caracteres, não cacheado). Isso torna custo e latência imprevisíveis e contraria o objetivo de enviar à LLM apenas o estritamente necessário. Além disso, não há visibilidade do gasto de tokens e o watchdog de inatividade (120 s) encerra envios longos no meio, reativando o botão "Enviar" por engano.

## What Changes

- **Chat estritamente leitor de cache**: a aba "Chat AI" NUNCA resume documentos/notícias nem extrai texto sob demanda; usa apenas resumos e textos já processados e cacheados pelo usuário. Itens pendentes de resumo ou extração são **omitidos em silêncio** do contexto (sem citação e sem aviso).
- **Uniformização documentos × notícias**: as duas origens seguem a mesma cascata cache-only (resumos cacheados primeiro — curto+longo em bloco —, depois o texto integral cacheado sob pedido da LLM) e o mesmo tratamento de pendentes.
- **Minimização do índice de notícias**: o índice passa por um **pré-filtro determinístico por regex** (tickers/palavras-chave extraídos da pergunta aplicados ao título); lista apenas itens recuperáveis (com resumo ou texto em cache); se o subconjunto filtrado ainda for grande, o sistema **pede confirmação** antes de carregá-lo na LLM.
- **Segunda chamada sem o índice**: a rodada de escalonamento deixa de reenviar o índice de notícias (só o conteúdo resolvido dos alvos entra no sufixo).
- **BREAKING** — `LLMPort.complete` passa a devolver `LLMResposta(texto, LLMUsage)` em vez de `str`, para expor os tokens de entrada/saída do `usage` do provedor.
- **Contador de tokens na statusbar**: durante "Consultando a I.A.…", o sistema acumula tokens de entrada/saída e os exibe em um **rótulo persistente** na barra de status, visível somente na aba "Chat AI", formatado em `K` com 1 casa decimal; o total persiste após "Pronto." e é **zerado** ao limpar o chat ou na inicialização.
- **Envio longo não é cancelado por inatividade**: o processamento do chat mantém o job vivo durante chamadas longas (heartbeat), de modo que o botão de cancelamento permanece habilitado e o "Enviar" só reabilita ao término real.

## Capabilities

### New Capabilities

- `llm-chat-tokens`: contabilização acumulada de tokens de entrada/saída da sessão de chat, formatação em `K`, reset ao limpar/inicializar e rótulo persistente na barra de status restrito à aba "Chat AI".

### Modified Capabilities

- `llm-chat-context`: deixa de preparar resumos/textos sob demanda; a cascata documental passa a ser somente-leitura de cache e itens pendentes são ignorados.
- `noticias-chat-context`: índice restrito a itens recuperáveis, com pré-filtro determinístico e gate de confirmação por tamanho; leitura somente de cache e tratamento de pendentes alinhado aos documentos.
- `llm-chat-gui`: o envio do chat não é mais encerrado por inatividade durante chamadas longas, preservando a habilitação correta dos botões "Enviar"/cancelar e o desfecho só ao término real.
- `llm-provider`: a porta de completion passa a devolver o texto e o uso de tokens (`LLMResposta`/`LLMUsage`) em vez de apenas a string.

## Impact

- `src/flowscope/application/chat/documentos.py`: remover a geração de resumo e a extração sob demanda; leitura pura do catálogo/stores; filtrar pendentes.
- `src/flowscope/application/chat/noticias.py` e `application/noticias/fonte_chat.py`: índice restrito a recuperáveis, pré-filtro por regex e gancho de confirmação; sem extração sob demanda.
- `src/flowscope/application/chat/consultar.py` e `contexto.py`: rodada de escalonamento sem o índice volátil; metadados do filtro/confirmação.
- `src/flowscope/domain/llm/{ports,__init__}.py` e `infrastructure/llm/adapter.py`: `LLMResposta`/`LLMUsage` e leitura de `response.usage`.
- Consumidores da porta (BREAKING): `application/resumo_documento.py`, `application/avaliar_guidance.py`, `presentation/gui/llm/config_dialog.py`, `application/chat/consultar.py`.
- `src/flowscope/presentation/gui/chat/{chat_panel,envio}.py`, `app_layout.py`/`app_status.py`/`app_tab_actions.py`: contador, rótulo persistente e visibilidade por aba.
- `src/flowscope/presentation/gui/background/manager.py`: heartbeat/long-call para não acionar o watchdog durante chamadas longas.
- Deltas em `openspec/specs/llm-chat-context/spec.md`, `noticias-chat-context/spec.md`, `llm-chat-gui/spec.md`, `llm-provider/spec.md` e nova `llm-chat-tokens/spec.md`.
- **Coordenação**: `cache-prompt-chat` (prefixo estável/sufixo volátil), `background-job-manager` (watchdog de inatividade, ainda não arquivada), `llm-chat-rag` (a fonte vetorial deve permanecer volátil e cache-only).
- Sem impacto em dependências externas.
