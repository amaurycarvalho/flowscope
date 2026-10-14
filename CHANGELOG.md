# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [cli-acoes-atualizacao](openspec/changes/cli-acoes-atualizacao) Subcomandos CLI de ação para agendamento externo (carregar watchlist, atualizar fundamentos/documentos/notícias e resumir pendentes), marcador de data de referência dos fundamentos e escrita concorrente segura

#### Added

- Novo grupo de subcomandos CLI de ação (`carregar`, `atualizar`, `resumir`) para agendamento externo: `flowscope carregar watchlist`, `flowscope atualizar fundamentos|documentos|noticias` e `flowscope resumir documentos|noticias`.
- Marcador `last_fundamentals` (`{data, fetched_at}`) em `config.json`, com resolução `marcador → fallback last_date`, escrito pela CLI e pela GUI ao carregar fundamentos.
- Leitura consultiva da data de referência: nó `/fundamentos/data-referencia` na árvore de conhecimento, operação `data_referencia` no núcleo de navegação, tool MCP `nav_data_referencia` e comando `flowscope nav data-referencia`.
- Segurança de escrita concorrente: escrita atômica com temporário único, lock global de ação na CLI e participação da GUI no mesmo lock nas fases de escrita.

#### Changed

- Núcleo de composição neutro `montar_nucleo()` reusado por GUI e CLI, e extração do núcleo do lote de resumos para a camada de aplicação.

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

## [1.4.0] — 2026-10-14

### [navegacao-mcp](openspec/changes/navegacao-mcp) Núcleo de navegação compartilhado, servidor MCP embutido (`flowscope --mcp`) e subcomandos `flowscope nav ...`

#### Added

- `NavegacaoCore` em `application/navegacao/`, com operações canônicas, limites centralizados, paginação por cursor opaco, erros estruturados e confinamento de leitura; reusado pelo chat, pela CLI e pelo MCP.
- Servidor MCP stdio embutido iniciado por `flowscope --mcp`, alvo da revisão `2026-07-28`, com `server/discover`, `tools/list` (sete tools `nav_*`) e `tools/call`, sem dependência nova.
- Subcomandos `flowscope nav listar|obter|contar|existe|buscar|buscar-semantico|manifesto`, com saída JSON e `--pretty`.
- Guia [docs/misc/mcp.md](docs/misc/mcp.md) e link no `README.md`.

#### Changed

- `ProtocoloNavegacao` passa a ser um adaptador fino sobre o `NavegacaoCore`, mantendo `[RESULTADO_NAVEGACAO]`, `foco` e o limite de 8 operações por turno; o reset permanece no loop do chat.
- Listagens passam a ser ordenadas deterministicamente por caminho canônico.

### [orientacao-chat-arvore](openspec/changes/archive/2026-10-13-orientacao-chat-arvore) Orientação da aba "Chat AI" atualizada para descrever a árvore de conhecimento navegável, as origens de contexto como ramos, o protocolo de navegação da LLM e a leitura somente de cache

#### Changed

- O texto de orientação da aba "Chat AI" em `TAB_CONTENT` passa a descrever a árvore de conhecimento navegável (ramos de origem do contexto), o protocolo de navegação da LLM, os orçamentos e a leitura somente de cache.
- Mantida a estrutura do `body` do `TAB_CONTENT` (título e seções Objetivo, Responde a pergunta, Como usar, Contexto enviado, Como interpretar) e o enquadramento dos ramos disponíveis.

### [reposicao-datas-uteis-b3](openspec/changes/archive/2026-10-14-reposicao-datas-uteis-b3) Datas substitutas de amostragem restritas a dias úteis da B3, com o predicado de feriados centralizado no domínio e reusado pelo calendário

#### Added

- Predicado de dia útil da B3 centralizado no domínio (`domain/b3/calendario.py`, com a lista de feriados nacionais e `is_business_day`), respeitando `layer-boundaries`.

#### Changed

- `infrastructure/b3/calendar.py` e `infrastructure/b3/holidays.py` passam a consumir/reexportar a definição do domínio, eliminando a duplicação.
- Testes unitários cobrindo a candidata em feriado pulada, a continuidade da busca e o resolvedor do calendário usando a mesma definição.

#### Fixed

- `_find_replacement_date` passa a usar `is_business_day` em vez de `candidate.weekday() >= 5`, de modo que feriados nacionais nunca sejam consultados como data substituta.

### [resumo-guidance-system-prompt](openspec/changes/archive/2026-10-14-resumo-guidance-system-prompt) Instruções estáveis de resumo de documentos/notícias e de avaliação de guidance em `system_prompt`, com orçamento de caracteres compatível com a fórmula XYZ

#### Changed

- `ResumirDocumentoUseCase` passa a enviar as instruções em um `system_prompt` constante e o texto do documento como única mensagem `user`, cobrindo as sub-abas "Documentos" e "Notícias".
- `AvaliarGuidanceUseCase` aplica o mesmo padrão: instruções em `system_prompt` constante e o trecho como mensagem `user`.
- Ajustes pontuais de prompt incorporam à versão enxuta regras da versão detalhada (sem markdown/listas, nada antes de `CURTO:`/`LONGO:`, fidelidade ao conteúdo, guidance vazio ⇒ saída vazia, valor único ⇒ mínimo = máximo, ponto decimal sem `R$`, dúvida em guidance ⇒ `NAO`).
- Orçamento de caracteres compatível com o XYZ: tetos de salvaguarda do resumo elevados (curto 280 → 450, longo 1500 → 2000) e orçamento declarado no prompt (400 / 1800), sem cortar a conclusão.
- `docs/misc/llm-payloads.md` (§1.1 e §1.5) atualizado com o payload separado em `system`/`user`.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.4.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
