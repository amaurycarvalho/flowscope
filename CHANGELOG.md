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

## [1.4.1] — 2026-10-16

### [fundamentos-e-downloads-resilientes](openspec/changes/archive/2026-10-16-fundamentos-e-downloads-resilientes) Fundamentos no host coberto pelo certificado, identidade/nome da B3 como fallback, resolução CVM API-only e downloads compartilhados com validação de conteúdo e orçamento por item

#### Added

- Nome de exibição do ativo obtido da identidade B3 já existente (`GetInitialCompanies`: `companyName`/`tradingName`) como fallback para ações/BDR, mantendo `fundName` para FII.
- Helper único de download de arquivos (PDF/HTML) com validação de conteúdo (assinatura `%PDF` ou HTML esperado) e orçamento total por item, aplicado a documentos relevantes, informe mensal, proventos/informe e documentos vinculados de notícias.

#### Changed

- Modo degradado visível: registrar por ticker a fonte/URL que falhou, em vez de varrer silenciosamente toda a cadeia de fallback.
- Só cachear `None` quando a API respondeu e não achou; falha de resolução (rede/HTTP) deixa de ser cacheada como ausência.
- FNET: repetir em resposta `200` não-PDF e tratar o `403` intermitente como repetível; opção de resolver via `visualizarDocumento` → `iframe exibirDocumento`.
- rad.cvm: renovar token/sessão antes de repetir o POST `ExibirPDF`, com backoff e validação `%PDF`.
- Ausência de dados de negociação em dia não útil (feriado) tratada como ausência, sem requisição nem erro.
- `fundamental_job` identificável no log do watchdog com o ticker em processamento.
- Desfecho da aquisição distingue falha de "nada novo" em Documentos e, de forma consistente, em Notícias e Fundamentos.

#### Fixed

- Host do Fundamentus corrigido para o apex coberto pelo certificado (`fundamentus.com.br`) nos três endpoints (`detalhes`, `proventos`, `fii_proventos`) e no `robots.txt`.

#### Removed

- Fallback `empresas-listadas.csv` removido, tornando a resolução `ticker → codeCVM` API-only. **BREAKING (interno)**.

### [renomear-flowscopebr](openspec/changes/archive/2026-10-16-renomear-flowscopebr) Nome exibido "FlowScope" renomeado para "FlowScopeBR" em título, aba "Sobre", chat/system prompts, CLI, atalho e documentação, preservando identificadores e caminhos internos

#### Changed

- Renomear "FlowScope" para "FlowScopeBR" em todos os textos visíveis: título da janela, aba "Sobre", textos e *system prompts* do chat de I.A., saída/ajuda da CLI, campo `Name=` do atalho e documentação (`README.md`, `docs/PRD.md`, `docs/misc/*.md`).
- Formato de nome+versão na aba "Sobre" passa de `FlowScope vX.Y.Z` para `FlowScopeBR vX.Y.Z`.
- Saída de `--version` da CLI passa a `FlowScopeBR vX.Y.Z`.
- Preservados deliberadamente `USER_AGENT`, o nó `/flowscope`, nomes de classes/módulos, docstrings internas, `~/.flowscope`, o nome do pacote/binário e os registros históricos `docs/rfcs/`, `docs/adrs/` e `CHANGELOG-ARCHIVE.md`.

### [titulo-watchlist-arquivo](openspec/changes/archive/2026-10-16-titulo-watchlist-arquivo) Título da janela com o nome-base do arquivo de watchlist e asterisco de alteração não salva, com persistência do caminho do último arquivo

#### Added

- Persistência em `~/.flowscope/config.json` da nova chave `last_ticker_file` com o caminho completo do último arquivo de watchlist carregado ou salvo.

#### Changed

- Título da janela passa ao formato `FlowScopeBR v{versão} — <arquivo>[*]`, com `<arquivo>` = nome-base do arquivo e `[*]` quando o conteúdo foi editado e ainda não salvo; sem arquivo, exibe `Nova lista.txt`.
- Carregar um arquivo atualiza o título e guarda o caminho completo; **Salvar** atualiza o nome/caminho e remove o asterisco.
- Editar o conteúdo do watchlist (adicionar/remover tickers) marca alteração não salva; mudar seleção/filtro não marca.
- Clicar em IBOV/IDIV/IFIX exibe `<ÍNDICE>.txt` sem asterisco e não persiste o nome.
- Aposentado o requisito "Título dinâmico da janela" (data + N ativos, nunca implementado) e registrado o novo formato na spec `ui-polish`.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.4.1...HEAD
[1.4.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.4.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
