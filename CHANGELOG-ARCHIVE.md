# Changelog Archive

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [1.3.3] — 2026-09-30

### [chat-arvore-navegavel](openspec/changes/archive/2026-09-30-chat-arvore-navegavel) Chat AI reescrito sobre uma árvore de conhecimento navegável, com manifesto estável cacheável, protocolo JSON determinístico e navegação de documentos e notícias por nós

#### Added

- Capability `llm-chat-tree`: árvore de conhecimento cache-only (índice de caminhos em memória + conteúdo no cache de arquivos), manifesto estável (teto de 4K tokens) e protocolo JSON de navegação (`listar`, `obter`, `contar`, `existe`, `buscar`, `buscar_semantico`, `resetar_navegacao`) com gates de tokens e iterações.

#### Changed

- `llm-chat-llm`: a cascata de até três chamadas é substituída por um loop de navegação (até 10 ciclos) sobre a porta `LLMPort`; o contrato de resposta passa de `{resposta, documentos}` para `{resposta, solicitacoes}`; o prefixo estável (manifesto) e a estimativa de cache são preservados.
- `llm-chat-context`: a cascata de documentos e a máquina de `input_limitado` são substituídas por fontes de nós (conhecimento, fundamentos, documentos, notícias) e resolução por caminho.
- `llm-chat-tokens`: contadores e cotas separados de diálogo e navegação, rótulo com `nav: W/32K` e gate de janela total a 80%.
- `noticias-chat-context`: as notícias passam a ser o ramo `/noticias` navegável pela LLM; o filtro determinístico por pergunta e a escalada em duas camadas são substituídos por `listar`/`buscar`/`obter`.
- `llm-chat-rag`: ajuste de planejamento — a fonte vetorial deixa de compor o sufixo do prompt e passa a retroalimentar a op `buscar_semantico` da árvore, com a dependência re-apontada para `chat-arvore-navegavel`.

#### Removed

- **BREAKING** `llm-config` e `llm-gui`: o campo `input_limitado` é eliminado (config, caixa de seleção, confirmação de recursos); a chave antiga é ignorada na leitura.

### [escudo-inicializacao-mensagem](openspec/changes/archive/2026-09-30-escudo-inicializacao-mensagem) Escudo de inicialização passa a exibir mensagem de espera e a cobrir toda a janela, inclusive a barra superior de data

#### Changed

- O escudo de inicialização passa a exibir, dentro dele, uma mensagem de espera centralizada na janela.
- O escudo passa a cobrir de forma garantida toda a extensão do toplevel — incluindo a barra superior (rótulo "Data de referência", entrada de data, botões e comboboxes) —, sendo reerguido sobre os irmãos após a colocação.
- Popups auxiliares associados à barra superior (tooltip da data e calendário do `DateEntry`) não aparecem acima do escudo durante a inicialização.

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

## [1.3.1] — 2026-09-26

### [add-layer-architecture-guardrails](openspec/changes/archive/2026-09-25-add-layer-architecture-guardrails) Fundação do programa de arquitetura: teste de fronteira generalizado para todas as camadas, allowlist de violações legadas que só encolhe e convenção de view-model documentada

#### Added

- Teste de fronteira generalizado para `domain`, `application`, `infrastructure` e `presentation`, cobrindo os imports proibidos definidos em `specs/layer-boundaries/spec.md`.
- Allowlist explícita das violações legadas (arquivo de dados versionado), que só pode encolher; import novo fora do permitido reprova o teste.
- Verificação de que a allowlist está vazia como critério de fechamento do programa.
- Documentação da convenção de view-model (aplicação devolve dados prontos; apresentação formata/desenha).

#### Changed

- **BREAKING (interno)**: a partir daqui, violações de fronteira novas reprovam o quality gate.

### [clean-architecture-layering](openspec/changes/archive/2026-09-26-clean-architecture-layering) Change chapéu que fixa o contrato de fronteira entre camadas, a convenção de view-model, o guardrail com allowlist decrescente e o orçamento de testes de UI, coordenando os incrementos filhos

#### Changed

- Define o contrato de fronteira entre camadas (`domain`, `application`, `infrastructure`, `presentation`) e a regra de importação de cada uma.
- Define a convenção de view-model: `application` devolve dataclasses prontas; `presentation` apenas formata e desenha.
- Estabelece um guardrail de fronteira com allowlist de violações legadas que só pode encolher, zerada no incremento de fechamento.
- Restringe o escopo dos testes de UI a wiring, estado de widget/botão, empty-state e ciclo de thread/queue; lógica pura passa a ser testada em `test_domain`/`test_application`.
- Coordena os incrementos filhos na ordem fundação, Documentos, Notícias, Correlação/Rede, Dominância, Quadrante+VWAP, Amplitude de Preço, Fluxo Financeiro, Fundamentos, Chat e fechamento.
- **BREAKING (interno)**: imports entre camadas passam a ser validados por teste; violações novas reprovam o quality gate.

### [documentos-resumo-lote-persistente](openspec/changes/archive/2026-09-25-documentos-resumo-lote-persistente) Resumo em lote dos documentos pendentes passa a persistir cada resultado imediatamente após a geração, sobrevivendo a interrupções

#### Added

- Seam reutilizável no fluxo compartilhado (`DocumentFlowMixin` + `ResumosPendentesJob`): gerar e persistir no worker e apenas refletir em memória na thread do Tk.

#### Changed

- Cada resumo passa a ser gravado imediatamente após a geração, na thread de trabalho do lote, antes de processar o próximo documento.
- `JsonDocumentSummaryStore.salvar` torna-se segura a escritas concorrentes (lock), evitando *lost update* entre o lote e a pré-visualização individual.
- Interrupção por cancelamento, fechamento do aplicativo ou crash passa a preservar todos os resumos já gerados; perde-se no máximo o item em processamento.

### [enforce-clean-architecture-boundaries](openspec/changes/archive/2026-09-26-enforce-clean-architecture-boundaries) Fechamento do programa: imports de `infrastructure` restritos ao composition root via portas de `application` e allowlist de fronteira zerada

#### Added

- Portas de `application` para releases, configuração de LLM e clipboard, com adaptadores em `infrastructure` ligados no composition root.
- Testes puros em `tests/test_application` para as portas/casos de uso.

#### Changed

- A verificação de nova versão (`obter_ultima_release`) sai de `presentation/gui/app_about_actions.py` para uma porta de `application`, com a comparação de versões usando `domain.version.is_newer`.
- O diálogo de LLM deixa de importar `infrastructure.llm.config`/`factory` e passa a receber uma porta de configuração de `application`.
- A cópia de gráfico deixa de importar `infrastructure.clipboard_image` e passa a receber uma porta de clipboard de `application`.
- O composition root (`presentation/cli.py`, `presentation/main.py` e `presentation/gui/app_wiring.py`) constrói os adaptadores de infraestrutura e injeta as portas, continuando a única exceção a `presentation -> infrastructure`.
- A allowlist de fronteira (`tests/architecture/allowlist.txt`) é zerada; o teste passa a exigir zero violações e zero entradas.

### [noticias-cache-sharding](openspec/changes/archive/2026-09-25-noticias-cache-sharding) Caches JSON de texto e resumo das notícias particionados por ano e mês, reduzindo o custo de O(N²) e migrando o `NOTICIAS.json` anterior

#### Added

- Wrapper de shard de notícias que deriva o shard da chave estável (`noticias/<ANO>/<MES>/<hash>.html`) e delega aos stores JSON existentes.

#### Changed

- Os caches JSON de texto e resumo das notícias passam a ser particionados por ano e mês (`NOTICIAS-<ANO>-<MES>.json`), levando o custo de O(N²) para a soma dos quadrados por shard.
- A leitura em massa de resumos do catálogo passa a mesclar os shards.
- `NoticiaArquivo.ticker` continua `NOTICIAS` e o fluxo compartilhado (`DocumentFlowMixin`, `DocumentSummaryService`, chat) permanece inalterado.
- **BREAKING (formato do cache de notícias)**: o `NOTICIAS.json` anterior é migrado uma única vez para os shards, sem reconverter.

### [noticias-resumo-lote-ordenado](openspec/changes/archive/2026-09-25-noticias-resumo-lote-ordenado) Resumo em lote das notícias passa a seguir ordem explícita por grupo e da mais recente para a mais antiga, persistindo cada resumo imediatamente

#### Changed

- Ordem explícita do lote por grupo ("Censuras Públicas" → "Condições Excepcionais" → "Programas de Aquisição de Ações" → "Geral") e, dentro de cada grupo, da notícia mais recente para a mais antiga.
- A ordenação deixa de ser efeito colateral da inserção na árvore e passa a ser regra explícita, com desempate determinista para datas ausentes ou empatadas.
- Cada resumo é gravado imediatamente após a geração, no worker, reutilizando o seam de `documentos-resumo-lote-persistente`.
- Interrupção (cancelar, fechar, crash) preserva os resumos já gerados; perde-se no máximo o item em processamento.

### [refactor-chat-context-layers](openspec/changes/archive/2026-09-26-refactor-chat-context-layers) Montagem de contexto do chat movida para `application`; painel restrito a widget, sessão e thread

#### Added

- Montador de contexto em `application/chat/` que reúne conhecimento, fundamentos, cascata de documentos e fontes adicionais em um `ContextoChat`, com o gate de confirmação delegado a um callback.

#### Changed

- `chat/fundamentos.py`, `chat/documentos.py` e `chat/noticias.py` saem de `presentation` para `application/chat/`.
- `chat/conhecimento.py` passa a ser montado em `application/chat/`, com os textos de interface fornecidos pela apresentação como entrada.
- A extração de texto de documentos sai de `presentation/gui/charts/document_preview.py` para `application/document_preview.py`.
- `chat_panel.py` e `envio.py` consomem o montador de `application` e mantêm apenas widget, sessão, thread/fila, cancelamento, cópia/limpeza e o diálogo de confirmação.
- Testes puros de contexto migram para `tests/test_application`; os testes de `tests/test_presentation` ficam restritos a wiring, estado de widget e thread/queue.

### [refactor-correlation-network-layers](openspec/changes/archive/2026-09-26-refactor-correlation-network-layers) Extração de séries da rede de correlação movida para `application`; painel apenas desenha

#### Changed

- O módulo puro `network_data.py` sai de `presentation` para `application/network/`, como read-model pronto (`DadosRede`, `extrair_series`, mensagens e formatadores).
- `correlation_network_panel.py` consome o read-model de `application` e permanece apenas com o desenho (grafo, colorbar, legenda, estado vazio).
- Testes puros de `tests/test_presentation/test_network_data.py` migram para `tests/test_application`; o painel mantém apenas testes de UI.

### [refactor-documentos-layers](openspec/changes/archive/2026-09-26-refactor-documentos-layers) Entidades de catálogo para `domain`, catálogo e resumo em `application`; painel de documentos apenas desenha

#### Added

- Porta `CatalogoRepository` e caso de uso de consulta do catálogo em `application`, incluindo a montagem/ordenação e a derivação da chave estável.
- Porta `DocumentSummaryStore` em `application`; `JsonDocumentSummaryStore` e `JsonDocumentTextStore` passam a implementá-la.

#### Changed

- Entidades de catálogo (`DocumentoArquivo`, `CategoriaDocumentos`, `MesDocumentos`, `AnoDocumentos`, `CatalogoTicker`) saem de `infrastructure/document_catalog.py` para `domain/documents/`.
- `infrastructure/document_catalog.py` passa a implementar a porta varrendo o cache (apenas I/O), usando as entidades de domínio.
- `DocumentSummaryService` e `GuidanceService` saem de `presentation/gui/charts/` para `application`.
- `document_tree_panel` recebe as dependências por injeção pelo composition root, sem importar `infrastructure`.
- Testes puros de documentos migram para `tests/test_domain`/`tests/test_application`.

#### Removed

- Entradas correspondentes de `tests/architecture/allowlist.txt`.

### [refactor-dominance-panels-layers](openspec/changes/archive/2026-09-26-refactor-dominance-panels-layers) Construção de ranking/timeline e geometria das hastes movidas para `application`; painéis apenas desenham

#### Added

- Testes puros em `tests/test_application` para as funções movidas, sem `DISPLAY`.

#### Changed

- A construção pura do ranking (`build_rows`, `stem_lengths`) sai de `ranking_data.py` para `application/dominance/`, como view-model pronto (`RankingRow`).
- A construção pura da linha do tempo (`build_rows`, `direction_balance`) sai de `timeline_data.py` para `application/dominance/` (`TimelineRow`).
- A geometria/cor das hastes e a localização da linha sob o cursor saem de `dominance_data.py` para `application/dominance/`.
- `dominance_ranking.py` e `dominance_timeline.py` passam a consumir `application` e mantêm apenas o desenho.

### [refactor-flow-panels-layers](openspec/changes/archive/2026-09-26-refactor-flow-panels-layers) Extração de métricas e resumo do fluxo para `application`/`domain`; painel apenas orquestra e desenha

#### Added

- Testes puros em `tests/test_application` e `tests/test_domain` para as funções movidas, sem `DISPLAY`.

#### Changed

- `extract_session_metrics` sai de `financial_flow_helpers.py` para `application/flow/`, como view-model pronto (`SessionFlowMetrics` + `build_session_metrics`).
- `generate_summary` e os trechos `flow_intensity_part`, `close_position_part`, `dominance_part` e `conviction_part` saem do helper para `application/flow/`.
- `pressure_percentages` sai do helper para `domain`.
- `financial_flow_helpers.py` permanece com a formatação, o desenho e o tooltip, consumindo `domain`/`application`.
- `financial_flow_panel.py` passa a consumir os view-models e o resumo de `application`.

### [refactor-fundamental-table-layers](openspec/changes/archive/2026-09-26-refactor-fundamental-table-layers) Linhas, CSV e evolução dos fundamentos como view-models de `application`; a tabela apenas insere e copia

#### Changed

- `montar_linhas`, `montar_csv`, o layout de colunas e os formatadores saem de `fundamental_rows.py` e `fundamental_formatters.py` para `application/fundamental/`.
- A amostragem Fibonacci e a montagem das séries de evolução (`fundamental_evolution_data.py`) saem de `presentation` para `application`.
- `app_csv.py` passa a montar o CSV da tabela a partir do view-model de `application`.
- `controller_fundamental.py` recebe o adaptador de mercado por injeção do composition root.
- Testes puros (linhas, CSV, formatação e evolução) migram para `tests/test_application`.

#### Removed

- Entrada `presentation/gui/controller_fundamental.py -> infrastructure` de `tests/architecture/allowlist.txt`.

### [refactor-noticias-layers](openspec/changes/archive/2026-09-26-refactor-noticias-layers) Classificação e entidades de notícia para `domain`/`application`; painel de notícias apenas desenha

#### Changed

- A classificação de notícias sai de `infrastructure/b3/noticias_tipos.py` para `domain`.
- Entidades de catálogo e a ordenação do lote saem de `infrastructure`/`presentation` para `domain`/`application`.
- `infrastructure/b3/noticias_catalogo.py` permanece como adaptador de leitura, implementando a porta de catálogo e reaproveitando o read-model `montar_catalogo`.
- A montagem do índice compacto do chat e a intercalação por seção passam para `application`.
- `NoticiasPanel` recebe caso de uso e portas por injeção; `NoticiasTreeView` importa entidades de `domain`.
- Testes puros de notícias migram para `tests/test_domain`/`tests/test_application`.

#### Removed

- Três entradas de notícias de `tests/architecture/allowlist.txt`.

### [refactor-price-range-layers](openspec/changes/archive/2026-09-26-refactor-price-range-layers) Classificação de pregão para `domain`; normalização e dimensionamento permanecem em `presentation`

#### Added

- Testes puros em `tests/test_domain` para a classificação movida, sem `DISPLAY`.

#### Changed

- `classify_trend` e `classify_session` (com o auxiliar `median_value`) saem de `price_range_helpers.py` para `domain`, preservando as mesmas categorias.
- `normalize`, `efficiency_color`, `size_mapper`/`_constant_size` e o desenho permanecem em `presentation`.
- `price_range_helpers.py` passa a importar `classify_session` do `domain` em `draw_classification_text`.

### [refactor-quadrant-vwap-layers](openspec/changes/archive/2026-09-26-refactor-quadrant-vwap-layers) Quadrante para `domain`; dados de VWAP e trajetórias/dispersão para `application`; painéis apenas desenham

#### Added

- Testes puros em `tests/test_domain` e `tests/test_application`, sem `DISPLAY`.

#### Changed

- `classify_quadrant` (e a constante dos quadrantes) sai de `quadrant_data.py` para `domain`, passando a operar sobre primitivos (`clv`, `vwap_dist`).
- A preparação das trajetórias e dos pontos de dispersão do quadrante vai para `application`, como view-models prontos (`PontoQuadrante`).
- As contagens/interpretação/resumo (`count_quadrants`, `pick_interpretation`, `generate_summary`) saem para `application`, preservando os mesmos textos.
- A preparação dos dados de VWAP (`to_pct`, `collect_ticker_data`, `estimate_bucket_size`, `compute_violin_shapes`) sai para `application`, como read-model pronto (`DadosVwap`).
- `quadrant_chart.py` e `vwap_hist.py` consomem `domain`/`application` e mantêm apenas o desenho.

## [1.3.0] — 2026-09-25

### [correlation-cointegration-panel](openspec/changes/archive/2026-09-25-correlation-cointegration-panel) Nova sub-aba "Rede de Correlação" na "Análise Geral" com grafo force-directed, codificando a correlação assinada na cor da aresta e a cointegração (Engle-Granger + ADF em `numpy` puro) no estilo/espessura

#### Added

- Nova sub-aba "Rede de Correlação" na "Análise Geral", com grafo force-directed (nós = papéis, arestas = pares com relação relevante).
- Codificação visual dupla: cor da aresta = correlação de curto prazo assinada (colormap divergente, escala fixa `[-1, +1]`); estilo/espessura = cointegração de longo prazo (sólido/grosso quando cointegrado, tracejado/fino caso contrário).
- Cor do nó = comunidade da rede; tamanho do nó = centralidade (grau).
- Cálculo de correlação e cointegração (Engle-Granger + ADF) implementado em `numpy` puro, sem `statsmodels`/`scipy`.
- Rede calculada sobre o resultado já carregado na análise corrente, filtrado pelos tickers selecionados no Listbox, sem leitor de cache, download, janela própria ou job em background.
- Recálculo automático quando o período ou a amostragem mudam com a sub-aba ativa.
- Gates por densidade: correlação exige ≥ 30 observações alinhadas; cointegração exige ≥ 40, com diagnóstico de gaps (mín/mediana/máx em dias úteis) e span de calendário.
- `networkx` adicionado para layout (`spring_layout`), detecção de comunidades e centralidade.
- Texto de orientação (OrientationPanel) e a mesma barra de ferramentas (`ToolbarBR`) da sub-aba VWAP, incluindo "Copiar Gráfico".

### [llm-chat](openspec/changes/archive/2026-09-25-llm-chat) Aba de topo "Chat AI" que responde em linguagem natural sobre os dados carregados, os documentos em cache e o próprio FlowScope, com cascata de recuperação sobre resumos e texto e histórico de conversa em memória

#### Added

- Aba de topo "Chat AI", única e sempre visível, entre "Análise do Ticker" e "Sobre", como ponto único de entrada do chat.
- Sem seletor de escopo: o contexto cobre a watchlist completa e a LLM infere o ticker referido na pergunta.
- Contexto com três origens: conhecimento do próprio FlowScope, tabela de fundamentos carregada e documentos em cache (watchlist completa).
- Cascata de documentos: resumos curtos → resumos longos → texto integral dos alvos, com interrupção antecipada ao obter resposta.
- Histórico textual da conversa com teto de 10 mensagens e 8.000 caracteres; erros e avisos fora do histórico e sessão em memória, sem persistência.
- Confirmação ao usuário conforme a quantidade de documentos-alvo (até 3 prossegue; 4 a 7 lista os nomes; 8 ou mais informa a quantidade).
- Cabeçalho com "Limpar", "Copiar chat" e "Configuração"; campo de entrada e "Enviar" habilitados apenas com a LLM configurada e fundamentos carregados.
- Botão "Limpar" com confirmação (Sim/Não); "Limpar" e "Copiar chat" habilitados apenas quando há conteúdo textual.
- Bloqueio de "Limpar", "Copiar chat", "Configuração" e "Enviar" durante o envio, com restauração ao término ou cancelamento.
- Quadro de texto orientativo das abas "Chat AI" e "Sobre"; a cópia de dados CSV inclui o conteúdo do chat quando a aba está ativa.
- Respostas em campo somente-leitura com cursor, seleção e atalhos de teclado; erros da LLM na statusbar e no log.
- Caches da sub-aba "Notícias" oferecidos como fonte adicional de contexto do chat.

#### Changed

- Sem VectorStore, embeddings, chunker, indexação ou `--index`, itens que migram para a change `llm-chat-rag`.

### [llm-config-por-provedor](openspec/changes/archive/2026-09-25-llm-config-por-provedor) Persistência da configuração de completion por provedor no bloco `llm.chat`, com restauração da configuração salva ao trocar de provedor e migração do formato plano anterior

#### Added

- Mapa `providers` no bloco `llm.chat` com `api_url`, `model`, `api_key` e `rpm` por provedor, mantendo `provider` como a seleção ativa.
- Restauração automática da configuração salva ao trocar de provedor; sem configuração salva, aplica os defaults do preset e limpa a chave, sem herdar a de outro provedor.
- Selecionar `none` limpa os campos ativos sem apagar as configurações dos demais provedores, permitindo voltar a qualquer um e retomar o que foi salvo.
- Gravação em disco apenas ao clicar em "Salvar"; edições ainda não salvas ficam em memória durante a sessão do diálogo.
- Migração automática do formato plano (sem `providers`) na primeira gravação, sem perder a configuração existente.

#### Changed

- `load_llm_config()` continua devolvendo o dicionário plano resolvido do provedor ativo, preservando os consumidores atuais (factory, resumo de documentos, guidance e chat).

### [noticias-b3](openspec/changes/archive/2026-09-25-noticias-b3) Nova sub-aba "Notícias" na Análise Geral, com aquisição e cache do corpo dos artigos, pré-visualização, resumos por LLM e disponibilização como contexto do "Chat AI"

#### Added

- Sub-aba "Notícias" na Análise Geral com árvore, pré-visualização e botões "Atualizar", "Abrir", "I.A." e "Resumir pendentes".
- Categorias de topo "Geral", "Censuras Públicas", "Condições Excepcionais" e "Programas de Aquisição de Ações", cada uma seguindo a sub-estrutura ano → mês → categoria → item.
- Categoria "Geral" lista o Plantão B3 do último ano, somente casos excepcionais de mercado, com carga incremental dia a dia e marcadores persistidos da data mais antiga processada e da última carga.
- Fontes regulatórias ("Censuras Públicas", "Condições Excepcionais" e "Programas de Aquisição de Ações") carregadas com histórico completo e tolerância à falha individual.
- Cache próprio do HTML das notícias, reuso dos caches de texto e resumos da sub-aba "Documentos" e índice de metadados para exibição sem rede.
- Carga inicial somente do cache local; a listagem e a aquisição de novos itens ocorrem apenas pelo botão "Atualizar", em segundo plano.
- Status por categoria durante o "Atualizar", carga parcial preservada a cada item processado e escritas do índice agrupadas em lotes.
- Corpo do artigo da "Geral" extraído de `#conteudoDetalhe`, com resolução sob demanda de documentos vinculados da CVM RAD e do FNET.
- Extração de texto (HTML → texto), resumo curto/longo por LLM, pré-visualização e abertura do artigo no navegador.
- Conteúdo disponibilizado como fonte adicional de contexto da aba "Chat AI", cobrindo as quatro categorias, com o ticker inferido pela LLM.

## [1.2.0] — 2026-09-23

### [aba-sobre](openspec/changes/archive/2026-09-23-aba-sobre) Nova aba "Sobre" com informações institucionais, apresentação, links para repositório e log e verificação automática de nova versão

#### Added

- Nova aba de nível superior "Sobre", posicionada imediatamente após "Análise do Ticker", com conteúdo próprio de rolagem vertical e o painel de orientação à direita inalterado.
- Conteúdo da aba com ícone da aplicação, nome e versão (`FlowScope vX.Y.Z`), data de lançamento em formato ISO, licença GNU GPLv3, texto de apresentação derivado do `README.md`, botão para o repositório no GitHub e botão para abrir o log da aplicação.
- Verificação automática de nova versão ao abrir a aba, no máximo uma vez por sessão e em background, exibindo aviso e botão para a página da release quando houver versão mais recente.
- Nova constante `__release_date__` em `src/flowscope/__init__.py`, atualizada pelo fluxo de release junto de `__version__`.

#### Fixed

- Metadados de licença do `pyproject.toml` corrigidos de MIT para `GPL-3.0-only`, com elevação do `setuptools` mínimo para 77 (PEP 639).

### [analise-short-interest](openspec/changes/archive/2026-09-23-analise-short-interest) Adiciona quatro colunas de short interest (Shorts%, Volume de Shorts, Fechamento Shorts e Risco Fechamento) à tabela de Fundamentos

#### Added

- Quatro novas colunas à tabela da sub-aba "Fundamentos", entre `Tendência do dividendo` e `FFO/Receita (12m)`: `Shorts%`, `Volume de Shorts`, `Fechamento Shorts` e `Risco Fechamento`.
- `Shorts%` = `(Ações Alugadas ÷ Free Float) × 100`, numérico em percentual com uma casa decimal, e `Volume de Shorts` como classificação categórica em cinco rótulos.
- `Fechamento Shorts` (SIR) = `Ações Alugadas ÷ Volume Médio Diário de Negociação`, em dias com sufixo `d`, e `Risco Fechamento` como classificação categórica nos mesmos cinco rótulos.
- Free float obtido do CVM FRE (`Quantidade_Total_Acoes_Circulacao`), com fallback para o total emitido; ações alugadas obtidas da B3 (BTBLendingOpenPosition) e volume médio calculado em memória a partir do `daily_data` injetado.
- Escopo por tipo (`Papel`, `FII`, `ETF`/`FIAGRO`/`BDR`), resultando em `N/A` na coluna quando o insumo não existir, sem impedir as demais.

#### Changed

- **BREAKING (colunas)**: a ordem das colunas da tabela fundamentalista muda, e o CSV copiado e o texto de orientação da sub-aba passam a incluir as novas colunas.
- Bump da versão de schema do cache histórico de fundamentos para persistir os novos campos estruturados.

### [cache-texto-documentos](openspec/changes/archive/2026-09-22-cache-texto-documentos) Cache persistente do texto extraído por documento, eliminando a reconversão e curto-circuitando o processamento quando não há texto extraível

#### Added

- Cache persistente do texto extraído por documento em `~/.cache/flowscope/document-texts/<TICKER>.json`, com escrita atômica e tolerância a arquivo ausente ou corrompido, no mesmo modelo de `document_summaries.py`.
- Marcador `Sem texto extraível para pré-visualização.` gravado no cache quando não houver texto, tratado por um predicado compartilhado `tem_texto()`.

#### Changed

- A pré-visualização passa a ler o texto do cache e só converte (`pypdf`/`BeautifulSoup`) em *miss*, gravando o resultado para os acessos seguintes, sem invalidação por alteração do arquivo.
- Sem texto extraível, não se gera resumo LLM, não se tenta extrair guidance e não se executa qualquer outro processamento do texto, mantendo disponível a abertura do documento.
- A change `fii-guidance-informacoes-adicionais` passa a consumir o texto do novo cache, em vez de reextrair, e a não avaliar guidance quando não houver texto extraível.

#### Fixed

- Corrige a barra de rolagem vertical da árvore e do campo de texto da sub-aba "Documentos", empacotando a barra primeiro (ou por `grid` com pesos) para torná-la visível e funcional, inclusive com rolagem pela roda do mouse.

### [centralizar-controle-cursor](openspec/changes/archive/2026-09-22-centralizar-controle-cursor) Centraliza a política de estado ocupado no presenter como máquina de estado `IDLE <-> BUSY`, eliminando caminhos diretos de cursor

#### Added

- Máquina de estado `IDLE <-> BUSY` no presenter, com contagem de referência e context manager `busy()` que garante entrada/saída balanceadas mesmo em exceção.

#### Changed

- Removidos os caminhos diretos de cursor (`controller.on_ticker_edit`, `actions._copy_chart`) que furam o contador do presenter.
- Garantia de que todo `on_fundamental_started` tenha exatamente um `on_fundamental_finished`, inclusive quando `job.iniciar()` ou `on_progress` falham após o incremento.
- Watchdog de inatividade/liveness e tratamento por mensagem estendidos ao job de documentos, sem impedir `on_operation_finished`.
- Snapshot da view normalizado para ignorar cursores transitórios geridos pelo Tk (`hresize`, `sb_*`) e reafirmação do cursor enquanto ocupado em `<Motion>`.
- Teste de GUI da sincronização entre os dois `Treeview` da tabela de Fundamentos e teste de cobertura que enumera as abas/sub-abas construídas.

### [corrigir-botao-resumir-durante-lote](openspec/changes/archive/2026-09-23-corrigir-botao-resumir-durante-lote) Mantém o botão "Resumir pendentes" desabilitado durante o lote, reabilitando-o apenas ao término

#### Added

- Predicado de "resumo em lote em andamento" injetado no painel de documentos, no mesmo padrão de callbacks já usados (`resumir_callback`, `ia_callback`).

#### Fixed

- O estado derivado do botão "Resumir pendentes" passa a considerar o lote em andamento, mantendo-o desabilitado em qualquer reavaliação durante o processamento (documento aplicado, resumo individual concorrente ou recarregamento do painel) e reabilitando-o somente ao término, conclusão ou interrupção.
- Cobertura de testes para a permanência do estado desabilitado ao longo do lote e para a reabilitação ao término.

### [corrigir-vazamento-cursor-grid-fundamentos](openspec/changes/archive/2026-09-23-corrigir-vazamento-cursor-grid-fundamentos) Corrige o cursor de espera preso sobre o grid rolável da sub-aba "Fundamentos"

#### Fixed

- Captura do cursor de repouso torna-se robusta a valores que o Tk devolve como lista Tcl (por exemplo `('sb_h_double_arrow',)`), filtrando cursores transitórios de separador/sash antes de usá-los como baseline.
- Restauração do cursor nunca deixa o widget preso em "watch": se a restauração do baseline falhar, o widget volta ao cursor padrão.
- Teste de regressão de GUI cobrindo o ponteiro sobre o separador no início da operação.

### [fii-guidance-informacoes-adicionais](openspec/changes/archive/2026-09-23-fii-guidance-informacoes-adicionais) Cache de guidance por FII avaliado ao ler o Relatório Gerencial na sub-aba "Documentos" (LLM preferencial com fallback determinístico) e exibido em "Informações adicionais"

#### Added

- Cache de guidance por FII em `~/.cache/flowscope/guidance/<TICKER>.json`, com informação inicial vazia, escrita atômica e tolerância a ausência/corrupção.
- Avaliação do Relatório Gerencial ao ser lido na sub-aba "Documentos" (categoria `Relatorio`), lendo o texto do cache de documentos e sem reextrair o PDF; documento sem texto extraível não dispara avaliação.
- Flag de análise de guidance via LLM (`llm.guidance.enabled`), desabilitada por padrão: com o recurso disponível e funcional, a LLM faz a avaliação específica; caso contrário, usa-se a extração determinística (`pypdf` + regex) do valor, do período de validade e da data do relatório.
- Escopo restrito à palavra literal `guidance` e a ativos do tipo `FII`.

#### Changed

- A coluna `Informações adicionais` de FIIs passa a exibir um item `Guidance ...` lido do cache, sem calcular guidance na carga de dados nem na renderização; cache vazio → item omitido.
- O botão "Resumir pendentes" também avalia o guidance dos Relatórios Gerenciais pendentes já processados, reaproveitando o texto preparado pelo lote e sem interromper o lote em caso de falha; Relatórios já resumidos continuam atualizados apenas ao serem lidos.

### [interromper-processamento](openspec/changes/archive/2026-09-23-interromper-processamento) Botão de interromper na barra de status com cancelamento cooperativo de todos os processamentos em background ativos

#### Added

- Botão de interromper (ícone `process-stop.png`) na barra de status, imediatamente à esquerda da barra de progresso, visível apenas enquanto houver ao menos um job cancelável em background ativo.
- Um único clique cancela todos os processamentos em background ativos (fundamentalista, documentos e resumos em lote).
- Cancelamento cooperativo real com token compartilhado observado no topo dos loops de trabalho, encerrando o worker por uma exceção dedicada (`OperacaoCancelada`), sem ser confundido com falha recuperável.
- Ao cancelar, barra e botão somem, controles e cursor são restaurados, os flashes de sucesso são suprimidos e a barra de status exibe "Processamento interrompido.".

### [melhorias-evolucao-fundamentos](openspec/changes/archive/2026-09-23-melhorias-evolucao-fundamentos) Adiciona o painel `Shorts%` aos small multiples de "Evolução dos Fundamentos" e tooltip de hover, e corrige o formato de data para dia/mês/ano

#### Added

- Oitavo painel `Shorts%` nos small multiples da sub-aba "Evolução dos Fundamentos", representando a evolução de `AnaliseFundamental.short.shorts_pct` em percentual com uma casa decimal.
- Tooltip de hover em todos os painéis da sub-aba, exibindo a data e o valor do ponto sob o cursor.

#### Changed

- Texto do OrientationPanel da sub-aba e documentação (`panels.md`, `TAB_CONTENT`/`TAB_CONFIGS`) atualizados para refletir os oito painéis e o novo indicador.

#### Fixed

- Rótulo de data dos eixos dos gráficos corrigido de `MM/AA` (`%m/%y`) para `DD/MM/AA` (`%d/%m/%y`).

### [mensagens-amigaveis-erros-llm](openspec/changes/archive/2026-09-23-mensagens-amigaveis-erros-llm) Humaniza as mensagens de erro de I.A. por categoria de falha e introduz `LLMServiceUnavailableError` para sobrecarga/5xx do provedor

#### Added

- Novo subtipo de domínio `LLMServiceUnavailableError` para sobrecarga/erro 5xx do provedor, exportado pelo domínio de LLM.
- Helper de apresentação (erro → texto) que traduz cada categoria de falha em mensagem amigável, sem que a GUI dependa do liteLLM.

#### Changed

- Mensagens exibidas no botão "Resumir pendentes" e no campo de status do botão "Testar" do diálogo "I.A." passam a ser humanizadas, mantendo `str(exc)` técnico e os registros de log inalterados.
- `ServiceUnavailableError` e `InternalServerError` do liteLLM passam a mapear para o novo subtipo, antes da entrada genérica `APIError`.
- Texto bruto preservado para exceções que não forem da camada de LLM (ex.: falha de conversão de PDF) e banner de depuração do liteLLM (`Give Feedback / Get Help`, `LiteLLM.Info`) silenciado no terminal.

### [resumir-pendentes-documentos](openspec/changes/archive/2026-09-22-resumir-pendentes-documentos) Botão "Resumir pendentes" para processar em lote todos os documentos do ticker sem resumo, com progresso e interrupção segura

#### Added

- Botão "Resumir pendentes" na barra de controles da sub-aba "Documentos", imediatamente após o botão "I.A.", sempre visível e habilitado apenas quando a LLM está configurada, existe documento sem `long_summary` e nenhum lote está em andamento.
- Processamento em background, em duas fases (preparar o texto reutilizando o cache e gerar o resumo) de todos os documentos do ticker sem `long_summary`, persistindo os resumos e refletindo-os no catálogo em memória.
- Andamento exibido na barra de status com a barra de progresso, uma fase por vez, mantendo botões e cursor bloqueados pela autoridade única de estado ocupado.
- Interrupção do lote em qualquer erro, reportando na barra de status o documento e o motivo da falha e liberando os controles.
- Pulo de documentos sem texto extraível (`SEM_TEXTO`), sem chamar a LLM, contabilizando-os no desfecho.

#### Changed

- Estado do botão reavaliado após salvar a configuração de I.A. e ao término do lote.

## [1.1.0] — 2026-09-18

### [documentos-resumos](openspec/changes/archive/2026-09-18-documentos-resumos) Resumos curto e longo dos documentos via LLM, com lista Markdown dos agrupamentos, pré-visualização composta, geração sob demanda persistida, campo de texto copiável e persistência da configuração de I.A.

#### Added

- Novos campos `short_summary` (até 280 caracteres, nulo quando não gerado) e `long_summary` (até 1500 caracteres, nulo quando não gerado) no catálogo de documentos, com persistência em `~/.cache/flowscope/document-summaries/<TICKER>.json` (JSON por ticker, escrita atômica, chave = caminho relativo à raiz de cache).
- Novo serviço `ResumirDocumentoUseCase` que recebe o texto de um documento e produz os dois resumos via `LLMPort`, consumindo a base da change `llm-core`.

#### Changed

- Ao selecionar um agrupador da árvore (ticker, ano, mês ou categoria), o campo de texto exibe uma lista Markdown dos documentos contidos, com níveis relativos e o `short_summary` de cada documento; sem resumo, exibe a mensagem de indisponibilidade condicional.
- Ao selecionar um documento, o campo de texto exibe `long_summary`, linha em branco, `---`, linha em branco e o texto integral; sem `long_summary`, gera os dois resumos via LLM (fórmula XYZ) e os persiste, ou exibe a mensagem de indisponibilidade quando a LLM não está configurada/funcional.
- O campo de texto permanece somente-leitura, mas passa a aceitar atalhos de seleção e cópia (Ctrl+A, Ctrl+C, Shift+setas) e a exibir o cursor de foco.
- O botão "Copiar dados CSV" passa a copiar o conteúdo do campo de texto quando a sub-aba "Documentos" está ativa, ficando habilitado nessa sub-aba mesmo sem dados da B3.

#### Fixed

- Vincular explicitamente o atalho Ctrl+A no widget, pois no X11 o evento virtual `<<SelectAll>>` do Tk mapeia para Ctrl+barra e não para Ctrl+A.
- Fazer a configuração de I.A. salva pelo diálogo persistir de fato: "Salvar" grava o bloco `llm.chat` e fecha o diálogo, e a gravação de preferências da interface deixa de sobrescrever o bloco `llm`.

### [llm-core](openspec/changes/archive/2026-09-18-llm-core) Camada base reutilizável de LLM com porta `LLMPort`, adaptador liteLLM com presets de provedores, rate limiting por RPM, bloco `llm.chat` no `config.json`, exceções tipadas e diálogo de I.A. na sub-aba Documentos

#### Added

- Novo grupo opcional `[llm]` em `pyproject.toml` com `litellm` (`pip install flowscope[llm]`).
- Novo domínio `domain/llm/`: porta genérica `LLMPort` (completion) e hierarquia de exceções (`LLMUnavailableError`, `LLMConfigurationError`, `LLMCommunicationError`, `LLMProviderError`, `LLMRateLimitError`).
- Nova infraestrutura `infrastructure/llm/`: presets de provedores (`none`, `openai`, `gemini`, `copilot`, `claude`, `deepseek`, `ollama`, `custom`), adaptador `LiteLLMChatAdapter` via `litellm.completion()` com `custom_llm_provider`, rate limiter configurável (RPM, default 5), load/save de config, detecção das dependências `[llm]` e factory `create_llm_provider(config)`.
- Bloco `llm.chat` no `~/.flowscope/config.json` com `provider` (default `none`), `api_url`, `model`, `api_key` e `rpm`, preservando as demais preferências do arquivo.
- Diálogo de configuração de LLM na GUI (modal e não redimensionável) com dropdown de presets, `api_url`, `model`, chave de API mascarada, RPM, botão "Salvar" e botão "Testar"; as falhas do teste também são registradas em log (nível aviso, no logger `flowscope`, sem a chave de API).
- Botão "I.A." na barra da sub-aba "Documentos", logo após "Abrir documento", que abre o diálogo de configuração e segue o bloqueio global dos demais botões durante as cargas de dados.

#### Changed

- O executável do PyInstaller passa a embutir o liteLLM: o alvo `build` instala `[llm]` e a especificação coleta submódulos e arquivos de dados do litellm, incluindo o pacote de plugins `tiktoken_ext.openai_public`, garantindo os recursos de I.A. em máquinas que rodam apenas o binário (sem Python/pip).
- README passa a documentar a instalação `pip install flowscope[llm]`.
- A change `llm-chat` passa a herdar `llm-core` (remove a duplicação de cliente de chat, config e diálogo, mantendo embeddings, VectorStore, RAG e o ChatPanel).

## [1.0.0] — 2026-09-17

### [corrigir-cursor-fundamentos](openspec/changes/archive/2026-09-17-corrigir-cursor-fundamentos) Corrige o cursor de espera e os controles que ficavam presos quando uma análise fundamentalista em background era substituída por outra antes de concluir

#### Changed

- Compensar o ciclo de vida do job fundamentalista substituído: todo `on_fundamental_started` deve ter exatamente um `on_fundamental_finished` correspondente, mesmo quando um novo job assume o lugar do anterior.
- Impedir que a análise fundamentalista manual (botão "Atualizar fundamentos") deixe os controles habilitados: os botões passam a ser desabilitados já no início da análise, e um novo disparo é bloqueado enquanto um job estiver ativo.
- Cobrir a regressão com testes de controller/presenter e um teste de GUI (quando houver display) verificando que o cursor do `Treeview` da tabela de Fundamentos volta ao valor original.

### [documentos-aquisicao](openspec/changes/archive/2026-09-17-documentos-aquisicao) Orquestração da aquisição sob demanda dos documentos de um ticker, escolhendo a fonte pelo tipo (ações/BDR via material facts; FII via documentos relevantes e informe mensal) e gravando nos caches existentes

#### Added

- Nova orquestração de aquisição sob demanda dos documentos de um ticker, escolhendo a fonte pelo tipo: ações/BDRs via material facts (`GetMaterialFacts`) com download do PDF no visualizador da CVM e validação `%PDF`; FIIs via documentos relevantes (`GetReportsRelevants`) e informe mensal estruturado (HTML).
- Gravação nos caches existentes: `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf` e `<cache>/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`.

#### Changed

- Ao abrir a sub-aba "Documentos", exibir somente os documentos constantes no catálogo de leitura do cache do ticker apresentado (sincronizado com "Evolução dos Fundamentos"), sem acionar download.
- Acionar a aquisição apenas sob demanda pelo botão "Atualizar": buscar e baixar uma janela de 12 meses de documentos do ticker até a data de referência, reutilizando sem novo download os que já estiverem em cache, em worker, com remontagem da árvore ao final.
- Durante a execução do "Atualizar", desabilitar os botões da aplicação, ativar o cursor de espera (hourglass) e atualizar a barra de status e a barra de progresso com o andamento do processo; restaurar os controles ao término.
- Integrar os botões "Atualizar" e "Abrir documento" da sub-aba ao mesmo mecanismo de bloqueio global dos demais botões, ficando desabilitados também durante as cargas de dados e demais operações da aplicação.
- Renomear o botão de abertura para "Abrir documento", habilitando-o somente quando um documento estiver selecionado.
- Reutilizar `B3FundosClient` (resolução de ticker/codeCVM, `GetReportsRelevants`, `GetMaterialFacts`), os provedores `DocumentosRelevantesProvider` e `InformeMensalArquivoProvider`, o catálogo `DocumentCatalog` e o mecanismo CVM `ExibirPDF`.
- Limitar o timeout das requisições de documento do FundosNet (PDF e HTML) para que uma conexão que aceita e não responde falhe rápido e o retry reabra a conexão, em vez de travar a aquisição por dezenas de segundos por tentativa.
- Sem nova fonte para tickers sem documentos: falha de rede ou ausência de dados resulta em cache vazio, sem erro.

#### Fixed

- Corrigir a resolução `ticker → codeCVM` para consultar `GetInitialCompanies` (endpoint real do cadastro de empresas da B3) filtrando por `company` e casando o registro cujo `issuingCompany` é a raiz do ticker; a chave de cache passa a ser versionada para descartar `None` envenenado por execuções anteriores.
- Corrigir o payload do `GetMaterialFacts` para os nomes de campo aceitos pela API (`language`, `dateInitial`, `dateFinal`, `category`), sem os quais a listagem retorna vazia.

### [documentos-relevantes](openspec/changes/archive/2026-09-17-documentos-relevantes) Listagem de documentos não estruturados da B3 (Assembleias, Comunicados, Fatos Relevantes e Relatórios) via `GetReportsRelevants`, com download validado e cache em árvore por ticker/ano/mês/categoria

#### Added

- Novo método `listar_documentos_relevantes(id_fnet, data_inicio, data_fim, category)` no `B3FundosClient`, usando `GetReportsRelevants` com iteração pelas 4 categorias (1=Fatos Relevantes, 2=Assembleias, 3=Comunicados, 7=Relatórios), paginação e cache de listagem (TTL 1 dia).
- Download dos PDFs via `exibirDocumento?id=` com validação de assinatura `%PDF`.
- Cache binário em `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`, sem expiração.
- Nova entidade `DocumentoRelevante` com metadados (ticker, id, categoria, descrição, datas, url).
- Mapeamento de categorias da API para nomes e slugs de pasta.

#### Changed

- Ticker-agnóstico: retorna lista vazia quando a resolução falha ou o ticker não tem documentos.

#### Removed

- Remover do escopo a preparação para o `llm-chat` (`DocumentoRelevante.to_text()`, `RelevantesSource`/`DocumentSource`, extração de texto para embedding), transferida para a change `llm-chat`.

### [fix-fundamentos-fiagro-bdr](openspec/changes/archive/2026-09-17-fix-fundamentos-fiagro-bdr) Preenche os campos de Fundamentos de FIAGROs e BDRs, resolvendo identidade B3 multi-tipo, proventos `fii_proventos.php` e dividendos de BDR via Plantão de Notícias

#### Added

- Nova fonte de dividendos para BDRs via **Plantão de Notícias da B3**: lista `Aviso aos Acionistas` mês a mês, baixa o PDF do documento na CVM (POST `ExibirPDF`, base64), cacheia por ticker/ano/mês, extrai último dividendo, dividendo anterior, data-com, ISIN, depositário e empresa, e calcula P/L e Dividend Yield com anualização trimestral (×4).

#### Changed

- Resolução de fundo na B3 passa a iterar os tipos de fundo `FII`, `FIAGRO`, `FIP` e `FIDC`, desbloqueando a cadeia B3/CVM para FIAGROs (nome, CNPJ, administrador, gestor, patrimônio, cotas, cotistas, indexadores e proventos B3).
- Histórico de proventos do Fundamentus passa a ler `fii_proventos.php` para FIIs/FIAGROs (tabela `Última Data Com`/`Tipo`/`Data de Pagamento`/`Valor`), preenchendo data-com, dividendo anterior, tendência e o P/L derivado.
- Classificação determinística de FIAGRO passa a reconhecê-los como `FII` com sub-tipo `FIAGRO`, eliminando `Desconhecido` no fallback e mantendo-os fora da elegibilidade FFO.
- A sub-aba Fundamentos passa a exibir, para BDRs, o sub-tipo `BDR`, o nível do programa (ex.: `Nível I Não Patrocinado`) e a observação fiscal do aviso (dedução de IR/IOF/tarifa) em `Informações adicionais`, e, quando não houver identidade fiscal, o depositário (ex.: `Banco B3 S.A.`), a empresa (ex.: `Exxon Mobil Corporation`) e o ISIN em `Dados fiscais`.

### [informe-mensal](openspec/changes/archive/2026-09-17-informe-mensal) Persistência em arquivo do HTML do Informe Mensal Estruturado (type=40) da B3, organizada por ticker/ano/mês, para leitura pelo catálogo de documentos

#### Added

- Persistir o HTML do informe mensal em `~/.cache/flowscope/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`, com ano/mês derivados da data de referência do documento.
- Expor a leitura dessa árvore (existência, caminho e conteúdo) para o catálogo de documentos.

#### Changed

- Reutilizar a listagem type=40 e o download HTML já existentes no `B3FundosClient`, **sem alterar** as entidades de leitura (`B3InformeMensal`, parser e repositório).

#### Removed

- Remover do escopo: domínio rico (`Carteira`, `Resultados`, `Indicadores`, `InformeMensal`), value object `Percentual`, `InformeMensalRepository`/`ExtrairInformeMensalUseCase`, parser multi-tabela, CLI `--informe-mensal` e `to_text()`/preparação de VectorStore (transferida para `llm-chat`).

### [reorganizacao-abas-ticker](openspec/changes/archive/2026-09-17-reorganizacao-abas-ticker) Reorganiza as sub-abas da Análise do Ticker e torna a linha selecionada na tabela de Fundamentos a fonte única do ticker analisado

#### Changed

- Mover a sub-aba "Fundamentos" para a **primeira** posição na aba "Análise Geral".
- Reordenar as sub-abas da "Análise do Ticker": "Evolução dos Fundamentos" em primeiro e "Documentos" em último.
- Deixar **invisíveis** as três sub-abas sem painel implementado — "Participação Institucional", "Eficiência do Movimento" e "Resumo Geral" — que têm changes dedicadas (`participation-negociacoes`, `eficiencia-do-movimento`, `diagnosis-panel`).
- Tornar a linha selecionada na tabela da sub-aba "Fundamentos" a **fonte única** do ticker analisado em todas as sub-abas da "Análise do Ticker" (Dominância, Amplitude, Fluxo, Evolução dos Fundamentos e Documentos) e na cópia CSV dessa aba.
- Desvincular o ticker analisado da seleção na TickerList: a lista continua definindo **quais linhas** aparecem na tabela de Fundamentos e governa a "Análise Geral", mas não define mais o ticker das sub-abas por ticker.
- Ao carregar os fundamentos, **auto-selecionar a primeira linha** da tabela quando houver dados; sem dados, permanecer sem seleção e sem ticker analisado.
- Manter o duplo-clique na linha de Fundamentos como atalho: seleciona o ticker e navega para "Análise do Ticker" → "Evolução dos Fundamentos".
- **BREAKING** (comportamento observável): a seleção na TickerList deixa de atualizar as sub-abas da "Análise do Ticker"; o requisito correspondente é removido e substituído.

### [visualizacao-documentos](openspec/changes/archive/2026-09-17-visualizacao-documentos) Adiciona a sub-aba Documentos na Análise do Ticker com catálogo hierárquico de caches, pré-visualização textual e abertura no aplicativo padrão

#### Added

- Catálogo de documentos que varre as raízes de cache (`bdr/`, `informe-mensal/`, `documentos-relevantes/`) e normaliza os arquivos em uma hierarquia `ticker → ano → mês → categoria → arquivos`, com tipo (`pdf`/`html`) e caminho.
- Nova sub-aba **"Documentos"** na "Análise do Ticker" com uma árvore hierárquica, o nome do ticker no topo e as categorias derivadas da fonte/ pasta.
- Pré-visualização textual em caixa de texto somente-leitura ao selecionar um arquivo, com extração sob demanda (HTML→texto; PDF→`pypdf`) executada fora da thread da interface.
- Abertura do arquivo no aplicativo padrão do sistema operacional (PDF→leitor de PDF; HTML→navegador) por duplo-clique, tecla Enter ou botão "Abrir".
- Ordenação (ano/mês decrescentes, categorias alfabéticas, arquivos do mais recente ao mais antigo), estado vazio e atualização manual.

## [0.9.0] — 2026-09-15

### [evolucao-fundamentos](openspec/changes/archive/2026-09-15-evolucao-fundamentos) Sub-aba "Evolução dos Fundamentos" na aba "Análise do Ticker" com small multiples da evolução temporal dos campos Cotação, VP, P/VP, DY, Último dividendo, Nº de cotistas e Nº de cotas

#### Added

- Criar a sub-aba "Evolução dos Fundamentos" na aba "Análise do Ticker", exibindo a evolução temporal (timeseries) dos campos Cotação, VP, P/VP, DY, Último dividendo, Nº de cotistas e Nº de cotas para o ticker selecionado.

#### Changed

- Ler os dados exclusivamente do cache histórico de fundamentos, sem qualquer aquisição de rede ao abrir a sub-aba.
- Amostrar as datas do cache por Fibonacci de forma acumulada a partir da observação mais recente (gaps de 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377 dias), aproximando cada alvo para a data de cache mais próxima e incluindo sempre a mais antiga e a mais recente, exibidas em ordem crescente.
- Representar os campos em small multiples (um mini-gráfico de linha por campo, eixo X de datas compartilhado e escala própria), preservando a leitura dos valores absolutos por um leigo.
- Permitir que o duplo clique em uma linha da tabela da sub-aba "Fundamentos" (aba "Análise Geral") fixe o ticker e torne ativa a sub-aba "Evolução dos Fundamentos".
- Popular a sub-aba de forma preguiçosa (somente quando selecionada), funcionando apenas com o cache mesmo sem carga B3 corrente.
- Exibir estado vazio quando não houver histórico retido para o ticker e preencher o quadro de texto orientativo da sub-aba no mesmo padrão explicativo das demais.

### [fundamentos-cache-historico](openspec/changes/archive/2026-09-15-fundamentos-cache-historico) Cache histórico estruturado da tabela de Fundamentos por `(ticker, data)`, com read-through, retenção de 365 dias e atualização forçada

#### Added

- Introduzir um cache estruturado do resultado da análise fundamentalista (o conteúdo da linha da tabela "Fundamentos"), chaveado por `(ticker, data escolhida na GUI)`, com a `data_referencia` guardada dentro do registro.

#### Changed

- Persistir o `AnaliseFundamental` estruturado (não os valores formatados), com `schema_version` por observação, em um arquivo JSON por ticker contendo um mapa `data -> observação`.
- Reter um histórico deslizante de 365 dias, com prune na escrita e observações expiradas ignoradas na leitura.
- Integrar o cache como read-through no `FundamentalAnalysisUseCase`: em HIT, pular todo o pipeline de aquisição; em MISS, executar o caminho atual e registrar.
- Nunca gravar observações com `erro`; observações parciais (sem identidade do Fundamentus) podem ser sobrescritas no mesmo dia; observações completas são imutáveis no dia (first-write-wins).
- Tornar a leitura estrita para o HIT do dia (exige `schema_version` atual) e tolerante para consultas de histórico (best-effort, marcando a versão).
- Expor uma porta de recuperação (`obter`, `historico`, `datas`, `registrar`) para as futuras consultas de evolução do ticker.
- Ligar o cache por padrão e oferecer um caminho explícito de bypass para forçar recomputo e sobrescrever a observação do mesmo dia.
- Aplicar a todos os tickers (FII e Papel).

### [fundamentos-numero-cotas](openspec/changes/archive/2026-09-15-fundamentos-numero-cotas) Adiciona a coluna `Nº de cotas` (quantidade de cotas/ações emitidas) antes de `Nº de cotistas`, priorizando B3/CVM para FIIs e o Fundamentus para Papéis

#### Added

- Adiciona a coluna `Nº de cotas` imediatamente antes de `Nº de cotistas`, alinhada à direita e formatada como inteiro com separador de milhar.

#### Changed

- Expõe no Fundamentus a quantidade de cotas/ações emitidas: `Nro. Cotas` (FII) e `Nro. Ações` (Papel), normalizados em `Decimal`.
- Resolve a quantidade por tipo de ativo: para **FII**, prioriza a B3 (Informe Mensal) e a CVM como fallback, usando o Fundamentus como fallback final; para **Papel**, usa o Fundamentus (única fonte disponível), exibindo `N/A` quando ausente.
- Propaga o valor resolvido por `AnaliseFundamental.cotas`, reutilizando o `PatrimonioFii` já buscado e memorizado (sem novo acesso à rede).
- Atualiza a lista/ordem de colunas, o alinhamento numérico e o quadro de orientações da sub-aba "Fundamentos".
- A contagem de colunas passa de 29 (2 fixas + 27 roláveis) para 30 (2 fixas + 28 roláveis).

## [0.8.2] — 2026-09-14

### [fundamentos-ffo-receita](openspec/changes/archive/2026-09-14-fundamentos-ffo-receita) Recalcula o Dividend Yield de FII pelo último dividendo e substitui FFO Yield, P/FFO e Dividend Payout pelas razões FFO/Receita, Dividendos/Receita e Dividendos/FFO

#### Added

- Adicionar as colunas `FFO/Receita (12m)`, `FFO/Receita (3m)`, `Dividendos/Receita (12m)`, `Dividendos/Receita (3m)`, `Dividendos/FFO (12m)` e `Dividendos/FFO (3m)`, em notação percentual com uma casa decimal, calculadas apenas para Tipo `FII` (Tipo `Papel` exibe `N/A`).

#### Changed

- Recalcular o Dividend Yield de FIIs como `(último dividendo × 12) / P (Cotação)` quando o último dividendo e a cotação existirem; caso contrário manter o Dividend Yield do Fundamentus, preservando os fallbacks existentes para Tipo `Papel`.
- Tratar insumos negativos com texto na célula (`Receita negativa`, `FFO negativo` ou `Receita e FFO negativos`), exibindo `N/A` para divisão por zero e para dado ausente.
- Redefinir o `FFO Trend` como a diferença em pontos percentuais entre `FFO/Receita (3m)` e `FFO/Receita (12m)`, classificada nas cinco faixas existentes, posicionada após `FFO/Receita (3m)`.
- Expor `Receita` e `Rend. Distribuído` (12m e 3m) do Fundamentus na composição de campos fundamentalistas, tratando `Rend. Distribuído` como Dividendos.
- Atualizar o quadro de orientações da sub-aba "Fundamentos" para as novas colunas e sua leitura.

#### Removed

- Remover as colunas `FFO Yield`, `P/FFO` e `Dividend Payout (DY/FFOY)`.

## [0.8.1] — 2026-09-11

### [fundamentos-informacoes-adicionais-fiscais](openspec/changes/archive/2026-09-11-fundamentos-informacoes-adicionais-fiscais) Novas colunas Preço Típico, P / PT, Informações adicionais e Dados fiscais com ingestão do Informe Anual da CVM

### [fundamentos-congelar-colunas](openspec/changes/archive/2026-09-11-fundamentos-congelar-colunas) Congela as colunas Ticker e Nome na tabela de Fundamentos com dois Treeviews sincronizados

#### Added

- Congelamento: as colunas `Ticker` e `Nome` passam a ficar fixas à esquerda da tabela de Fundamentos, enquanto as demais 24 colunas rolam horizontalmente.
- Dois Treeviews sincronizados: a tabela passa a ser composta por um Treeview fixo (Ticker, Nome) e um Treeview rolável (demais colunas), lado a lado; a fronteira entre eles é a borda direita da última coluna congelada, reforçada por uma linha divisória vertical fixa (não arrastável).
- Scroll vertical compartilhado: uma única barra de rolagem vertical controla os dois Treeviews; a roda do mouse sobre qualquer um dos painéis rola ambos.

#### Changed

- Scroll horizontal: apenas o Treeview rolável possui rolagem horizontal; o painel congelado não rola.
- Largura da região congelada: a largura do painel congelado é a soma das larguras de `Ticker` e `Nome`, sem gap nem clipping; as larguras persistidas continuam sendo a única fonte de verdade.
- Seleção: a seleção de uma linha em qualquer um dos Treeviews é espelhada no outro; o modo multi-seleção é desabilitado.
- CSV inalterado: o botão "Copiar dados CSV" continua copiando a tabela inteira, com todas as 26 colunas.
- Compatibilidade: a preferência existente (`fundamental_column_widths`) permanece válida e passa a ser a única fonte de largura.

### [fundamentos-fallback-b3-cvm](openspec/changes/archive/2026-09-11-fundamentos-fallback-b3-cvm) Fallback B3/CVM para cotação, VP/Cota, classificação e FFO, e leitura do layout largo do Informe Trimestral

#### Added

- Preencher `P (Cotação)` e `Data de referência` a partir do último fechamento da B3 (`MarketPricePort`) quando o Fundamentus não fornecer.
- Preencher `VP (VP/Cota)` a partir do Informe Mensal da B3 (e da CVM como fallback), derivando `patrimônio líquido / cotas` quando o VP/Cota não vier reportado.
- Derivar `P/L` automaticamente quando `P` e a classificação FII estiverem disponíveis.
- Classificar `Tipo`/`Sub-tipo` a partir da "Classificação autorregulação" do Informe Mensal da B3 quando o Fundamentus não fornecer, produzindo rótulos como `FII` / `Papel: Outros, Ativa`.
- Preencher `Preço Típico` e `P / PT` a partir dos extremos (`Mín`/`Máx`) da janela de preços B3 já carregada em cache para a análise, restrita a 52 semanas antes da data de referência.

#### Changed

- BREAKING (comportamento do motor): restringir o motor determinístico de FFO a FIIs de tijolo/híbrido; para FII de papel, as métricas derivadas do motor permanecem `N/A`.
- Coordenação de ordem: esta change é aplicada depois de `fundamentos-informacoes-adicionais-fiscais` e constrói sobre os acréscimos daquela change nos módulos compartilhados, sem duplicar parsing nem sobrescrever campos.
- Cobertura de fallback (limites conhecidos): permanecem sem fallback B3/CVM e continuam `N/A` quando o Fundamentus não os fornece — `LPA`/`ROE`/`ROIC` (Papel) e `Qtd Imóveis`/`Cap Rate`/`Vacância Média` (FII).

#### Fixed

- Corrigir o `CvmQuarterlyRepository` para reconhecer e ler o layout largo real (`inf_trimestral_fii_resultado_contabil_financeiro_*.csv`), convertendo as colunas monetárias em componentes do FFO com código e proveniência preservados; o layout longo legado continua aceito.

### [fundamentos-orientacao-colunas](openspec/changes/archive/2026-09-11-fundamentos-orientacao-colunas) Atualiza o texto de orientação da sub-aba Fundamentos para descrever as novas colunas

#### Changed

- Atualizar o campo **Indicadores envolvidos** do conteúdo de orientação da sub-aba "Fundamentos" para descrever todas as colunas exibidas, incluindo Preço Típico, P / PT, Dividend Payout, Informações adicionais e Dados fiscais.
- Ampliar o campo **Como interpretar** com orientações sucintas sobre a leitura de Preço Típico e P / PT, do Dividend Payout, dos itens de Informações adicionais e da identidade fiscal.
- Manter o padrão existente de quatro campos na ordem **Objetivo → Responde a pergunta → Indicadores envolvidos → Como interpretar**, com formatação rica (negrito nos cabeçalhos, itálico na pergunta).

## [0.8.0] — 2026-09-09

### [structured-earnings](openspec/changes/archive/2026-09-09-structured-earnings) Extração de rendimentos e amortizações de FIIs via API B3 com entidades de domínio, cache e CLI

### [regulacao-mercado](openspec/changes/archive/2026-09-09-regulacao-mercado) Dados regulatórios e de mercado da B3 (fatos relevantes, notícias, censuras, condições excepcionais) integrados ao llm-chat

### [b3-cache-documentos-identidade](openspec/changes/archive/2026-09-10-b3-cache-documentos-identidade) Cacheia HTML de documentos FundosNet e respostas de identidade da B3, com chaves versionadas por parser

#### Added

- Cobrir com testes a ausência de requisição HTTP na segunda chamada (documento e identidade) e a invalidação por versão.

#### Changed

- Cachear o HTML do documento FundosNet em `B3FundosClient.buscar_html_documento`, indexado pelo `id` do documento e aplicável tanto a proventos (`type=41`) quanto ao informe mensal (`type=40`), evitando o rebaixamento a cada análise.
- Cachear `GetListClassFund` em `B3FundosClient.listar_candidatos`, indexado pelo `id` primário do fundo, para que `B3FundRepository.find_by_ticker` não reconsulte a B3 a cada execução.
- Consistência: centralizar TTLs e nomes de chave em constantes do cliente e versionar as chaves de cache com a versão do parser/aquisição, de modo que uma mudança de parser invalide os registros anteriores.

### [b3-fii-identity-and-dividends](openspec/changes/archive/2026-09-10-b3-fii-identity-and-dividends) Primeira fase do programa Fundamentos: aquisição B3 de identidade e dividendos e wiring da análise em background na GUI

#### Added

- Nova camada de aquisição B3 (`fundsListedProxy`) conforme RFC-008, escopo identidade + dividendos: resolução de ticker para `idFNET` (heurística `idMain`), listagem paginada de `GetStructuredReports(type=41)`, download e parsing de documento FundosNet, retry para erros transitórios, rate-limit por host, cache e preservação de metadados de aquisição.
- Modelos de domínio B3 normalizados (`B3Fund`, `B3ReportReference`, `AcquisitionMetadata`, `AcquisitionResult`) que distinguem lista vazia de falha de aquisição.
- Adaptador `FiiFundamentalRepository` apoiado na camada B3 para nome e proventos; `Dividend Yield` calculado como dividendo por cota / preço de fechamento, desacoplado de NAV e FFO.

#### Changed

- Wiring da GUI: o `FundamentalAnalysisUseCase` passa a ser instanciado e executado após cada carga de dados, em thread de background com reporte de progresso; os resultados são publicados na thread do Tk via fila e consumidos pela sub-aba "Fundamentos". Um token de geração descarta resultados obsoletos quando uma nova carga começa.
- Sem mudanças de contrato nas fontes CVM/Fundamentus nesta fase; o `FundamentusProvider` permanece como fonte primária, e a camada B3 desta change atua como fallback de identidade e dividendos.

### [conditional-cache-fundamentus-cvm](openspec/changes/archive/2026-09-10-conditional-cache-fundamentus-cvm) Abstração de cache condicional com revalidação por data/HTTP, aplicada ao Fundamentus e à CVM (corrige frescura do ZIP anual)

#### Added

- Introduzir uma abstração genérica de cache condicional que separa _frescor_ (quando o valor é considerado válido), _revalidação_ (checagem barata contra a fonte remota) e _retenção_ (quando evictar do disco), com protocolo de `Validator` plugável.
- Adicionar validadores concretos: `DateValidator` (campo `Data últ cot`) e `HttpValidator` (`ETag`/`Last-Modified`, `304`), com chaves versionadas por `parser_version`/`SOURCE_SCHEMA_VERSION`, escrita atômica e coalescência de checagens de rede.

#### Changed

- Aplicar ao provider do Fundamentus: revalidar o snapshot por `Data últ cot` (primário) e validadores HTTP (secundário), cachear HTML cru com versão do parser e devolver o resultado do cache (hit/revalidado/atualizado) para a camada de apresentação.
- Propagar o resultado do cache até a statusbar para exibir "Dados atualizados" quando houver atualização real, sem acoplar infraestrutura à GUI.

#### Fixed

- Corrigir o bug da CVM: revalidar o arquivo anual contra a fonte remota (validador HTTP) antes de reutilizar o ZIP local, rebaixando apenas quando a fonte mudou; em falha de revalidação, servir o arquivo local (stale-on-failure) e atualizar os metadados.

### [copy-fundamentos-csv](openspec/changes/archive/2026-09-10-copy-fundamentos-csv) Botão Copiar Dados passa a copiar a tabela de Fundamentos quando essa sub-aba está ativa

#### Changed

- Quando a aba principal for "Análise Geral" e a sub-aba selecionada for "Fundamentos", o botão "Copiar Dados" (e `Ctrl+Shift+C`) copia o conteúdo da tabela de Fundamentos (cabeçalho + uma linha por ticker exibido) em vez do CSV bruto de negociações.
- A cópia da tabela reutiliza o mesmo mecanismo de clipboard (`pyxclip` primário, fallback Tkinter) e o mesmo feedback na statusbar do fluxo existente.
- Fora dessa combinação de abas, o fluxo de cópia atual permanece inalterado.

### [cvm-monthly-fund-data](openspec/changes/archive/2026-09-10-cvm-monthly-fund-data) Segunda fase: extração do Informe Mensal Estruturado da CVM como fallback de patrimônio/cotas/cotistas e P/VP

#### Added

- Nova camada de aquisição CVM (`dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL`) por CNPJ: download do ZIP anual, extração dos CSVs, descoberta/versionamento de schema, filtro por CNPJ e competência, seleção da reapresentação mais recente e preservação de hash/metadados.
- Resolução de identidade (`FundIdentity`): ticker → CNPJ + idFNET + codeCVM, combinando a identidade B3 (change anterior) com o cadastro CVM.
- Normalização de patrimônio (`PatrimonioFii`): `VL_PATRIM_LIQ`, `QT_COTA`, `NR_COTST` a partir do schema 2025+, com aliases legados (`CNPJ_Fundo`, `QUANT_COTA`).

#### Changed

- Atualização/encapsulamento do `CvmFiiAdapter` existente para consumir o novo repositório, removendo o acoplamento ao schema antigo.
- O patrimônio da CVM passa a ser usado como fallback para `P/VP` quando o Fundamentus não fornecer o dado; `FFO Yield`, `P/FFO` e `FFO Trend` permanecem `N/A`.

### [deterministic-ffo-engine](openspec/changes/archive/2026-09-10-deterministic-ffo-engine) Terceira fase: motor determinístico de FFO a partir de componentes estruturados da CVM (Informe Trimestral + DFIN)

#### Added

- Nova camada de aquisição CVM do Informe Trimestral Estruturado e das Demonstrações Financeiras (DFIN) por CNPJ, sobre o pipeline de dados abertos da CVM.
- Classificador determinístico de componentes de resultado (`RECURRING`, `FAIR_VALUE`, `DISPOSAL`, `NON_RECURRING`, `UNKNOWN`), com regra conservadora: apenas `RECURRING` entra no FFO.
- Motor de FFO: FFO mensal → FFO 12m → FFO por cota (média ponderada de cotas) → FFO Yield e P/FFO, com qualidade (`HIGH`/`MEDIUM`/`LOW`) e proveniência por componente.
- Reconciliação com DFIN/Informe Trimestral, gerando warning quando a diferença exceder o limite configurável.

#### Changed

- O FFO calculado passa a atuar como fallback do Fundamentus: quando o Fundamentus não fornece FFO, as métricas usam o motor determinístico.
- Integração com o motor de métricas existente, definindo uma única fonte de verdade para `FFO Yield` e `P/FFO`.

### [fii-patrimonio-cotistas-provider](openspec/changes/archive/2026-09-10-fii-patrimonio-cotistas-provider) Preenche cotistas/patrimônio/VP-Cota via B3 (type=40) com fallback CVM e corrige a resolução de ticker na B3

#### Changed

- BREAKING (resolução B3): a resolução de ticker passa a usar `GetListFunds` (busca por `acronym` → `id` primário) e a consultar `GetListClassFund` por `idFNET`; corrige a resolução hoje quebrada, pré-requisito de toda a aquisição B3.
- A B3 passa a listar e extrair o Informe Mensal Estruturado (`GetStructuredReports`, `type=40`), baixando o documento do FundosNet e extraindo por rótulo: `Número de cotistas`, `Patrimônio Líquido`, `Número de Cotas Emitidas` e `Valor Patrimonial das Cotas`.
- A B3 (type=40) passa a ser a fonte primária de cotistas/patrimônio/cotas/VP-Cota, por ser mais atual: disponível por ticker assim que o informe é entregue (ex.: referência 07/2026 entregue em 14/08/2026), contra ~3 semanas de latência do arquivo anual da CVM (revalidado em 05/09/2026).
- A CVM permanece como fallback, passando a ler o layout multi-arquivo atual (`inf_mensal_fii_complemento_*`: `Total_Numero_Cotistas`, `Patrimonio_Liquido`, `Cotas_Emitidas`, `Valor_Patrimonial_Cotas`), sem abortar a leitura por `CvmSchemaError` de um arquivo isolado.
- As colunas "Nº de cotistas", "Patrimônio" e "VP (VP/Cota)" passam a ser preenchidas a partir da fonte consolidada.

### [fundamental-dividend-consolidation](openspec/changes/archive/2026-09-10-fundamental-dividend-consolidation) Tendência do dividendo por comparação direta e consolidação de data-com/dividendos de B3, CVM e Fundamentus

#### Changed

- BREAKING (rótulos): a tendência do dividendo passa a ser `Neutro` (igual), `Crescimento` (acima) e `Redução` (abaixo), por comparação direta entre o último dividendo e o anterior, sem banda de tolerância.
- A última data-com e o par último/anterior de dividendos passam a ser consolidados a partir do histórico B3 (primário), CVM (secundário) e Fundamentus (fallback), preenchendo o que estiver faltando.
- A coluna "Última data-com" da tabela passa a ser preenchida para todos os tickers em que houver dado consolidado.

### [fundamental-metrics-table](openspec/changes/archive/2026-09-10-fundamental-metrics-table) Tabela fundamentalista "Fundamentos" na aba "Análise Geral" com FFO Yield, Dividend Yield, P/FFO e P/VP para FIIs elegíveis

#### Added

- Nova sub-aba "Fundamentos" no sub-notebook da aba "Análise Geral", com uma tabela (`ttk.Treeview`) alimentada pela watchlist de tickers
- Colunas de identidade para todos os tickers: ticker, nome, tipo (ação/FII/ETF/BDR) e sub-tipo (FII: tijolo/papel/híbrido/fiagro/fiinfra; ação: ordinária/preferencial/ETF)
- Classificação de tipo/sub-tipo: tipo e sub-tipo de ação derivados sintaticamente do ticker e cruzados com `code-cvm-resolution`; sub-tipo de FII via taxonomia versionada
- Colunas de dividendo para todos os tickers: última data-com, último dividendo (somente `Rendimento`; amortização excluída) e tendência do dividendo (último vs. anterior, banda de ±5% configurável, `N/A` sem dividendo anterior)
- Colunas fundamentalistas apenas para FIIs elegíveis (tijolo/híbrido): FFO Yield, Dividend Yield 12m, P/FFO, P/VP, FFO Trend, nº de cotistas + classe e patrimônio + classe — conforme RFC-006/007; ações/ETF/papel/fiagro exibem `N/A`
- Adapter CVM para NAV, nº de cotas e nº de cotistas; provedor Fundamentus para FFO 12m/3m
- Camada de domínio isolada (funções puras, `decimal.Decimal`, evidência por métrica) conforme RFC-007

#### Changed

- Reuso do preço de fechamento dos dados B3 já baixados (sem novo adapter de mercado)

### [fundamentos-correcoes](openspec/changes/archive/2026-09-10-fundamentos-correcoes) Corrige parser de proventos B3, expõe VPA e histórico de proventos do Fundamentus e padroniza casas decimais

#### Added

- Fundamentus (Papel): expor o indicador `VPA` como `vp_cota` para ações e prover o histórico de proventos de `proventos.php` como uma implementação de `DividendHistoryProvider`.

#### Changed

- Layout: formatar com exatamente 2 casas decimais as colunas "Último dividendo", "Dividendo anterior", "Dividend Payout (DY/FFOY)", "P (Cotação)" e "VP (VP/Cota)".
- Dividendos: ligar o `historico_dividendos` no wiring e consolidar B3 (FII) + histórico Fundamentus para preencher data-com, último/anterior e tendência em FII e Papel.
- BREAKING (dados exibidos): para FIIs, "Último dividendo" passa a ser o rendimento mais recente da B3 (com data real) em vez do `Dividendo/cota` do Fundamentus; a formatação fixa de 2 casas altera a saída textual e o CSV.

#### Fixed

- B3 (FII): corrigir o parser do documento FundosNet para o layout real de duas colunas (`Rendimento | Amortização`), identificando o tipo pela coluna que contém o valor e extraindo a `Data-base` do rótulo parentético. Adicionar fixture de contrato do documento real.

### [fundamentos-pl-acionistas-layout](openspec/changes/archive/2026-09-10-fundamentos-pl-acionistas-layout) Reordena colunas com P/L, número de acionistas via FRE e rótulos descritivos de tendência

#### Added

- P/L (Papel): expor o indicador `P/L` do Fundamentus como campo fundamentalista e exibi-lo na tabela.
- P/L (FII): calcular `P/L = Preço / (Último dividendo × 12)`, anualizando o dividendo mensal para expressar a quantidade de anos, por função pura de domínio, com `N/A` quando o último dividendo for ausente ou zero.
- Nº de acionistas (Papel): obter a quantidade de acionistas do FRE (`distribuicao_capital`, somando pessoa física, pessoa jurídica e investidores institucionais) usando a ponte ticker→CNPJ do FCA (`valor_mobiliario`), preenchendo "Nº de cotistas" e reutilizando `classificar_cotistas` para "Classe de cotistas". FII mantém a fonte atual (Informe Mensal/B3).

#### Changed

- Layout: reordenar as colunas da tabela de Fundamentos para `Ticker;Nome;Tipo;Sub-tipo;P (Cotação);VP (VP/Cota);P/VP;P/L;Dividend Yield;Última data-com;Último dividendo;Dividendo anterior;Tendência do dividendo;FFO Yield;Dividend Payout (DY/FFOY);FFO Trend;P/FFO;Nº de cotistas;Classe de cotistas;Patrimônio;Classe de patrimônio;Data de referência`, adicionando a coluna `P/L` após `P/VP` e alinhando-a à direita.
- Rótulos de tendência: exibir rótulos descritivos no lugar dos identificadores do enum: `FORTE_ALTA` = `Forte Alta`, `ALTA` = `Leve Alta`, `ESTAVEL` = `Estável`, `QUEDA` = `Leve Queda` e `FORTE_QUEDA` = `Forte Queda`.
- Tendência do dividendo: classificar em cinco faixas percentuais com os mesmos rótulos do FFO Trend: `Forte Alta` (≥ +5%), `Leve Alta` (> 0% e < +5%), `Estável` (= 0%), `Leve Queda` (≥ −5% e < 0%) e `Forte Queda` (< −5%).
- BREAKING (valores exibidos): os valores de `TendenciaDividendo` deixam de ser `Crescimento`/`Redução`/`Neutro` e passam às faixas do FFO Trend, alterando a saída textual/CSV e os testes de tendência; "FFO Trend" deixa de exibir `FORTE_ALTA` e passa a exibir `Forte Alta`.

### [fundamentos-table-columns](openspec/changes/archive/2026-09-10-fundamentos-table-columns) Adiciona dividendo anterior, payout, P e VP/Cota e reordena/alinha as colunas da tabela de Fundamentos

#### Added

- Novas colunas:
- Dividendo anterior: valor do dividendo imediatamente anterior (`UltimoDividendo.valor_anterior`).
- Dividend Payout (DY/FFOY): razão `Dividend Yield / FFO Yield`.
- P (Cotação): preço de mercado do ativo (campo `cotacao` do Fundamentus).
- VP (VP/Cota): valor patrimonial por cota reportado pelo Fundamentus.
- O Fundamentus passa a expor `VP/Cota` como campo normalizado da análise fundamentalista.

#### Changed

- BREAKING (colunas): a tabela fundamentalista passa a exibir, nesta ordem: Ticker, Nome, Tipo, Sub-tipo, Última data-com, Último dividendo, Dividendo anterior, Tendência do dividendo, FFO Yield, Dividend Yield, Dividend Payout (DY/FFOY), FFO Trend, P (Cotação), VP (VP/Cota), P/FFO, P/VP, Nº de cotistas, Classe de cotistas, Patrimônio, Classe de patrimônio, Data de referência.
- "FFO Trend" é movida para logo após "Dividend Payout (DY/FFOY)".
- Alinhamento à direita do conteúdo das colunas: Último dividendo, Dividendo anterior, FFO Yield, Dividend Yield, Dividend Payout (DY/FFOY), P, VP, P/FFO, P/VP, Nº de cotistas e Patrimônio.
- O sub-tipo passa a concatenar suas partes com `", "` em vez de `"; "` (tanto para FII quanto para Papel).
- Fora de escopo: congelamento das colunas Ticker/Nome (não será implementado).

### [fundamentos-table-data](openspec/changes/archive/2026-09-10-fundamentos-table-data) Deriva Tipo/Sub-tipo do Fundamentus, remove gate de FFO e preenche colunas de cotistas/patrimônio

#### Added

- Novas colunas ao final da tabela: número atual de cotistas, classificação por número de cotistas, tamanho patrimonial do fundo, classificação por tamanho patrimonial e data de referência dos dados.

#### Changed

- BREAKING (classificação): as colunas "Tipo" e "Sub-tipo" passam a ser derivadas do Fundamentus, substituindo a taxonomia/sintaxe anteriores:
- "Tipo" = `Papel` (rótulo `Papel`) ou `FII` (rótulo `FII`);
- `Papel`: Sub-tipo = `Tipo; Setor; Subsetor` (concatenados por `"; "`);
- `FII`: Sub-tipo = `Tijolo: Segmento; Gestão` quando `Qtd imóveis > 0`, senão `Papel: Segmento; Gestão`.
- O parser do Fundamentus extrai o discriminador do ticker (`Papel`/`FII`) e os campos `Tipo`, `Setor`, `Subsetor`, `Segmento`, `Gestão`; `Qtd imóveis` (já extraído) passa a ser o balizador Tijolo/Papel.
- Todas as colunas da tabela passam a ser preenchidas quando houver dado na fonte (Fundamentus primário, B3/CVM como fallback), inclusive P/VP, Dividend Yield e dividendo para ações.
- A classificação por cotistas e por patrimônio reutiliza as faixas determinísticas já existentes.
- Quando o Fundamentus não fornecer a classificação, a taxonomia/sintaxe atual (`classificar_ticker`) permanece como fallback.

#### Removed

- O gate de elegibilidade FFO é removido: FFO Yield, P/FFO e FFO Trend são preenchidos sempre que a fonte fornecer o dado, independentemente do tipo do ticker.

### [fundamentos-table-ux](openspec/changes/archive/2026-09-10-fundamentos-table-ux) Persiste largura das colunas, melhora feedback de cache/status e mantém cursor de espera durante a análise

#### Added

- As larguras das colunas da tabela fundamentalista são persistidas no `config.json` e restauradas na próxima execução.

#### Changed

- O texto de progresso da análise fundamentalista recebe o sufixo `" - cached"` quando o dado do ticker vem do cache (resultados `HIT` e `REVALIDATED`).
- Ao final da carga, a barra de status exibe:
- `"Dados atualizados com sucesso."` quando não houve falha na captura;
- `"Dados atualizados com mitigação de falhas."` quando houve falha recuperável;
- `"Falha ao atualizar dados"` em falha catastrófica.

#### Fixed

- O cursor de espera (`watch`) permanece visível durante toda a análise fundamentalista, inclusive quando os dados vêm do cache.

### [fundamentus-fundamental-provider](openspec/changes/archive/2026-09-10-fundamentus-fundamental-provider) Provider completo do Fundamentus como fonte primária, com composição e fallback por campo (B3/CVM/motor FFO)

#### Added

- Implementação do provider do Fundamentus conforme RFC-011 (`detalhes.php?papel={TICKER}`): fetch, parsing tolerante a mudanças de layout, normalização para `Decimal`/`date` e modelo tipado para ações e FIIs.
- Novo modelo de domínio normalizado com proveniência por campo, usado para compor a análise fundamentalista.
- Camada de composição de provedores com prioridade por campo: Fundamentus primeiro; B3/CVM/motor-FFO como fallback; o resultado registra de qual fonte veio cada valor.
- Pacote `infrastructure/fii/fundamentus/` (fetch, parser, modelo), mantendo `obter_ffo` como adaptador fino para compatibilidade.

#### Changed

- Integração do provider composto ao `FundamentalAnalysisUseCase` como caminho primário; as fontes das changes anteriores deixam de ser o caminho principal e passam a ser substitutas.
- Reuso das dependências existentes (`requests` + `beautifulsoup4`), sem `httpx`/`lxml`/`pydantic`; rate-limit de 1 req/s e respeito a `robots.txt`.

### [progresso-fundamentos-statusbar](openspec/changes/archive/2026-09-10-progresso-fundamentos-statusbar) Barra de progresso na fase de Fundamentos, glifo de status consistente e cursor/controles durante a análise

#### Added

- Barra de progresso na fase de Fundamentos: exibir a barra de progresso durante a análise fundamentalista, avançando por ticker (`current`/`total`) e com um estado inicial `0/N`, mantendo-a visível até a conclusão da fase.

#### Changed

- Controles desabilitados durante a fundamental: manter botões, comboboxes, data entry e a lista de tickers desabilitados durante toda a análise fundamentalista em background, restaurando-os somente ao final, como ocorre na carga histórica.
- Ajuste de apresentação: a mensagem de progresso por ticker deixa de usar `set_status` com `ℹ` e passa a atualizar a barra de progresso com o marcador consistente. A mensagem publicada pelo job passa a carregar `current`/`total`.

#### Fixed

- Glifo de status consistente: substituir o `ℹ` por um marcador que renderize de forma confiável (ex.: `•`), alinhado aos demais glifos que já aparecem corretamente (ex.: `✓`).
- Cursor de espera em todos os widgets: propagar o cursor `watch` para os widgets interativos, inclusive os que definem cursor próprio (botões, lista de tickers, comboboxes e data entry), restaurando cada cursor ao final da operação.

## [0.7.0] — 2026-08-11

### [kill-mutation-survivors](openspec/changes/archive/2026-08-11-kill-mutation-survivors) Eleva o mutation score de 61.95% para >= 80% com novos testes unitários, asserts mais fortes e padrões do_not_mutate para os 886 mutantes sobreviventes

#### Added

- Novos testes unitários para funções/métodos que hoje não possuem cobertura de teste, focando nos 886 mutantes sobreviventes agrupados por módulo
- Padrões adicionados ao `do_not_mutate_patterns` do mutmut para mutações impossíveis de matar com testes unitários

#### Changed

- Fortalecimento de asserts em testes existentes que cobrem o código mas não são sensíveis o suficiente para detectar mutações (ex: mocks que validam apenas que a chamada ocorreu, sem verificar argumentos específicos)

### [log-timestamps](openspec/changes/archive/2026-08-11-log-timestamps) Logs passam a incluir timestamp (data/hora) via basicConfig configurado globalmente no main.py

#### Changed

- `logging.basicConfig` configurado em `src/flowscope/presentation/main.py` com formato de log que inclui timestamp
- Timestamps em formato ISO 8601 com milissegundos (ex.: `2026-08-11 14:23:07,120`)
- Formato aplicado globalmente a todos os handlers via `basicConfig` (um único `format` para todo o processo)
- Testes de logging ajustados para o novo formato quando asserem na saída de log

### [quality-gate-ci](openspec/changes/archive/2026-08-11-quality-gate-ci) Implementa o quality gate completo da RFC-005 (lint, complexidade, duplicação, cobertura, mutação, segurança) e acopla-o ao pipeline de release

#### Changed

- `ci.yml` reescrito como workflow reutilizável (`workflow_call`) com 3 jobs encadeados (lint → test → quality-gate), usando Python 3.12 e 3.13
- `release.yml` ganha job `ci` que invoca o workflow reutilizável antes do build; jobs `build` e `release` passam a depender de `ci`
- Makefile com 30+ targets de qualidade: `venv`, `install-quality-tools`, `quality-gate`, `complexity`, `duplication`, `mutation-*`, `security*`
- `pyproject.toml` com dependências `dev` e `quality` e configurações `[tool.ruff]`, `[tool.pytest.ini_options]`, `[tool.mutmut]`, `[tool.coverage]`
- RFC-005 corrigida (target `build` como PyInstaller, remoção de menções a `build-wheel.yml`)

#### Added

- Scripts `scripts/quality_gate.py`, `scripts/complexity_metrics.py`, `scripts/check-mutation-score.py`
- Entradas `.gitignore` para `mutants/` e `.mutmut-cache`

### [remember-last-tickers](openspec/changes/archive/2026-08-11-remember-last-tickers) Persiste e restaura a última lista de tickers usada em `~/.flowscope/config.json`

#### Added

- Persistência da última lista de tickers em `~/.flowscope/config.json` sob a chave `last_tickers`
- Restauração da lista salva no startup sem disparar download de dados
- Testes unitários para `load_preferences` / `save_preferences` cobrindo o round-trip de `last_tickers`

#### Changed

- Salvamento da lista ao fechar o app (`_on_close`)
- Persistência da lista também quando muda via load-from-file / troca de diretório, sobrevivendo a crashes e saídas não-graciosas
- Contador de tickers no startup mostra `Tickers (N)` em vez de `Exibindo 0 de N ativos`

## [0.6.0] — 2026-07-10

### [copiar-dados-csv](openspec/changes/archive/2026-07-10-copiar-dados-csv) Botão Copiar Dados passa a exportar dados brutos CSV da B3 em vez de indicadores agregados

#### Added
- `segment` e `trades_qty` adicionados ao `daily_data` no use case para viabilizar o CSV completo

#### Changed
- Lógica do botão "Copiar Dados" substituída para copiar dados brutos CSV (SgmtNm=CASH) com campos `RptDt;TckrSymb;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;FinInstrmQty;NtlFinVol`
- Na aba "Análise do Ticker": copia dados apenas do ticker selecionado; na "Análise Geral": copia de todos os tickers selecionados
- Período copiado reflete o selecionado nos comboboxes de período e amostragem
- Formato brasileiro: campo separado por `;`, decimal com `,` (vírgula)
- OperationGuard continua desabilitando/habilitando o botão durante cargas; atalho `Ctrl+Shift+C` mantido

### [sampling-strategy-selector](openspec/changes/archive/2026-07-10-sampling-strategy-selector) Comboboxes de período e amostragem para controle flexível da janela temporal de análise

#### Added
- Combobox de período (30/60/90 dias) na barra superior, ao lado do botão Copiar CSV
- Combobox de amostragem (Fibonacci, Fibonacci reverso, Fibonacci duplo, Monte Carlo, Monte Carlo duplo, Todos os dias)
- Tooltip único e fixo em cada combobox com explicação geral do controle
- Recarga automática de dados ao mudar seleção dos combos quando dados já estão carregados
- Se nenhum dado estiver carregado, mudar combos não tem efeito

#### Changed
- Barra de status exibe texto explicativo do item selecionado ao percorrer os comboboxes
- `calendar.py` com novas funções de geração de datas para cada combinação período × amostragem
- `DataRepository.get_available_dates()` recebe parâmetros de período e amostragem
- `B3Client.fetch_file()` aceita modo `cache_only` — período > 30 usa apenas cache
- Ajuste de cada data de amostragem para o próximo dia útil disponível no cache (±7 dias), com deduplicação
- `AnalyzeTickersUseCase.execute()` recebe config de período/amostragem e propaga ao repositório
- Dois comboboxes incluídos no OperationGuard (desabilitados durante carga/processamento)

## [0.5.2] — 2026-07-09

### [refactor-loading-architecture](openspec/changes/archive/2026-07-09-refactor-loading-architecture) Refatoração da arquitetura de carregamento com controller, presenter e guarda de operação

#### Added
- `LoadIndexPortfolioUseCase` — caso de uso em application layer para carregar carteiras de índices, eliminando a comunicação direta da GUI com o repositório
- `OperationGuard` — context manager que previne operações concorrentes, garantindo fluxos atômicos de botão-para-gráfico
- `FlowScopeController` — extrai a lógica de orquestração do `FlowScopeGUI` para uma classe separada na adapter layer
- `FlowScopePresenter` — extrai a lógica de atualização da UI do `FlowScopeGUI` para uma classe separada de apresentação

#### Changed
- `DataRepository` port ganha `get_index_tickers()` para fechar a lacuna atual do protocolo
- Todos os botões (índice, carregar, salvar, editar, selecionar todos, desmarcar todos) desabilitam durante o pipeline completo de portfólio + análise e restauram ao estado anterior ao finalizar

#### Removed
- `_fill_with_index()` e `_ensure_tickers()` do `FlowScopeGUI` — orquestração movida para o controller

### [add-presentation-layer-tests](openspec/changes/archive/2026-07-09-add-presentation-layer-tests) Testes unitários para a camada de apresentação com protocolo GUIView destacável

#### Added
- Testes unitários para `FlowScopeController.on_index_clicked()` e `on_load_data()` com dependências mockadas (sequência, erros, guard)
- Testes para `FlowScopeController._make_progress_cb()` — verifica advance/fail no callback
- Testes para `FlowScopePresenter` com mock de `GUIView` (operation_started/finished, progress, result, error, getters)
- Teste para `OperationGuard.is_busy` property
- Teste para `LoadIndexPortfolioUseCase.execute()` repassando `progress_callback`
- Testes Tkinter headless para `_disable_all_buttons()` e `_restore_all_buttons()` com snapshot de estados

#### Changed
- `FlowScopePresenter` passa a depender do protocolo `GUIView` em vez da classe concreta `FlowScopeGUI`
- `FlowScopeGUI` implementa o protocolo `GUIView` com 16 novos métodos públicos

### [testes-core](openspec/changes/archive/2026-07-09-testes-core) Testes para lacunas de cobertura nas camadas de application e infrastructure com mock HTTP

#### Added
- Testes para `AnalyzeTickersUseCase.execute()` com trades mockados (com/sem filtro de tickers, agregação diária)
- Testes para `OperationGuard.acquire()` nos estados livre e ocupado, incluindo reentrância
- Testes para `LoadIndexPortfolioUseCase.execute()` com índices válidos, inválidos, retorno vazio e sucesso
- Testes para `CacheManager.get_or_fetch()` com cache válido, expirado, ausente e falha no fetch
- Testes para `CacheManager.invalidate()` com chave existente e inexistente
- Testes para `B3Client.fetch_file()` com cache hit, cache miss (HTTP mockado) e callback de progresso
- Testes para `B3Client.fetch_portfolio()` com retorno de tickers, resposta vazia e falha HTTP
- Testes para `B3DataRepository.fetch_trades()` com parser sucesso, erro de parse e erro de download
- Testes para `B3Client._build_portfolio_url()` — verificação do encoding base64
- Dependência `responses` adicionada em `[project.optional-dependencies] dev` para mock HTTP
- `conftest.py` com fixtures padronizadas para B3Client, CacheManager e B3DataRepository mockados

### [cross-platform-logging](openspec/changes/archive/2026-07-09-cross-platform-logging) Logging técnico cross-platform com LogPort, PythonLogAdapter e handlers nativos (syslog/Event Log)

### [fix-linting-warnings](openspec/changes/archive/2026-07-09-fix-linting-warnings) Correção de 75 warnings de linting com extração de métodos e limpeza de código

#### Changed
- `DominanceRankingChart.update` e `DominanceTimelineChart.update` — lógica de stems extraída para função compartilhada `_compute_stems` (reduz complexidade C901 de 21→~16 e 12→~8)
- `PriceRangePanel._build_main_chart` — bloco `is_last` extraído para `_render_last_day_markers` (C901 16→~10)
- `VWAPHistChart.update` — loops de coleta de dados e violins extraídos para `_collect_ticker_data` e `_compute_violin_shapes` (C901 14→~9)
- `QuadrantChart.update` — anotações de ticker extraídas para `_annotate_tickers` (C901 15→~12)

#### Fixed
- 19 imports não usados (F401) e 4 variáveis não usadas (F841) removidos
- 37 problemas cosméticos corrigidos (E501, E306, E741, W391, E302, E127-E131)
- 2 `_generate_summary` suprimidos com `# noqa: C901` (complexidade inerente de texto narrativo)

#### Added
- `LogPort` (Protocol) na camada application como porta de logging, seguindo o padrão Clean Architecture já usado com `DataRepository`
- `PythonLogAdapter` na infraestrutura que implementa `LogPort` delegando para o módulo `logging` stdlib

#### Changed
- Handlers de logging configurados por plataforma no `main.py`: `SysLogHandler` (Linux/macOS), `NTEventLogHandler` (Windows), `RotatingFileHandler` (fallback universal em `~/.flowscope/logs/`)
- `LogPort` injetado no `FlowScopeController` para logar erros técnicos antes de exibir mensagem na statusbar
- `FlowScopePresenter` ganha `on_technical_error()` que exibe mensagem amigável orientando o usuário a consultar o log

#### Removed
- `NullHandler` de `main.py` (substituído por configuração real de logging)

## [0.5.1] — 2026-07-03

### [sem-dados-empty-state](openspec/changes/archive/2026-07-03-sem-dados-empty-state) Estado vazio "Sem dados" com lazy rendering por sub-tab

#### Added
- Todos os 6 charts passam a exibir "Sem dados" centralizado com `ax.axis("off")` na inicialização e quando não há dados disponíveis
- Utility function compartilhada para o estado vazio (`create_empty`, `show_empty`, `hide_empty`)
- Registry mapping em `app.py` para coordenar qual chart renderizar por sub-tab, eliminando o `if/elif` atual

#### Changed
- Renderização dos charts passa a ser lazy por sub-tab: apenas o chart da sub-tab visível é atualizado ao carregar/recarregar dados
- Ao recarregar dados, todos os charts não-visíveis voltam ao estado "Sem dados" (Opção A)
- Charts multi-eixos (PriceRangePanel, FinancialFlowPanel) usam `fig.text()` centralizado em vez de labels por subplot (Opção B)

## [0.5.0] — 2026-07-02

### [fluxo-financeiro-panel](openspec/changes/archive/2026-07-02-fluxo-financeiro-panel) Painel visual de fluxo financeiro com classificação DMF, barra CLV/Score e pressão de compra/venda

#### Added
- Painel visual matplotlib para sub-aba "Fluxo Financeiro" com card de classificação, barra CLV/Score e barra empilhada de pressão de compra/venda
- `summary_callback` para resumo textual dinâmico
- `MoneyFlowClassifier` para classificação qualitativa do fluxo financeiro

#### Changed
- Sub-aba "Fluxo Financeiro" ativada (removida do conjunto de abas desabilitadas)
- OrientationPanel atualizado com novo conteúdo explicativo para o fluxo financeiro

## [0.4.0] — 2026-07-01

### [orientation-add-question-field](openspec/changes/archive/2026-07-01-orientation-add-question-field) Pergunta-guia adicionada ao conteúdo de orientação de cada sub-aba

#### Changed
- Conteúdo do OrientationPanel passa a incluir "Responde a pergunta" entre Objetivo e Indicadores envolvidos
- Ordem dos campos: **Objetivo → Responde a pergunta → Indicadores envolvidos → Como interpretar**

### [orientation-richtext-formatting](openspec/changes/archive/2026-07-01-orientation-richtext-formatting) Formatação rica nativa (negrito/itálico) no OrientationPanel via tags tk.Text

#### Added
- Formatação rica: cabeçalhos de seção em **negrito** e perguntas em itálico via tags nativas `tk.Text`
- Configuração das tags `"bold"` (TkDefaultFont 9 bold) e `"italic"` (TkDefaultFont 9 italic)

#### Changed
- `set_content` alterado de `(title: str, body: str)` para `(title: str, body: list[tuple[str, str]])`
- Todas as 9 sub-abas refatoradas para usar lista de tuplas `(segmento, tag)`
- `_on_quadrant_summary` atualizado para anexar resumo como tupla à lista body

### [unify-price-amplitude-chart](openspec/changes/archive/2026-07-01-unify-price-amplitude-chart) Três métricas correlatas unificadas num único axes com camadas visuais de posição, amplitude e eficiência

#### Changed
- Price Range Timeline, Range % Histórico e Eficiência Diária unificados num único axes matplotlib com 3 camadas visuais por row (eficiência como barra de fundo, timeline como scatter, amplitude como tamanho do marcador)
- Tooltip expandida com Amplitude Relativa (Range %)
- Nomenclatura atualizada: título "Amplitude de Preço — {ticker}", "Range %" → "Amplitude Relativa"
- Texto de orientação atualizado com as três perguntas "Onde / Quanto / Se andou com convicção" e significado interpretativo das classificações
- Setas de trajetória (ax.arrow) substituídas por linhas (ax.plot) — eliminou artefatos visuais de traçado extra
- Labels "← Vendedores" e "Compradores →" adicionados abaixo do gauge CLV
- Título do CLV alterado para "CLV (data mais recente)"
- Labels "Min:" e "Max:" separados e posicionados abaixo de 0% e 100%
- Altura do gauge CLV reduzida em ~20%

#### Removed
- Sub-gráfico "Range % Histórico" — substituído pelo tamanho do marcador de fechamento (●)
- Sub-gráfico "Eficiência Diária" — substituído por barra horizontal de fundo por row (eficiência visível em todos os dias, não apenas no último)

### [redesign-amplitude-panel](openspec/changes/archive/2026-07-01-redesign-amplitude-panel) Reformula a aba Amplitude de Preço como painel visual com timeline, gauges de eficiência e CLV

#### Added

- Criar o Price Range Timeline Chart: gráfico horizontal que posiciona cada pregão em uma linha do eixo Y, normaliza o range [Min, Max] no eixo X (0-100%), e mostra marcadores de referência (Median, Typical, VWAP, Weighted Close) apenas no dia atual, com a trajetória do fechamento (●) conectada por setas entre dias consecutivos
- Adicionar gráfico de linha do Range % histórico (30 pregões) para contextualizar a amplitude do dia
- Adicionar gauge horizontal de Eficiência (0 a 1) indicando quanto do range virou deslocamento
- Adicionar gauge horizontal de CLV (-1 a +1) indicando onde o preço fechou dentro do range
- Incluir classificação qualitativa como annotation no gráfico (ex: "Movimento Direcional Forte")

#### Changed

- Substituir o painel textual de "Amplitude de Preço" por um painel visual com quatro componentes gráficos
- Atualizar o texto de orientação para guiar a interpretação visual

## [0.3.1] — 2026-06-29

### [statusbar-progress-indicator](openspec/changes/archive/2026-06-29-statusbar-progress-indicator) Barra de progresso determinate na statusbar com fases ponderadas, cache e falhas; ProgressReporter injetado nas camadas application/infrastructure

#### Added
- **Barra de progresso determinate** (`ttk.Progressbar`) com label textual lado a lado na statusbar, substituindo o texto animado cego
- **ProgressReporter**: classe com sistema de fases ponderadas, throttling de updates e contagem de falhas
- **Progresso em múltiplas fases**: download de dados históricos (7 datas Fibonacci), processamento de indicadores (DAG engine) e carregamento de portfólio
- **Cache refletido no progresso**: datas em cache são avançadas imediatamente sem delay perceptível
- **Falhas contabilizadas**: datas com erro são contadas no progresso com label indicando "N/M (X falhas)"
- **Portfolio loading textual**: exibe "Baixando portfólio IBOV..." como etapa da progressão
- **Callback de progresso** injetado via `UseCase` → `Repository` → `Client` → `Engine`, permitindo reporte em todas as camadas

#### Changed
- **Statusbar**: de `tk.Label` com texto animado para `tk.Frame` contendo `tk.Label` + `ttk.Progressbar` determinate
- **`_animate_loading()`**: removido em favor do sistema de progresso via `ProgressReporter`

## [0.3.0] — 2026-06-29

### [dominancia-pregao-stem-mfv](openspec/changes/archive/2026-06-29-dominancia-pregao-stem-mfv) Stem horizontal substitui círculo do MFV nos gráficos de Dominância; botões Mover/Ampliar da toolbar tornam-se mutuamente exclusivos

#### Changed
- **DominanceRankingChart**: círculo de MFV substituído por stem horizontal que parte de x=0 com comprimento proporcional ao MFV; label do ticker reposicionado após o stem; "Vendedores"/"Compradores" movidos para y=-0.08
- **DominanceTimelineChart**: mesma substituição círculo→stem (stem_max_data=0.15); "Vendedores"/"Compradores" movidos para y=-0.10
- **ToolbarBR**: botões Mover e Ampliar tornam-se mutuamente exclusivos (apenas um ativo por vez); Início desmarca ambos
- **OrientationPanel**: textos de orientação atualizados de "círculo" para "traço horizontal"

### [painel-dominancia-pregao](openspec/changes/archive/2026-06-29-painel-dominancia-pregao) Painéis de Dominância do Pregão (ranking) e Evolução da Dominância (timeline) com barras divergentes, classificadores e indicadores de fluxo

#### Added
- **Painel "Dominância do Pregão" na aba Análise Geral**: ranking visual de todos os tickers usando CLV do último pregão, com barras horizontais divergentes, classificação qualitativa e indicador de Money Flow Volume acumulado.
- **Painel "Evolução da Dominância" na aba Análise do Ticker**: gráfico temporal de barras divergentes (um dia por barra) com overlay de Daily Efficiency e indicador de Money Flow diário.
- **Duas novas strategies no engine**: `daily_money_flow` (MFV por dia, não acumulado) e `dominance_score` (CLV × Daily Efficiency).
- **Módulo de classificadores** (`domain/strategies/classifiers/`): `classify_dominance(clv)` e `classify_conviction(efficiency)` com tipagem forte e saída textual + score numérico.

#### Changed
- **Aba "Dominância do Pregão" renomeada para "Amplitude de Preço"** no notebook de Análise do Ticker (conteúdo atual são indicadores de amplitude).
- **Painel de orientação**: textos de ajuda para os novos painéis.
- **`_format_all_indicators`**: incluído `dominance_score` na listagem exibida.

### [multi-ticker-selector](openspec/changes/archive/2026-06-29-multi-ticker-selector) Modo visualização com Listbox de seleção múltipla, lazy refresh híbrido e remoção dos comboboxes da Análise Geral

#### Added
- **Modo visualização com Listbox(EXTENDED)**: toggle "Editar lista de tickers" alterna entre Text (edição) e Listbox (seleção múltipla via Ctrl+Click e Shift+Click)
- **Botões "Selecionar Todos" e "Desmarcar Todos"** na barra superior, ao lado direito do toggle, visíveis apenas no modo visualização
- **Preservação de seleção ao transitar entre modos**: tickers existentes mantêm marcação; novos entram marcados; remoções desaparecem; se lista mudou, recarga de dados é disparada
- **Separadores verticais** entre Salvar/Editar e entre grupo de seleção/índices
- **Lazy refresh híbrido**: aba ativa renderiza imediatamente após carga/filtro; demais abas renderizam apenas ao serem selecionadas

#### Changed
- `get_tickers()` retorna apenas tickers selecionados no modo visualização (todos no modo edição)
- `_ensure_tickers()` usa `get_all_listbox_tickers()` — carga de dados usa todos os tickers, independente da seleção
- `_on_load_data()` não substitui `self._tickers` nem chama `set_tickers()` (preserva lista original do usuário)
- Regra de quiver mantida no painel Quadrantes: setas exibidas quando apenas 1 ticker selecionado

#### Removed
- **Botão "Filtrar"** removido (seleção no Listbox já funciona como filtro)
- **Comboboxes de ticker da Análise Geral** (VWAP, Quadrantes, Dominância) removidos; seleção via Listbox controla todos os gráficos

### [refactor-analise-ticker-ui](openspec/changes/archive/2026-06-29-refactor-analise-ticker-ui) Combobox de seleção substituído por TickerList; painel Evolução da Dominância simplificado sem resumo lateral e linha de eficiência

#### Added
- **Labels "Compradores/Vendedores"** no QuadrantChart, abaixo do eixo CLV

#### Changed
- **Sub-abas reordenadas**: "Evolução da Dominância" como primeira aba da "Análise do Ticker", antes de "Amplitude de Preço"
- **DominanceTimelineChart redesenhado**: painel lateral de resumo removido; linha de eficiência (twiny) removida; informações movidas para o tooltip de cada barra (Data, Dominância, Convicção, MFV); percentuais adicionados nos labels "Compradores" e "Vendedores"
- **Spec `ticker-analysis` atualizada**: mecânica de seleção sem combobox
- **Spec `dominance-timeline-panel` atualizada**: design sem painel lateral, sem linha de eficiência, tooltip expandido

#### Removed
- **Combobox de seleção de ticker** na aba "Análise do Ticker"; ticker analisado agora deriva da TickerList (primeiro selecionado, ou primeiro da lista, ou "Selecione um ticker" se vazia)

#### Fixed
- **Hover nos charts de barra**: tooltip detecta mouse em qualquer ponto da barra (entre 0 e CLV), não apenas no endpoint
- **Zorder do tooltip**: tooltip renderiza acima dos stems MFV em ambos os charts de barra
- **Ordenação das datas**: DominanceTimelineChart ordena mais antiga no topo, mais recente na base
- **TickerList**: `exportselection=False` evita que seleção externa (X11 PRIMARY) limpe seleção interna
- **Lazy refresh**: `_on_tab_changed()` sempre atualiza a aba atual ao navegar, não apenas quando `_charts_dirty` está True

### [default-gui-mode](openspec/changes/archive/2026-06-29-default-gui-mode) `flowscope` sem argumentos passa a abrir a GUI por padrão

#### Changed

- `flowscope` (no flags) now opens the GUI instead of running CLI mode
- `--gui` flag is kept for backward compatibility (used by desktop shortcut)
- CLI mode (`--tickers`, `--vwap`, etc.) behavior is unchanged
- `--version` and `--create-shortcut` behavior is unchanged

### [wait-cursor-refactor](openspec/changes/archive/2026-06-29-wait-cursor-refactor) Cursor watch reutilizável nas operações de refresh de painel e cópia de gráfico

#### Added

- Adicionar `_set_wait_cursor()` / `_clear_wait_cursor()` como métodos reutilizáveis de uso geral

#### Changed

- Refatorar `_enter_loading_state` / `_exit_loading_state` em duas camadas: uma camada base de cursor (genérica) e a camada pesada atual (cursor + desabilitar inputs + animação)
- Envolver com try/finally os seguintes pontos com cursor watch:
- `_on_tab_changed` — refresh de charts ao trocar de aba
- `_on_ticker_edit` — refresh ao editar lista de tickers
- `_on_ticker_combo_selected` — refresh ao selecionar ticker (delega para `_on_tab_changed`)
- `_copy_chart` — cópia de imagem do gráfico (savefig + xclip)
- `_enter_loading_state` / `_exit_loading_state` passam a delegar o cursor para os novos métodos

## [0.2.1] — 2026-06-28

### [quadrantes-ticker-sync](openspec/changes/archive/2026-06-28-quadrantes-ticker-sync) Sincronização de comboboxes e visibilidade condicional de setas nos quadrantes

#### Added
- **Sincronização bidirecional de comboboxes:** combobox do Quadrantes e da Análise do Ticker sincronizam valores entre si. "Todos" no Quadrantes limpa o combobox da Análise do Ticker.

#### Changed
- **Quadrantes — setas (quiver):** ocultas quando o ticker está como "Todos"; exibidas apenas para o ticker selecionado.
- **`QuadrantChart.update()`:** adicionado parâmetro `show_arrows` para controle explícito das setas.

## [0.2.0] — 2026-06-28

### [index-portfolio-buttons](openspec/changes/archive/2026-06-28-index-portfolio-buttons) Botões para IBOV, IDIV e IFIX com cliente B3 genérico e parser reutilizável

#### Added

- Botões "IBOV", "IDIV" e "IFIX" no `TickerList` (fileira abaixo dos botões existentes)

#### Changed

- `B3Client.fetch_idiv_portfolio()` generalizado para `fetch_portfolio(index: str)` que aceita qualquer código de índice
- `parse_idiv_csv()` generalizado para `parse_index_csv()` que funciona para qualquer índice
- `B3DataRepository.get_idiv_tickers()` substituído por `get_index_tickers(index: str)`
- Lógica de autopreenchimento extraída para `_fill_with_index("IDIV")` e reusada em `_ensure_tickers()` e `_on_ticker_edit()`

#### Removed

- `fetch_idiv_portfolio()` e `parse_idiv_csv()` (substituídos)

### [quadrant-chart-panel](openspec/changes/archive/2026-06-28-quadrant-chart-panel) Painel Quadrantes com CLV × VWAP Distance, quiver de trajetória e resumo automático

#### Added

- **Novo indicador `vwap_distance`**: derivado do VWAP, calculado como `(last_price - avg_price) / avg_price` por ticker-por-data
- **Painel "Quadrantes"**: bubble chart (CLV × VWAP Distance) com quiver de trajetória temporal, colormap RdYlGn e bolhas dimensionadas por `fin_instr_qty`
- **Resumo textual automático**: análise da distribuição das bolhas entre os quadrantes
- **Seletor de ticker por chart**: Combobox nos gráficos VWAP e Quadrantes (opção "Todos")
- **Atalho Ctrl+A**: selecionar todos os filtros no TickerList

#### Changed

- **Documentação**: `panels.md` e `indicators.md` atualizados (descrição do Quadrantes e VWAP Distance)
- **Título da janela**: removida alteração ao carregar dados (título fixo "FlowScope v0.2.0")

### [replace-buttons-with-icons](openspec/changes/archive/2026-06-28-replace-buttons-with-icons) Substitui botões textuais por ícones na top bar e sidebar, compactando o layout

#### Changed

- Top bar: botões "Hoje", "Carregar" e "Copiar Dados" passam a exibir apenas ícone (sem texto), com tooltip mantido
- Sidebar (TickerList): botões "Salvar Tickers", "Carregar Tickers" e "Filtrar" passam a exibir apenas ícone (sem texto)
- Sidebar (TickerList): botões IBOV, IDIV e IFIX movidos para a mesma linha dos botões de ação (ao lado direito), eliminando a segunda fileira de botões
- Tooltips: todos os tooltips existentes são preservados; tooltips são adicionados aos botões que atualmente não possuem (Salvar Tickers, Carregar Tickers, Filtrar)

## [0.1.0] — 2026-06-28

### Added

- **Estrutura do projeto**: Clean Architecture (domain, application, infrastructure, presentation), pyproject.toml, Makefile, flowscope.spec para PyInstaller
- **Ingestão de dados B3**: Download de arquivos TradeInformationConsolidated via API two-step da B3, parser de CSV com schema definido, janela temporal com offsets de Fibonacci (d-1, d-2, d-3, d-5, d-8, d-13, d-21) e ajuste para dias úteis, cache local em `~/.cache/flowscope/`
- **Indicadores de fluxo**: Cálculo de Cumulative Volume Delta (CVD), Volume Weighted Average Price (VWAP) e Volume Profile por ticker, seleção automática dos 15 tickers com maior volume financeiro
- **Interface gráfica (Tkinter)**: Janela principal com seleção de data (tkcalendar), gráficos matplotlib (histogramas VWAP/CVD, scatter plot VWAP×CVD com setas temporais), campo multilinha de seleção de tickers com load/save .txt, botões de cópia para clipboard
- **Interface CLI**: argparse com flags `--gui`, `--tickers`, `--vwap`, `--cvd`, `--version`, `--create-shortcut`
- **Exportação para clipboard**: Cópia de dados CSV (pyxclip + fallback Tkinter) e cópia de gráfico como imagem PNG (xclip/Linux, win32clipboard/Windows, osascript/macOS)
- **Atalho desktop**: Geração de `.desktop` no Linux via `--create-shortcut`
- **Cache com TTL**: Método `get_or_fetch()` no CacheManager com suporte a TTL (usado para cache do portfólio IDIV)
- **Download automático do IDIV**: Novo método `fetch_idiv_portfolio()` no B3Client que baixa a carteira do IDIV (base64 → decode Latin-1 → parse) via endpoint da B3, com cache de 7 dias
- **Filtro CASH no parser**: Parâmetro `segment_filter="CASH"` em `parse_csv()` — linhas de outros segmentos (BMF, FUTURE) são ignoradas durante o parsing
- **Preenchimento automático do filtro**: Quando o campo de tickers está vazio e o usuário clica em "Carregar" ou "Filtrar", o sistema busca automaticamente a carteira IDIV e a usa como filtro padrão

### Changed

- **UI/UX — Proteção de carga**: Controles desabilitados durante carregamento, cursor "watch", indicador animado com pontos (`Carregando.` → `Carregando..` → `Carregando...`)
- **UI/UX — Feedback visual**: Statusbar com ícones Unicode (✓ ⏳ ⚠ ℹ), mensagens temporárias com auto-limpeza (2.5s), confirmação em ações de cópia
- **UI/UX — Atalhos de teclado**: Enter aciona "Carregar", Ctrl+Shift+C copia dados, F5 recarrega
- **UI/UX — Tooltips**: Em todos os controles interativos (botões, radio buttons, campos)
- **UI/UX — Contagem de tickers**: Label "Tickers (N)" e "Exibindo M de N ativos"
- **UI/UX — Layout**: Padding consistente (PAD_SMALL=4, PAD=8, PAD_LARGE=12), LabelFrame em "Visualização" e "Exportação", separador entre botões
- **UI/UX — Título dinâmico**: Janela exibe "FlowScope — YYYY-MM-DD — N ativos"
- **UI/UX — Menu de contexto**: Botão direito no campo de tickers com Copiar, Remover, Selecionar todos, Limpar seleção
- **UI/UX — Estado vazio**: Mensagem "Nenhum ticker corresponde ao filtro." quando filtro remove todos ativos
- **UI/UX — Preferências persistentes**: Geometria da janela, posição do sash, última data e último gráfico salvos em `~/.flowscope/config.json`
- **Filtro de tickers**: Alterado de automático (ao digitar) para manual via botão "Filtrar"
- **Barra de status**: Movida para abaixo dos botões de ação
- **Exportação CSV**: Colunas de VWAP/CVD diários adicionadas ao output (uma coluna por data da janela)
- **CLI export**: Flag `--tickers` agora filtra corretamente nas exportações `--vwap` e `--cvd`
- **Scatter plot**: Setas temporais (quiver) conectando posição d-1 → d de cada ticker implementadas
- **Ícone da aplicação**: Carregado na barra de título/tarefa (`.png` Linux, `.ico` Windows)

### Fixed

- **Especificações vs implementação**: Alinhamento de docs — descrição da API B3 corrigida de POST para GET, datas Fibonacci no spec corrigidas, fallback Tkinter documentado, `requests>=2.28` adicionado ao `requirements.txt`, seção vazia "Interface desktop" removida do README
- **Exit code do `--create-shortcut`**: Agora retorna 0 (sucesso) em plataformas não-Linux em vez de 1
- **Auto-refresh após load de tickers**: Gráficos atualizados ao carregar tickers de arquivo `.txt`

### Removed

- Filtro automático ao digitar no campo de tickers (substituído por botão "Filtrar" manual)

### [chart-interactivity](openspec/changes/archive/2026-06-27-chart-interactivity) Toolbox com zoom/pan/reset/save, hover tooltips com coordenadas X/Y e botão de navegação rápida Hoje

#### Added

- **Botão "Hoje"**: Resetar DateEntry para a data atual com um clique
- **Toolbox com zoom/pan/reset/save**: NavigationToolbar2Tk em cada chart com labels em português
- **Hover tooltip no scatter plot**: Ticker, VWAP, CVD e volume ao passar o mouse
- **Hover tooltip no CVD histogram**: Valor exato do CVD por barra
- **Hover tooltip no VWAP histogram**: Faixa de preço e volume do bucket

### [vwap-enhancement](openspec/changes/archive/2026-06-27-vwap-enhancement) VWAP recalculado com peso por quantidade de instrumentos e gráfico substituído por violin plot com perfil de volume

#### Changed

- **BREAKING**: VWAP geral calculado como Σ(TradAvrgPric × FinInstrmQty) / Σ(FinInstrmQty) — peso por quantidade de instrumentos, não por volume financeiro
- **VWAP Histogram**: Substituído por violin plot horizontal com perfil de volume, errorbar (VWAP, MinPric, MaxPric) e scatter (LastPric da data mais recente)
- **AnalyzeTickersUseCase**: Incluídos dados diários adicionais (FinInstrmQty, MinPric, MaxPric, LastPric) necessários ao novo gráfico
- **Tooltip do Radiobutton VWAP**: Atualizada com descrição completa do novo gráfico

### [improve-button-behavior](openspec/changes/archive/2026-06-27-improve-button-behavior) Hoje carrega dados automaticamente; persistência da última pasta nos diálogos de ticker

#### Added

- Preferência `last_ticker_dir` em `~/.flowscope/config.json` para persistir o último diretório usado nos diálogos de ticker

#### Changed

- Botão "Hoje" agora também executa carregamento automático de dados (antes apenas resetava a data)
- Botões "Hoje" e "Carregar" desabilitados durante o carregamento (loading guard estendido)
- `TickerList._save()` e `TickerList._load()` usam `initialdir` a partir da preferência persistida
- `TickerList` recebe parâmetros `initialdir` e `on_dir_changed` callback (baixo acoplamento)

### [redesign-gui-notebook](openspec/changes/archive/2026-06-28-redesign-gui-notebook) RadioButton chart selector replaced by two-level notebook with general and per-ticker analysis

#### Added

- Main `ttk.Notebook` replacing the "Visualização" RadioButton frame with tabs "Análise Geral" and "Análise do Ticker"
- Sub-notebook in "Análise Geral" with "VWAP" (existing chart) and "Quadrantes" (placeholder)
- Sub-notebook in "Análise do Ticker" with 5 placeholder tabs (Dominância, Fluxo, Participação, Eficiência, Resumo)
- `ttk.Combobox` in "Análise do Ticker" for selecting a single ticker
- `OrientationPanel` widget with fixed explanatory text per sub-tab

#### Changed

- `_show_current_chart()` adapted to control notebook tabs instead of pack/forget
- `_update_charts()` simplified to update only VWAP chart
- `_copy_chart()` simplified to copy only VWAP chart
- `config.json` persistence: `last_chart` → `last_tab` + `last_subtab`
- TickerList changes propagate to combobox in "Análise do Ticker"

#### Removed

- **BREAKING**: RadioButton group and "Visualização" frame
- **BREAKING**: `CVDHistChart` (GUI chart)
- **BREAKING**: `ScatterChart` (GUI scatter plot)
- **BREAKING**: `--cvd` CLI flag and `export_cvd_csv()`
- **BREAKING**: `ExportCVDUseCase` from application layer
- `AnalysisText` widget (replaced by `OrientationPanel`)

### [implementacao-indicadores-especificacao](openspec/changes/archive/2026-06-28-implementacao-indicadores-especificacao) Motor de cálculo DAG e 15 novos indicadores

#### Added

- Motor de cálculo baseado em DAG: cada indicador é uma estratégia independente que declara dependências; o engine resolve ordem de execução automaticamente e cacheia resultados
- 15 novos indicadores da especificação FS001–FS403: Range, Range%, Typical Price, Median Price, Weighted Close, CLV, Money Flow Multiplier, Money Flow Volume, Buying Pressure, Selling Pressure, Daily Efficiency, Financial Density, Trade Density, Volume Density, Average Trade Size, Average Financial Ticket
- Abas "Dominância do Pregão", "Fluxo Financeiro", "Participação Institucional", "Eficiência do Movimento" e "Resumo Geral" populadas com valores reais dos indicadores
- OrientationPanel com textos explicativos para cada grupo de indicadores

#### Changed

- Indicadores existentes (VWAP, Volume Profile, Top Tickers) refatorados para o novo padrão `IndicatorStrategy`
- **BREAKING**: Preço Referência definido como `avg_price` (desambigua Range% e Daily Efficiency)

#### Removed

- **BREAKING**: Indicador CVD (substituído por Money Flow Volume, que usa CLV contínuo em vez de sinal binário)

### [move-copy-buttons](openspec/changes/archive/2026-06-28-move-copy-buttons) Botões Copiar Dados/Gráfico realocados e frame Exportação eliminado

#### Added

- Botão "Copiar Gráfico" adicionado ao toolbar nativo do matplotlib (`ToolbarBR`), disponível em todos os charts
- Botão "Copiar Dados" na barra superior ao lado de "Carregar", iniciando desabilitado até o primeiro carregamento de dados

#### Changed

- `_copy_chart()` agora recebe o `Figure` como parâmetro (desacoplado do VWAP chart específico)
- `ToolbarBR` aceita `copy_chart_callback` via construtor (callback opcional)

#### Fixed

- `pyxclip` import corrigido (`pyxclip.main` não existe; usa `pyxclip.copy()` direto)
- `print()` substituído por `logging.warning()` com NullHandler na GUI para evitar vazamento de erros da API B3 no terminal
- URLs da API B3 removidas de mensagens de erro (sanitizadas no `B3Client`)

#### Removed

- Frame `Exportação` (LabelFrame + botões + separador) do `self._left_pw`
- Dependência do `_vwap_chart.get_figure()` em `_copy_chart()`

### [normalize-vwap-y-axis](openspec/changes/archive/2026-06-28-normalize-vwap-y-axis) Eixo Y do VWAP normalizado para desvio percentual com baseline em 0%

#### Changed

- **Eixo Y do VWAP**: Substituído preço absoluto (R$) por `(preço - VWAP) / VWAP × 100`
- **Baseline VWAP**: Linha horizontal tracejada em Y = 0% adicionada como referência visual
- **Violin plot, errorbar e scatter**: Todos os elementos visuais usam escala normalizada (%)
- **Errorbar → vlines**: Barra MinPric–MaxPric trocada para `ax.vlines()` + scatter em 0 (mais robusto em casos extremos)
- **Bucket size**: Heurística adaptada para ranges percentuais (0.01%–0.50%)
- **Tooltip hover**: Agora exibe delta percentual (Δ Máx/Mín) + LastPric % + VWAP absoluto (R$)
- **Rótulo do eixo Y**: Alterado para "Diferença do VWAP (%)"
- **Limites do eixo Y**: Configurados simetricamente em torno de 0%

### [fix-desktop-shortcut](openspec/changes/archive/2026-06-28-fix-desktop-shortcut) Atalho .desktop com caminho absoluto, ícone permanente e botão na GUI

#### Added

- Botão "Criar atalho no desktop" na barra superior da GUI (Linux) quando nenhum atalho existe, some após criar com sucesso
- Função compartilhada `_resolve_icon_path()` para resolução de ícone em modo dev e frozen (PyInstaller)
- `StartupNotify=true` e flag `--gui` no arquivo .desktop

#### Fixed

- `Exec` no .desktop agora usa caminho absoluto (`Path(sys.argv[0]).resolve()`), antes era relativo (`./flowscope`)
- Ícone no .desktop copiado para `~/.local/share/icons/flowscope.png` (permanente), antes resolvia para `/tmp/...` que sumia após fechar o app
- Resolução de ícone do toolbar (copy.png) corrigida para builds PyInstaller

#### Changed

- `_create_desktop_shortcut()` retorna `bool` em vez de chamar `sys.exit()` (reutilizável pela GUI)
- CLI `--create-shortcut` passou a verificar plataforma no `main()` e retornar exit code 0 em não-Linux

### [core-implementation](openspec/changes/archive/2026-06-27-core-implementation) Estabelece toda a fundação do projeto: Clean Architecture, indicadores de fluxo, ingestão B3, CLI/GUI e empacotamento

#### Added

- Estrutura de projeto: Criação de diretórios `src/flowscope/` e `tests/` com `pyproject.toml`, seguindo Clean Architecture tradicional (domain, application, infrastructure, presentation)
- Ingestão de dados: Cliente HTTP para API B3 (two-step: requestname → token → download), parser de CSV consolidado, seleção de datas via janela Fibonacci (d-1, d-2, d-3, d-5, d-8, d-13, d-21) com ajuste para dias úteis
- Indicadores: Cálculo de Cumulative Volume Delta (CVD), Volume Weighted Average Price (VWAP) e Volume Profile a partir dos dados consolidados
- CLI: argparse com flags `--gui`, `--tickers`, `--vwap`, `--cvd`, `--help`, `--version`, `--create-shortcut`
- GUI: Interface Tkinter com tkcalendar (seleção de data), matplotlib (histogramas VWAP/CVD, scatter plot VWAP×CVD com quiver opcional), campo de seleção/edição de tickers com load/save `.txt`, campo readonly para análise automática (placeholder), botões de clipboard
- Clipboard: Exportação CSV (texto) via pyxclip; exportação de gráfico (imagem) via ctypes + comandos nativos por plataforma
- Atalho desktop: `--create-shortcut` gera `.desktop` file no Linux
- Testes: Estrutura de testes em `tests/` com unittest/pytest

#### Changed

- Ícones: Movidos de `icons/` para `src/flowscope/icons/`
- Empacotamento: Atualização de `flowscope.spec` (PyInstaller) e `Makefile` para refletir a nova estrutura

### [especificacoes-vs-implementacao-diffs](openspec/changes/archive/2026-06-27-especificacoes-vs-implementacao-diffs) Alinha especificações com a implementação real, documentando divergências de API, parsing e testes

#### Fixed

- `data-ingestion`: B3 API descrita como POST mas implementada como GET — spec desatualizada
- `data-ingestion`: Exemplo de datas Fibonacci no spec diverge do cálculo real implementado
- `clipboard-export`: Cópia CSV tem fallback Tkinter não descrito no spec; falha de cópia de imagem usa `print(stderr)` em vez de feedback na GUI
- `project-scaffold`: `requirements.txt` não inclui `requests>=2.28` presente no `pyproject.toml`; README tem seção "Interface desktop" vazia
- `volume-indicators`: Sem teste para cenário "Menos de 15 tickers disponíveis"
- `desktop-shortcut`: Sem teste para cenários Windows/macOS

### [fix-verification-issues](openspec/changes/archive/2026-06-27-fix-verification-issues) Corrige os problemas encontrados na auditoria de verificação da `core-implementation`

#### Added

- CSV export columns: Add daily VWAP/CVD columns to CSV export output (one column per window date)
- Quiver arrows: Implement temporal arrow visualization connecting each ticker's d-1 → d position in the scatter plot
- Auto-refresh on edit: Trigger chart refresh when user edits the ticker list text field
- Ticker load refresh: Trigger chart refresh after loading tickers from a `.txt` file

#### Fixed

- CLI export: Wire `--tickers` flag to `--vwap`/`--cvd` export paths so `flowscope --vwap --tickers lista.txt` filters by the provided tickers
- Non-Linux exit code: Change `--create-shortcut` on non-Linux to exit with code 0 instead of 1

### [idiv-portfolio-default-filter](openspec/changes/archive/2026-06-27-idiv-portfolio-default-filter) Pré-carrega a carteira do IDIV como filtro padrão e filtra apenas o segmento CASH

#### Added

- Novo método `fetch_idiv_portfolio()` no `B3Client` para baixar a carteira do IDIV da B3
- Cache local do portfólio IDIV com TTL (7 dias) — revalidate apenas se expirado
- Filtro `SgmtNm == "CASH"` aplicado no parser do CSV, descartando linhas de outros segmentos (BMF, FUTURE, etc.)
- Quando o campo de filtro de tickers estiver vazio e o usuário pressionar "Carregar" ou "Filtrar", o sistema busca automaticamente a carteira do IDIV e a usa como filtro

#### Changed

- Usuário pode limpar o filtro manualmente para recarregar a carteira IDIV, ou editar a lista para personalizar

### [ui-ajustes-filtro-statusbar](openspec/changes/archive/2026-06-27-ui-ajustes-filtro-statusbar) Reposiciona a barra de status e substitui o filtro automático por botão Filtrar manual

#### Added

- Adicionar botão "Filtrar" ao lado de "Salvar Tickers" e "Carregar Tickers"

#### Changed

- Mover a barra de status para abaixo dos botões "Copiar Dados" e "Copiar Gráfico"
- O filtro só é aplicado quando o botão "Filtrar" é pressionado manualmente

#### Removed

- Remover o filtro automático ao digitar (evento KeyRelease) e ao carregar arquivo

### [ui-polish-and-usability](openspec/changes/archive/2026-06-27-ui-polish-and-usability) Polish geral da GUI: atalhos, tooltips, feedback visual, layout consistente e preferências persistentes

#### Added

- App icon set on the window for taskbar display (`.ico` on Windows, `.png` on Linux)
- Statusbar with Unicode state icons (✓ ⏳ ⚠ ℹ) and auto-clearing timed messages
- Ticker counter label updated live (e.g. "Tickers (37)" / "Exibindo 42 de 300")
- Show currently loaded reference date on the UI
- Confirmation flash on copy actions ("✓ Dados copiados") auto-clearing after 2.5s
- Keyboard shortcuts: Enter→Carregar, Ctrl+C→Copiar Dados, F5→Recarregar (avoids system conflicts)
- Double-click on ticker list filters/selects that ticker
- Tooltips on all controls (indicators, buttons, chart selector)
- Hand cursor (`hand2`) on all interactive controls
- Initial keyboard focus on DateEntry
- ttk.Separator between export buttons
- Dynamic chart title label above the chart area (e.g. "VWAP Histogram")
- Empty-state message when filter removes all tickers
- User-friendly error display (short message + expandable details)
- Filtered/Total count in status (e.g. "Exibindo 42 de 300 ativos")
- Persist window geometry and PanedWindow sash position to `~/.flowscope/config.json`
- Dynamic window title: "FlowScope — YYYY-MM-DD — N ativos"
- Animated processing indicator using `after()` (spinning dots)
- Context menu (right-click) on ticker list: Copy, Remove, Select All, Clear

#### Changed

- Controls disabled during loading (Carregar button + DateEntry) with wait cursor
- Chart type selector wrapped in a LabelFrame titled "Visualização"
- Bottom action buttons wrapped in a LabelFrame titled "Exportação"
- Consistent padding constants (`PAD_SMALL=4`, `PAD=8`, `PAD_LARGE=12`) replacing ad-hoc values
- Internal button padding (`ipadx=8`, `ipady=2`)
- Subtle toolbar border (GROOVE) around action buttons
- Consistent use of `ttk` themed widgets where possible

[1.3.3]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.3
[1.3.2]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.2
[1.3.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.1
[1.3.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.0
[1.2.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.2.0

[1.1.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.1.0

[1.0.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.0.0

[0.9.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.9.0

[0.8.2]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.8.2

[0.8.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.8.1

[0.8.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.8.0

[0.7.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.7.0

[0.6.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.6.0

[0.5.2]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.5.2

[0.5.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.5.1

[0.5.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.5.0

[0.4.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.4.0

[0.3.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.3.1
[0.3.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.3.0
[0.2.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.2.1
[0.2.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.2.0
[0.1.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.1.0

See main [CHANGELOG](CHANGELOG.md) for newer releases.
