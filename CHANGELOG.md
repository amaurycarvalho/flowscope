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

## [1.3.4] — 2026-10-08

### [deduplicacao-por-hash](openspec/changes/archive/2026-10-08-deduplicacao-por-hash) Deduplicação por SHA-256 do conteúdo bruto de documentos e notícias, mantendo apenas o registro mais antigo e podando os derivados do item descartado

#### Added

- Cálculo de SHA-256 do conteúdo bruto de cada documento/notícia baixado e verificação contra um registro de hashes antes de persistir.
- Regra "primeiro hash registrado vence": em colisão exata de conteúdo, o arquivo recém-baixado e o seu registro são descartados; o existente permanece.
- Escopo do registro por ticker para documentos (compartilhado entre as três raízes — `bdr/`, `informe-mensal/`, `documentos-relevantes/`) e único global para notícias (`NOTICIAS`), deduplicando inclusive entre seções.
- Poda dos derivados do item descartado: resumo, texto e, para notícias, a entrada do `index.json`.
- Housekeeping no "Atualizar": varredura cronológica dos arquivos em cache sem hash, aplicando a mesma regra para eliminar duplicatas legadas.
- Guarda de conteúdo: corpos vazios, apenas espaços ou abaixo de um piso mínimo não entram no registro.
- Validação do canônico: se o arquivo canônico de um hash não existe mais, a entrada é descartada e o novo arquivo passa a ser registrado.

#### Changed

- Hook de download em todas as vias (documentos relevantes, informe mensal, avisos de BDR e notícias) passa a verificar o hash antes de persistir.
- `documentos-ticker-panel` e `noticias-panel`: o botão "Atualizar" passa a executar, além da aquisição, o housekeeping de deduplicação por conteúdo.

### [desfecho-termino-status](openspec/changes/archive/2026-10-08-desfecho-termino-status) Desfecho terminal explícito no ciclo de vida dos jobs (`SUCESSO`/`FALHA`/`CANCELADO`/`ABORTADO`), com rede de segurança de status e mensagens de conclusão honestas

#### Added

- Desfecho terminal explícito no ciclo de vida do job: `SUCESSO`, `FALHA`, `CANCELADO` e `ABORTADO`, carregado pelo evento de término.
- O desfecho é declarado pelo worker (que sabe se recuperou falhas) e tem default por exceção que escapa; exceção não tratada e `BaseException` resultam em `FALHA`.
- Rede de segurança de status: falha fatal que não teve callback de erro consumidor produz mensagem genérica de falha, em vez de "Pronto.".
- Fallback de falha na pré-visualização de documento/notícia, que não fica mais presa em "Carregando…".

#### Changed

- Separação entre cancelamento do usuário (`CANCELADO`) e encerramento involuntário pelo watchdog (`ABORTADO`), que antes terminavam ambos com `cancelado=True`.
- **BREAKING (interno)**: removida a dependência do token global `presenter._cancel_token`; o desfecho passa a ser a única autoridade sobre a mensagem.

#### Fixed

- A mensagem de conclusão de aquisição de documentos/notícias não afirma mais atualização quando nada foi adquirido.

### [extracao-pdf-resiliente](openspec/changes/archive/2026-10-08-extracao-pdf-resiliente) Extração de texto de PDF resiliente com status tipado, tolerância por página, senha vazia automática e senha interativa opcional

#### Added

- Extrator de PDF único e resiliente na camada de aplicação, com resultado tipado (`OK`, `PARCIAL`, `SEM_TEXTO`, `FALHA`, `PROTEGIDO`) e tolerância por página.
- Tentativa automática de `decrypt("")` para PDFs criptografados antes de marcá-los como protegidos.
- Extração autenticada opcional por senha, para o fluxo interativo.
- Diálogo de senha no preview interativo de Documentos e do documento vinculado das Notícias, com limite de 3 tentativas por documento/seleção; o texto obtido é cacheado e a senha nunca é persistida, e o fluxo em lote nunca abre diálogo.
- Anotação do texto parcial e retentativa automática da extração ao re-selecionar o documento ou ao processar "Resumir pendentes".

#### Changed

- Semântica de cache: apenas resultados definitivos (`OK` completo e `SEM_TEXTO`) são persistidos; `PARCIAL`, `FALHA` e `PROTEGIDO` não são gravados, permitindo nova tentativa.
- Extração duplicada unificada: `infrastructure/b3/bdr/text.extrair_texto` passa a delegar ao extrator único, mantendo a assinatura `bytes -> str`.
- Marcador de ausência (`SEM_TEXTO`/`tem_texto`) unificado em `domain/documents/texto.py`, com re-export para os importadores atuais.

### [filtros-evolucao-fundamentos](openspec/changes/archive/2026-10-08-filtros-evolucao-fundamentos) Evolução dos Fundamentos passa a montar as séries conforme o período (30/60/90 dias) e o método de amostragem selecionados na barra superior

#### Changed

- A Evolução dos Fundamentos passa a montar as séries a partir do período (30/60/90 dias) e do método de amostragem selecionados nos comboboxes da barra superior.
- A janela é ancorada na data de referência atual; sem observações nela, a âncora recua para a observação mais recente do cache, sem aquisição de rede.
- Cada método (Fibonacci, Fibonacci reverso, Fibonacci duplo, Monte Carlo, Monte Carlo duplo, Todos os dias) seleciona um subconjunto das observações da janela, preservando extremos, `≤2` observações, ordem crescente e sem duplicatas.
- **BREAKING (spec-level)**: o requisito "Amostragem Fibonacci das datas" deixa de ser fixo e passa a depender da configuração selecionada; novo requisito de janela de período.
- Monte Carlo passa a ter amostra determinística por `(ticker, janela, método, n)`, para o gráfico não "pular" a cada render.
- Mudar qualquer um dos comboboxes re-renderiza o painel mesmo sem dados B3 carregados, e o título do painel passa a informar as datas exibidas em relação ao total do período.

### [fundamentus-erros-e-bdr](openspec/changes/archive/2026-10-08-fundamentus-erros-e-bdr) Classificação correta de erros do Fundamentus (`TickerNotFound` × `LayoutChanged`) e consulta ao portal pulada para BDRs

#### Changed

- Quando a página do Fundamentus não traz conteúdo utilizável (tabela/linhas vazias), o parser passa a sinalizar `TickerNotFound` em vez de `LayoutChanged`; `LayoutChanged` fica reservado ao caso em que a página tem conteúdo parseável mas faltam os rótulos obrigatórios.
- O `CompositeFundamentalProvider` registra `TickerNotFound` em `INFO`, sem traceback, e mantém `WARNING` com traceback apenas para `LayoutChanged` e `NetworkError` reais.
- Ativos classificados como `TipoAtivo.BDR` são pulados pela fonte Fundamentus nos compostos de campos fundamentalistas e de FFO, sem chamada de rede; dividendos permanecem inalterados.

### [guidance-avaliacao-por-rg](openspec/changes/archive/2026-10-08-guidance-avaliacao-por-rg) Avaliação de guidance por Relatório Gerencial em ledger por hash, com IA prevalecente, cascata de fontes e fim do portão de data

#### Changed

- O cache de guidance por FII passa a ser um ledger por RG (chave = hash SHA-256 do PDF), registrando o método (`ia`/`deterministico`) e o resultado (guidance ou ausência avaliada).
- A avaliação deixa de ter portão de data: todo RG processado é avaliado uma vez por método, exceto em falha na interação com a IA, que não grava `ia` e mantém o RG elegível a nova tentativa.
- A IA prevalece sobre o determinístico por RG; um resultado de IA sobrescreve a entrada determinística do mesmo RG.
- A avaliação segue a cascata resumo curto → resumo longo → texto extraído, parando na primeira fonte com guidance; sem nenhuma delas, registra ausência para aquele RG.
- A disponibilidade da IA passa a ser "provedor de chat configurado".
- O campo `Informações adicionais` passa a exibir o guidance da entrada com maior `data_relatorio` entre as avaliadas com resultado.
- Migração do cache v1 (guidance único, sem origem) para uma entrada `deterministico`.

#### Removed

- O flag `llm.guidance.enabled` e a exposição `guidance_llm_disponivel`.

### [llm-retry-transitorio](openspec/changes/archive/2026-10-08-llm-retry-transitorio) Retry com backoff exponencial e jitter no adaptador liteLLM, repetindo apenas erros transitórios e contando as tentativas no rate limiter

#### Added

- Retry com backoff exponencial e jitter no `LiteLLMChatAdapter.complete`, repetindo apenas erros transitórios (`LLMServiceUnavailableError`, `LLMRateLimitError`, `LLMCommunicationError`).
- Propagação imediata de erros permanentes (`LLMProviderError`, `LLMConfigurationError`, `LLMUnavailableError`), sem consumir tentativas.
- Injeção de `sleeper`/`clock` para tornar o retry observável e testável, no padrão do `RateLimiter` e de `infrastructure/b3/retry.py`.

#### Changed

- Cada tentativa física, incluindo os retries, passa a adquirir uma permissão do `RateLimiter`.
- Ao esgotar as tentativas, a exceção de domínio final segue propagando e o lote continua tratando-a como hoje.

### [persistencia-splitter-e-cursor-ocupado](openspec/changes/archive/2026-10-08-persistencia-splitter-e-cursor-ocupado) Persistência da largura do painel direito do divisor principal e correção do cursor de espera preso em widgets criados durante a operação

#### Changed

- A preferência de layout passa a persistir e restaurar a largura do painel direito do divisor principal, em vez da coordenada absoluta x do sash, com clamp para não colapsar o painel esquerdo; o formato legado de 4 valores é descartado e o tratamento morto da `_left_pw` é removido.
- Diálogos/`Toplevel` passam a ser tratados apenas pelo hover, e os managers locais (chat, pré-visualização de documentos e resumos de notícias) permanecem fora do cursor de espera global.

#### Fixed

- O cursor de espera deixa de vazar em widgets criados após a entrada no estado ocupado, com registro do cursor de repouso e auto-limpeza do `watch` durante o movimento quando não há operação ativa.
- Substituição de `unbind_all("<Motion>")` pela remoção do binding específico, sem afetar outros bindings globais.

### [seletor-modelo-ativo-llm](openspec/changes/archive/2026-10-08-seletor-modelo-ativo-llm) Combobox de provedor ativo e botão de configuração com ícone substituem o botão "I.A.", com estado `llm.chat.active` e troca de modelo sem republicar o rótulo

#### Added

- Novo estado persistido `llm.chat.active`: lista dos provedores cuja conexão foi testada com sucesso e cujo teste corresponde à configuração salva (string `api_url`+`model`+`api_key`, sem `rpm`).
- Combobox de seleção de modelo ativo (provedores em `active` + opção `None`), que grava `llm.chat.provider` imediatamente, preservando `providers` e `active`.
- Migração: na primeira leitura, o provedor corrente diferente de `none` e ausente de `active` é semeado em `active`; os demais provedores exigem re-teste.
- Comportamento definido na troca de modelo no meio da sessão: a sessão e a cota de navegação são herdadas e o rótulo de tokens não é republicado, evitando misturar modelos.

#### Changed

- O botão textual "Configuração" da aba "Chat AI" e o botão "I.A." das sub-abas "Documentos" e "Notícias" passam a ser um combobox de modelo ativo + botão de configuração com ícone (`ai-properties.png`).
- O modal de configuração passa a ativar e selecionar automaticamente o provedor ao salvar após um teste bem-sucedido dos valores salvos; sem teste correspondente, mantém a seleção anterior e apenas grava a entrada.
- O combobox e o botão de ícone ficam desabilitados durante processamento (envio no chat; jobs em Documentos/Notícias).

#### Removed

- O botão textual "I.A." das sub-abas "Documentos" e "Notícias".

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.3.4...HEAD
[1.3.4]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.4

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
