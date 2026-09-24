## Context

Ver `proposal.md` — Why. A `llm-core` (arquivada, implementada) já fornece `LLMPort`, `create_llm_provider`, `load_llm_config`, `check_llm_deps`, `LLMConfigDialog` e a hierarquia de exceções. A sub-aba "Documentos" já persiste o texto extraído em `~/.cache/flowscope/document-texts/` e os resumos curto/longo (280/1500 caracteres) em `~/.cache/flowscope/document-summaries/`, e já exibe material facts (fatos relevantes/assembleias) baixados para `documentos-relevantes/`.

Esta change é a versão não vetorial do chat. Ela reutiliza esses caches e serviços em vez de criar um pipeline de embeddings.

## Goals / Non-Goals

**Goals:**
- Uma aba de topo única de chat (**Chat AI**) sobre os dados já carregados e documentos em cache, com um ponto único de entrada.
- Contexto do FlowScope a partir dos textos de orientação e da aba Sobre.
- Contexto de fundamentos a partir da tabela carregada.
- Cascata de recuperação de documentos com confirmação por quantidade e orçamento de contexto.
- Reuso máximo da infraestrutura existente (stores, resumidor, widget readonly, diálogo de configuração).

**Non-Goals:**
- VectorStore, embeddings, chunker e indexação vetorial (change `llm-chat-rag`).
- Persistência de histórico, streaming, fine-tuning, OCR, langchain.
- Aquisição/download de documentos (permanece nas changes de extração e em `noticias-b3`).
- Cliente de LLM, presets de completion e diálogo de configuração (propriedade da `llm-core`).

## Decisions

### 1. Cascata em até duas chamadas de completion

O pedido original descreve três leituras (resumos curtos, resumos longos, texto integral). Como o RPM padrão é 5 e cada chamada extra adiciona latência e consumo de cota, os dois primeiros níveis são combinados em uma única chamada (resumos curtos + longos juntos). A segunda chamada lê apenas o texto integral dos alvos selecionados. A leitura lógica permanece em três níveis, com interrupção antecipada assim que houver resposta.

Alternativa considerada: três chamadas literais — mais fiel à descrição, porém com o dobro de round-trips e pressão sobre o rate limiter.

### 2. Contrato de resposta estruturada e tolerante

A LLM responde em um formato delimitado/JSON com `resposta` e a lista de chaves de documentos-alvo. O parser é tolerante (espelha `ResumoDocumento._interpretar`): quando o formato não é reconhecido, a resposta inteira é tratada como texto e nenhuma nova rodada é disparada.

Alternativa considerada: extração por marcadores textuais simples — menos expressiva para distinguir "resposta" de "selecionar documentos".

### 3. Gates de confirmação por quantidade de documentos-alvo

Antes da leitura do texto integral: até 3 documentos prossegue automaticamente; entre 4 e 7, lista os nomes e pede confirmação; 8 ou mais, informa a quantidade e pede confirmação. A confirmação é um diálogo que pausa a thread de trabalho e retoma a resposta no contexto do Tk.

Alternativa considerada: limite único binário — menos gradual e mais surpreendente para o usuário.

### 4. Reuso dos caches e serviços de documentos

A cascata lê `JsonDocumentSummaryStore`, `JsonDocumentTextStore` e `DocumentCatalog` (já usados pela sub-aba "Documentos"). Quando o texto ou o resumo não estão em cache, a preparação é feita sob demanda reutilizando `DocumentFlowMixin.preparar_texto` / `ResumirDocumentoUseCase`. Isso evita reimplementar extração de HTML/PDF e reutiliza os caches de material facts.

### 5. Conhecimento do FlowScope como bloco estático

O conhecimento vem de `TAB_CONTENT` (orientação das sub-abas) e das constantes da aba Sobre (apresentação, licença, versão). É montado uma vez e enviado como bloco de sistema, estável entre turnos.

### 6. Fundamentos serializados da tabela carregada

Os dados de `_fundamental_data` são serializados de forma compacta (reutilizando o formato da tabela) cobrindo a watchlist completa. O ticker relevante é inferido pela LLM a partir da pergunta, sem seletor de escopo na interface. Sem dados carregados, o chat orienta o carregamento.

### 7. Aba de topo única "Chat AI", sempre visível

A aba "Chat AI" entra no `_main_notebook` entre "Análise do Ticker" e "Sobre", substituindo as sub-abas "Chat Geral" e "Chat Ticker". Diferente de esconder a aba, ela permanece visível e mostra o estado não configurado, permitindo ao usuário abrir a configuração pela própria aba.

### 8. Reuso dos componentes de UI existentes

`ReadonlyText` (cursor, seleção, Ctrl+A/C), o despacho por aba de `_texto_para_copiar`, `LLMConfigDialog` via `_abrir_config_llm`, `_set_status`/`_flash_status`, `mensagem_erro_llm`. O cabeçalho da aba tem os botões "Limpar", "Copiar chat" e "Configuração"; este último fica sempre visível, logo após "Copiar chat", e abre o mesmo diálogo da `llm-core` usado na sub-aba "Documentos". O completion roda em thread de trabalho publicando em `queue.Queue`, consumida na thread do Tk via `after` (padrão de `LLMConfigDialog`/`DocumentosJob`).

### 9. Sessão em memória

`ChatSession` sem persistência; a aba começa limpa. Simplicidade e ausência de preocupações de privacidade.

### 10. Escopo por ticker inferido pela LLM

Não há seletor de escopo. O contexto enviado é sempre o da watchlist completa (fundamentos e documentos) e o prompt instrui a LLM a identificar o ticker referido na pergunta, escolhendo os documentos-alvo pelas chaves. Quando a pergunta for ambígua quanto ao ativo, o prompt orienta a LLM a pedir esclarecimento em vez de adivinhar.

### 11. Ponto de extensão de contexto

`ContextoChat` recebe uma lista de fontes adicionais de contexto (título e texto), renderizadas no prompt como seções próprias, além do conhecimento do FlowScope, dos fundamentos e da cascata de documentos. Changes futuras (notícias em `noticias-b3`, recuperação vetorial em `llm-chat-rag`) registram as suas fontes por esse ponto, sem alterar a cascata. A montagem das fontes adicionais ocorre na thread de trabalho, no `ChatPanel`, e pode receber a pergunta para permitir recuperação dependente da consulta. Uma fonte que falha ou retorna vazio é simplesmente omitida, sem impedir a resposta.

### 12. Botão "Limpar" com confirmação

O cabeçalho ganha o botão "Limpar", antes de "Copiar chat", que reinicia a conversa reutilizando `ChatPanel.limpar()`. Como a sessão é em memória, limpar equivale a começar agora. Antes de executar, exibe um `messagebox.askyesno` (mesmo padrão do gate de confirmação de documentos); se o usuário recusar, a sessão permanece inalterada.

## Risks / Trade-offs

- **[Risco] RPM padrão 5** → cascata limitada a 2 chamadas e interrupção antecipada reduzem a pressão; mensagens de espera na statusbar.
- **[Risco] Escopo da watchlist completa** → orçamento de caracteres e gates de confirmação antes de ler o texto integral.
- **[Risco] Inferência do ticker pela LLM** → o prompt instrui a citar o ticker identificado e a pedir esclarecimento quando a pergunta for ambígua; a seleção de documentos-alvo é validada pelas chaves existentes no escopo.
- **[Risco] Caches frios** → preparação sob demanda pode ser lenta; a orientação deve sugerir "Atualizar"/"Resumir" na sub-aba Documentos.
- **[Risco] Formato da resposta do modelo** → parser tolerante com fallback para texto integral.
- **[Trade-off] Sem streaming** → resposta completa, sem token-a-token.
- **[Trade-off] Sem token accounting** → teto por documento (~12k caracteres, precedente do resumidor) e teto global, truncando com aviso.
