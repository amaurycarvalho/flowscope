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

### 15. Botão de cancelar o envio com cancelamento cooperativo

O rodapé ganha, ao lado do botão "Enviar", um botão de cancelamento com o ícone `process-stop.png`, habilitado apenas enquanto há um envio em processamento. Ao acioná-lo, o painel solicita o cancelamento pelo `CancellationToken` da `process-cancellation`, restaura imediatamente os controles (Enviar habilitado, cancelar desabilitado) e exibe "Envio cancelado." na barra de status, sem aguardar a thread de trabalho. A thread observa o token antes de montar o contexto, entre as duas chamadas de completion e na confirmação; um contador de geração no painel descarta respostas tardias, que não são registradas na sessão nem exibidas.

Como `LLMPort.complete` é uma chamada bloqueante e não cancelável, o cancelamento é cooperativo: não aborta a requisição HTTP em andamento, mas o usuário recupera o controle de imediato e nenhum resultado posterior contamina a conversa. Isso segue o precedente da `process-cancellation` (finalizar a interface sem aguardar a thread).

Alternativa considerada: aguardar o término da chamada antes de restaurar os botões — deixaria a interface presa enquanto o provedor responde.

### 16. Histórico textual da conversa no envio multi-turno

O `ChatPanel` captura, na thread do Tk e antes de registrar a pergunta atual, a lista de `ChatMessage` bem-sucedidos da `ChatSession` e a passa ao `ConsultarChatUseCase` como `historico: Sequence[ChatMessage]`. O caso de uso converte cada turno em `{"role", "content"}` e envia `[*historico, {"role": "user", "content": prompt}]`, mantendo o mesmo histórico nas duas chamadas da cascata. Somente o texto final exibido compõe o histórico — o envelope JSON e as chaves de documentos ficam de fora. As mensagens de erro e aviso são registradas com `enviar_ao_modelo=False` e não são reenviadas ao modelo. O histórico respeita um teto de 10 mensagens e 8.000 caracteres, descartando os turnos mais antigos quando excedido; "Limpar" zera a sessão e, com ela, o histórico. Sem persistência entre aberturas da aba.

Alternativa considerada: reinjetar a transcrição inteira dentro de um único prompt de sistema — descartada por duplicar o formato de mensagens que a porta `LLMPort` já oferece e por dificultar a truncagem por turno.

### 17. "Enviar" condicionado aos fundamentos carregados

O chat só faz sentido com dados para consultar, e a sub-aba "Fundamentos" é a origem canônica dos dados da watchlist. O botão "Enviar" passa a exigir `_disponivel` (LLM configurada) **e** fundamentos não vazios, consultados por `fundamental_data_provider`. `ChatPanel._tem_fundamentos` centraliza essa checagem. Quando os fundamentos chegam com a aba "Chat AI" já aberta, o desfecho da carga chama `on_tab_changed`, que reavalia o painel por `_reavaliar_chat_llm` — sem novo acoplamento em `set_fundamental_data`.

Alternativa considerada: manter o envio habilitado e orientar no prompt — descartada por permitir uma consulta sem contexto útil e mascarar o estado vazio.

### 18. Bloqueio do cabeçalho durante o envio e habilitação por conteúdo

Enquanto `_processando`, "Limpar", "Copiar chat" e "Configuração" ficam desabilitados, junto do "Enviar"; ao terminar (resposta, erro ou cancelamento) todos são reavaliados. "Limpar" e "Copiar chat" só habilitam com conteúdo textual (a sessão exibida não vazia) e voltam a desabilitar após "Limpar". `_atualizar_controles` passa a ser o ponto único dessa política, chamado no registro de mensagens, no desfecho e no `limpar`.

Alternativa considerada: desabilitar apenas o "Enviar" durante o envio — deixaria o usuário apagar ou sobrescrever a conversa em andamento, correndo o risco de o desfecho tardio contaminar uma sessão já reiniciada.

### 19. Orientação da aba "Chat AI" no quadro textual

A entrada `(CHAT_AI_TAB, CHAT_AI_TAB)` é adicionada a `TAB_CONTENT` com objetivo, requisitos, contexto enviado e uso dos botões. `_on_tab_changed` passa a aplicar esse conteúdo ao `OrientationPanel` no ramo da aba "Chat AI"; por vir de `TAB_CONTENT`, a orientação também entra automaticamente no bloco de conhecimento do FlowScope enviado à LLM.

Alternativa considerada: um texto dedicado fora de `TAB_CONTENT` — descartada por duplicar a fonte e mantê-la fora do conhecimento do próprio aplicativo.

### 20. Verificação do acesso aos caches de Notícias

A fonte `FonteNoticias` (change `noticias-b3`) já é registrada em `fontes_adicionais` do `ChatPanel` e lê os mesmos caches da sub-aba "Notícias" (`NoticiasCatalog` com a raiz padrão, resumos longos/curtos e texto cacheado, com fallback para o HTML). A verificação confirmou o wiring e a leitura; nenhuma mudança de código foi necessária nesta change. A leitura é sob demanda e tolerante a cache frio/falha, omitindo a seção quando não há conteúdo.

### 21. Orientação da aba "Sobre" no quadro textual

Assim como a aba "Chat AI", a aba "Sobre" ganha uma entrada em `TAB_CONTENT` (chave `(ABOUT_TAB, ABOUT_TAB)`) com objetivo, conteúdo e uso dos atalhos. `_on_tab_changed` passa a aplicá-la ao `OrientationPanel` no ramo da aba "Sobre". Por vir de `TAB_CONTENT`, a orientação também integra o bloco de conhecimento do FlowScope enviado à LLM — sem duplicar a fonte.

Alternativa considerada: manter o quadro vazio na aba "Sobre" — descartada por deixar o painel lateral inútil nessa aba.

## Risks / Trade-offs

- **[Risco] RPM padrão 5** → cascata limitada a 2 chamadas e interrupção antecipada reduzem a pressão; mensagens de espera na statusbar.
- **[Risco] Escopo da watchlist completa** → orçamento de caracteres e gates de confirmação antes de ler o texto integral.
- **[Risco] Inferência do ticker pela LLM** → o prompt instrui a citar o ticker identificado e a pedir esclarecimento quando a pergunta for ambígua; a seleção de documentos-alvo é validada pelas chaves existentes no escopo.
- **[Risco] Caches frios** → preparação sob demanda pode ser lenta; a orientação deve sugerir "Atualizar"/"Resumir" na sub-aba Documentos.
- **[Risco] Formato da resposta do modelo** → parser tolerante com fallback para texto integral.
- **[Trade-off] Sem streaming** → resposta completa, sem token-a-token.
- **[Trade-off] Sem token accounting** → teto por documento (~12k caracteres, precedente do resumidor) e teto global, truncando com aviso.
- **[Risco] Resposta tardia após cancelar o envio** → token cooperativo e contador de geração descartam o desfecho; nada é registrado na sessão.
