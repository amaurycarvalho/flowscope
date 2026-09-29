# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui o placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional

### [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões

### [llm-chat-rag](openspec/changes/llm-chat-rag) Recuperação vetorial como evolução da `llm-chat`, com VectorStore SQLite, embeddings e indexação de documentos consultada pela aba "Chat AI"

#### Added

- VectorStore em SQLite puro, com busca top-k por cosine similarity e filtro opcional por ticker.
- Módulo de embeddings com dois provedores: `fastembed` (local, default) e liteLLM (API).
- Porta `DocumentoIndexavel`/`DocumentSource` e fontes concretas, com extração de texto (HTML e PDF).
- Pipeline de indexação (`IndexarDocumentosUseCase`) e consulta RAG (`ConsultarDocumentosUseCase`) consumindo a porta `LLMPort` da `llm-core`.
- Integração da consulta RAG à aba "Chat AI" como fonte adicional de contexto, pelo ponto de extensão da `llm-chat`.
- Chunker de texto em Python puro.
- Configuração de embedding persistida em `llm.embedding` e presets de provedores de embedding.
- Dependência opcional `fastembed` no grupo `[llm]`.
- CLI `--index <TICKER>` com `--data-inicio` e `--data-fim`.

### [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado, com gauge de concentração, card informativo e timeline AFT

## [1.3.2] — 2026-09-29

### [background-job-manager](openspec/changes/archive/2026-09-29-background-job-manager) Componente único `BackgroundManager` que unifica a orquestração assíncrona (thread, fila, drenagem no Tk e watchdog), substituindo cinco implementações duplicadas

#### Added

- Introduz o `BackgroundManager` na camada de apresentação: submissão de trabalho assíncrono com políticas de agendamento (`latest_wins`, `serialize`, `parallel`), token de cancelamento **por job** e um único pump de drenagem na thread do Tk.
- Extrai um `JobContext` entregue ao worker para publicar progresso, resultado, erro e término sem tocar em widgets.

#### Changed

- Porta os quatro jobs existentes (`FundamentalJob`, `DocumentosJob`, `NoticiasJob`, `ResumosPendentesJob`) para o manager, removendo a coreografia duplicada de thread/fila/watchdog.
- Unifica sob o mesmo manager as demais threads inline de background já existentes.
- Nenhuma mudança de comportamento observável: rótulos, mensagens, estados de botão e ordem de exibição permanecem idênticos.
- `OperationGuard` permanece como guarda de UI contra reentrada do mesmo clique; a semântica de supersede passa a ser do manager.

### [bloquear-ui-inicializacao](openspec/changes/archive/2026-09-29-bloquear-ui-inicializacao) Gate de inicialização (escudo transparente + trava de controles e atalhos) que bloqueia a entrada até o Tk estar disponível, eliminando o vazamento de cursor de inicialização

#### Added

- Introduz um **gate de inicialização**: um escudo transparente cobrindo a janela (engole cliques em qualquer widget, inclusive abas e painéis sem `all_buttons()`), combinado com `disable_all_buttons()` para affordance e com o bloqueio dos atalhos globais (`F5`, `Return`, `Ctrl+Shift+C`) via flag de inicialização.

#### Changed

- O gate usa a autoridade única de estado ocupado (`FlowScopePresenter.enter/exit`) para travar controles e cursor de forma consistente, **dependendo** do `background-job-manager` (fatia A).
- O gate é liberado **após a restauração inicial de abas/painéis** (`_restore_tabs` → `_on_tab_changed` concluir), quando as leituras de catálogo já rodam em background por B/C.
- O release remove o escudo antes de restaurar o estado ocupado, para o snapshot de cursor não capturar o overlay.
- Testes do gate são headless (view fake), com apenas a existência/remoção do overlay em teste de UI, conforme `reduzir-testes-ui`.

### [cache-prompt-chat](openspec/changes/archive/2026-09-29-cache-prompt-chat) Prefixo estável cacheável do chat (conhecimento + fundamentos + resumos) com revalidação por assinatura, reduzindo o custo de tokens ao longo da conversa

#### Changed

- Reordena o prompt do chat em **prefixo estável + sufixo volátil**: o prompt de sistema passa a conter as instruções e o contexto estável (conhecimento + fundamentos + resumos); o histórico segue depois; e o sufixo (fontes adicionais por pergunta, texto integral da escalada e a pergunta) fica no fim.
- **Memoiza** o bloco de contexto estável com **revalidação por assinatura**: reusa o texto renderizado byte-a-byte enquanto a assinatura (conhecimento + fundamentos + resumos) não muda; reconstrói e aceita o miss quando muda.
- Mantém as fontes voláteis (busca vetorial/notícias do `llm-chat-rag`) e a pergunta sempre no sufixo, sem invalidar o prefixo.
- As duas chamadas da cascata compartilham o prefixo estável + histórico.
- Não altera a porta `LLMPort` nem o adaptador: a melhoria é provider-agnóstica (OpenAI/Gemini/DeepSeek aproveitam automaticamente).
- Conclui o porte do envio do chat para o `BackgroundManager` (única pendência da task 5.5 de `background-job-manager`): o `ChatPanel` deixa de manter thread/fila/poll/generation próprios e passa a derivar o estado dos controles do ciclo de vida dos jobs.

### [carga-principal-background](openspec/changes/archive/2026-09-29-carga-principal-background) Carga principal (`on_load_data`/`on_index_clicked`) migrada para o `BackgroundManager`, tornando-se assíncrona, cancelável e substituível

#### Changed

- Migra `on_load_data`, `on_index_clicked` e a carga de portfólio de `on_ticker_edit` para o `BackgroundManager`, com política `latest_wins` no grupo `carga`.
- O download do portfólio e o processamento de indicadores passam a publicar progresso por evento; a renderização (`on_result`, `_iniciar_analise_fundamental`) permanece na thread do Tk via marshaling.
- **BREAKING (spec)**: a carga principal deixa de ser síncrona e não cancelável; o botão "interromper" passa a ficar visível durante ela.
- Uma nova requisição de carga principal **substitui** a anterior (supersede) e o job novo inicia com token limpo. Reentrada do **mesmo** acionamento continua bloqueada pelo `OperationGuard`, mantido como guarda de UI.
- Atualiza `process-cancellation`, `loading-state-management` e `presentation-test-coverage` para refletir o novo modelo.

### [chat-cache-e-tokens](openspec/changes/archive/2026-09-29-chat-cache-e-tokens) Chat estritamente leitor de cache, com minimização do índice de notícias, contador de tokens na statusbar e envio longo que não é cancelado por inatividade

#### Added

- **Contador de tokens na statusbar**: durante "Consultando a I.A.…", o sistema acumula tokens de entrada/saída e os exibe em um **rótulo persistente** na barra de status, visível somente na aba "Chat AI", formatado em `K` com 1 casa decimal; o total persiste após "Pronto." e é **zerado** ao limpar o chat ou na inicialização.

#### Changed

- **Chat estritamente leitor de cache**: a aba "Chat AI" NUNCA resume documentos/notícias nem extrai texto sob demanda; usa apenas resumos e textos já processados e cacheados pelo usuário. Itens pendentes de resumo ou extração são **omitidos em silêncio** do contexto (sem citação e sem aviso).
- **Uniformização documentos × notícias**: as duas origens seguem a mesma cascata cache-only (resumos cacheados primeiro — curto+longo em bloco —, depois o texto integral cacheado sob pedido da LLM) e o mesmo tratamento de pendentes.
- **Minimização do índice de notícias**: o índice passa por um **pré-filtro determinístico por regex** (tickers/palavras-chave extraídos da pergunta aplicados ao título); lista apenas itens recuperáveis (com resumo ou texto em cache); se o subconjunto filtrado ainda for grande, o sistema **pede confirmação** antes de carregá-lo na LLM.
- **Segunda chamada sem o índice**: a rodada de escalonamento deixa de reenviar o índice de notícias (só o conteúdo resolvido dos alvos entra no sufixo).
- **BREAKING** — `LLMPort.complete` passa a devolver `LLMResposta(texto, LLMUsage)` em vez de `str`, para expor os tokens de entrada/saída do `usage` do provedor.

#### Fixed

- **Envio longo não é cancelado por inatividade**: o processamento do chat mantém o job vivo durante chamadas longas (heartbeat), de modo que o botão de cancelamento permanece habilitado e o "Enviar" só reabilita ao término real.

### [descarregar-tk-io-restante](openspec/changes/archive/2026-09-29-descarregar-tk-io-restante) Últimos pontos de I/O na thread do Tk (pré-visualização de documentos, cópia de gráfico e polling de notícias) migrados para background

#### Changed

- A pré-visualização de documentos deixa de ler o cache de texto e de avaliar `precisa_resumo`/`precisa_guidance` na thread do Tk; a decisão e a leitura passam para o worker do job de preview, mantendo o estado de carregamento e a exibição do resumo já existentes.
- A cópia de gráfico para o clipboard deixa de bloquear a thread do Tk no `subprocess` de transferência; o rendering da figura permanece serializado com a thread do Tk e a transferência roda em background, com feedback de sucesso/erro na barra de status.
- A remontagem da árvore de notícias após cancelamento passa a ser disparada pelo término do job (evento do manager) em vez de um laço de `after` que consulta `thread.is_alive()` na thread do Tk.
- Não altera as portas `LLMPort`, `ClipboardPort` nem `DocumentTextStore`: a melhoria é de orquestração na apresentação.
- Fora de escopo: I/O curto de preferências/atalho (`save_preferences`, `_on_create_shortcut`) e spawn de aplicativos externos (`xdg-open`/`webbrowser`), por custo desprezível.

### [leituras-catalogo-background](openspec/changes/archive/2026-09-29-leituras-catalogo-background) Leituras de catálogo (Documentos, Notícias e Evolução dos Fundamentos) movidas para o `BackgroundManager` com estado de carregamento

#### Changed

- Move para o `BackgroundManager` a leitura do catálogo da sub-aba "Documentos" (varredura de raízes + índice de resumos/textos) e a remontagem da árvore passa a ocorrer por evento na thread do Tk, com estado de carregamento.
- Move para o manager a leitura do índice de notícias e a checagem de existência de HTML na sub-aba "Notícias", com remontagem por evento e estado de carregamento.
- Move para o manager a leitura do cache histórico da sub-aba "Evolução dos Fundamentos".
- Preserva o comportamento observável: leitura apenas do cache local (sem B3), estado vazio em cache frio, ordenação, filtragem de entradas sem HTML e cancelamento/descarte de leituras obsoletas quando o ticker muda.
- As leituras usam política `latest_wins` no grupo do painel, de modo que trocar de ticker descarta a leitura anterior.

### [llm-chat-contabilidade-tokens](openspec/changes/archive/2026-09-29-llm-chat-contabilidade-tokens) Contabilidade real de tokens no chat: desconto de cache-hit e percentual de ocupação da janela de contexto na barra de status

#### Added

- A barra de status passa a exibir o percentual ocupado da janela de contexto, entre parênteses e sem casa decimal, calculado a partir do `prompt_tokens` bruto da completion atual sobre a janela do modelo.
- Os presets ganham `context_window` como tamanho default por provedor/modelo; a resolução via `litellm.get_model_info(...)["max_input_tokens"]` enriquece o valor quando disponível.

#### Changed

- `LLMUsage` passa a reportar os tokens de cache-hit (leitura) e de cache-write, além de entrada e saída; o adaptador liteLLM extrai `usage.prompt_tokens_details.cached_tokens`, tolerando a ausência.
- A barra de status acumula `entrada_real = prompt_tokens - cached_tokens`, exibindo o total de entrada novo (não cacheado).
- Quando o provedor não reporta cache, um fallback determinístico estima o cache-hit: apenas para provedores que suportam cache e quando a assinatura do bloco estável não muda entre envios, usando a contagem de tokens do prefixo estável (`system` + instrução de formato + bloco estável) via `litellm.token_counter`.

### [llm-chat-contexto-sob-demanda](openspec/changes/archive/2026-09-29-llm-chat-contexto-sob-demanda) Contexto inicial sob demanda: flag `input_limitado` por modelo servindo conhecimento, fundamentos e resumos apenas quando solicitados

#### Added

- Novo parâmetro booleano `input_limitado` por provedor/modelo na configuração da LLM (`llm.chat.providers[<provider>]`), com default `false`.
- Checkbox correspondente no diálogo de configuração, persistido e restaurado ao trocar de provedor.
- Recursos iniciais solicitados sob demanda DEVEM passar por um gate de confirmação com **texto próprio**, distinto do gate de texto integral de documentos.

#### Changed

- Com o flag ativo, o prefixo estável do chat NÃO DEVE carregar conhecimento, fundamentos e resumos; em vez disso, DEVE informar a existência desses recursos e como solicitá-los.
- Os recursos iniciais (conhecimento, fundamentos e resumos) passam a ser servidos sob demanda pela mesma cascata de requisição de conteúdo já usada para documentos.
- Com o flag ativo, o orçamento da cascata sobe de duas para **até três chamadas** para acomodar a requisição de recursos e a escalada para documentos na mesma pergunta.

### [reduzir-testes-ui](openspec/changes/archive/2026-09-29-reduzir-testes-ui) Teto enforced para testes de UI, com migração da lógica pura para testes headless e ratchet que só diminui

#### Added

- Introduz um **teto enforced** para os testes de UI: um baseline commitado da contagem de `@needs_display`, verificado por teste arquitetural que reprova aumento e exige queda — mesmo padrão da allowlist de fronteiras.

#### Changed

- Migra testes de lógica pura de `tests/test_presentation` para `tests/test_application`/`tests/test_domain`, eliminando o gate `@needs_display` desnecessário.
- Converte para headless, via fakes de mixin/manager, os testes de UI que só exercitavam processamento (preview em thread, cache de texto, lote, geração de resumo).
- Converte para headless os testes de orquestração do envio do chat portado por `cache-prompt-chat` (submissão, cancelamento cooperativo e descarte do desfecho tardio), preservando a paridade de mensagens e de estados de botão.
- Consolida testes de estado de widget duplicados, mantendo um representante por comportamento observável.
- Reconcilia `presentation-test-coverage` com o comportamento pós-A/B/C, exigindo verificação headless do processamento.
- **Reconciliação com a fatia A**: parte do escopo já foi entregue por A (guardrail de aumento, `TestPreview`, orquestração de jobs headless); esta change verifica e assume o que já existe, converte o baseline para arquivo commitado (`ui_test_budget.txt`, iniciando em 250), adiciona o ratchet (queda exige atualização) e **baixa** o baseline a partir de 250.

### [short-interest-cache](openspec/changes/archive/2026-09-29-short-interest-cache) Cache de short interest não persiste mais mapa vazio, reconsultando dias publicados após a coleta e descartando caches vazios legados

#### Changed

- O comportamento observável dos cálculos (Shorts%, SIR e classificações) permanece inalterado; muda apenas a disponibilidade do insumo ao longo do tempo.

#### Fixed

- O cache de ações alugadas passa a **não persistir mapa vazio**: um dia consultado antes da publicação é reconsultado em execuções seguintes.
- Um cache vazio já gravado passa a ser tratado como ausência (*miss*), forçando a recoleta do dia.
- O construtor do `B3ShortInterestSource` passa a **descartar caches vazios legados** (`b3_emprestimos_btb-v1_*.json` com `data` vazio), análogo ao *bust* de portfólio do `B3Client`.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.3.2...HEAD
[1.3.2]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.2

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
