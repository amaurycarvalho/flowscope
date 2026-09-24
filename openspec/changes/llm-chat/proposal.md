## Why

O FlowScope extrai dados de mercado e mantém documentos em cache, mas não permite consultá-los em linguagem natural. Esta change adiciona sub-abas de chat que respondem perguntas sobre os dados já carregados, sobre os documentos em cache e sobre o próprio FlowScope, consumindo a camada de LLM fornecida pela `llm-core`.

Esta versão inicial NÃO usa RAG vetorial: a recuperação de documentos é uma cascata sobre os resumos e o texto já cacheados pela sub-aba "Documentos". A indexação vetorial é uma evolução separada, na change `llm-chat-rag`.

## What Changes

- Aba de topo **Chat AI**, única e sempre visível, posicionada entre "Análise do Ticker" e "Sobre", como ponto único de entrada do chat.
- Sem seletor de escopo: o contexto cobre a watchlist completa e a LLM infere o ticker referido na pergunta.
- Contexto do chat com três origens: conhecimento do próprio FlowScope (textos de orientação das sub-abas + aba Sobre), tabela de fundamentos carregada (watchlist completa) e documentos em cache (watchlist completa).
- Cascata de documentos: resumos curtos → resumos longos → texto integral dos alvos, com interrupção antecipada ao obter resposta.
- Confirmação ao usuário conforme a quantidade de documentos-alvo (até 3 prossegue; 4 a 7 lista os nomes; 8 ou mais informa a quantidade).
- Campo de entrada habilitado apenas com a LLM configurada; orientação de configuração quando ausente. O cabeçalho tem os botões "Limpar", "Copiar chat" e "Configuração" (este sempre visível; abre o diálogo da `llm-core`, o mesmo da sub-aba Documentos).
- Botão "Limpar", antes de "Copiar chat", que reinicia a sessão como se estivesse começando agora, mediante confirmação (Sim/Não) do usuário.
- Botão "Copiar chat"; a cópia de dados CSV passa a incluir o conteúdo do chat quando a aba "Chat AI" está ativa.
- Respostas exibidas em campo somente-leitura com cursor, seleção e atalhos de teclado; erros da LLM na statusbar e no log.
- Sem VectorStore, embeddings, chunker, indexação ou `--index` — esses itens migram para a change `llm-chat-rag`.

## Capabilities

### New Capabilities

- `llm-chat-domain`: entidades de conversa em memória (`ChatMessage`, `ChatSession`).
- `llm-chat-context`: montagem do contexto (conhecimento do FlowScope, fundamentos carregados e cascata de documentos) e gates de confirmação.
- `llm-chat-llm`: orquestração da cascata sobre a porta `LLMPort` da `llm-core`, com contrato de resposta estruturada e interrupção antecipada.
- `llm-chat-gui`: widget de chat e aba única "Chat AI", com os comportamentos associados.

### Modified Capabilities

## Impact

- **Dependências**: consome a `llm-core` (implementada) — `LLMPort`, `create_llm_provider`, `load_llm_config`, `check_llm_deps`, `LLMConfigDialog` e as exceções tipadas. Não adiciona dependências `[llm]` (sem `fastembed`, sem `pypdf`).
- **Pré-requisitos**: caches `document-texts/` e `document-summaries/` populados pela sub-aba "Documentos"; resolução de fundamentos e material facts das changes de extração.
- **Remoção de escopo**: VectorStore, embeddings, configuração de embedding, indexação e `--index` saem desta change e passam para `llm-chat-rag`.
- **Binário**: inalterado (nenhuma dependência nativa nova).
