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

## [1.5.0] — 2026-10-16

### [cli-acoes-atualizacao](openspec/changes/archive/2026-10-16-cli-acoes-atualizacao) Subcomandos CLI de ação para agendamento externo (carregar watchlist, atualizar fundamentos/documentos/notícias e resumir pendentes), marcador de data de referência dos fundamentos e escrita concorrente segura

#### Added

- Novo grupo de subcomandos CLI de ação (`carregar`, `atualizar`, `resumir`) para agendamento externo: `flowscope carregar watchlist`, `flowscope atualizar fundamentos|documentos|noticias` e `flowscope resumir documentos|noticias`.
- Marcador `last_fundamentals` (`{data, fetched_at}`) em `config.json`, com resolução `marcador → fallback last_date`, escrito pela CLI e pela GUI ao carregar fundamentos.
- Leitura consultiva da data de referência: nó `/fundamentos/data-referencia` na árvore de conhecimento, operação `data_referencia` no núcleo de navegação, tool MCP `nav_data_referencia` e comando `flowscope nav data-referencia`.
- Segurança de escrita concorrente: escrita atômica com temporário único, lock global de ação na CLI e participação da GUI no mesmo lock nas fases de escrita.

#### Changed

- Núcleo de composição neutro `montar_nucleo()` reusado por GUI e CLI, e extração do núcleo do lote de resumos para a camada de aplicação.

### [reorganizar-cli-subcomandos](openspec/changes/archive/2026-10-16-reorganizar-cli-subcomandos) Reorganização das flags de leitura da CLI em subcomandos `exportar`/`consultar`, remoção das flags planas e do alias `--mcp`

#### Added

- Subcomandos de leitura `flowscope exportar vwap` e `flowscope consultar proventos|fatos|noticias|regulacao`, com saída em `stdout` ou em arquivo via `--saida`.

#### Changed

- `--output` renomeado para `--saida`, disponível nos subcomandos de leitura; `exportar vwap` mantém o arquivo padrão `vwap_<AAAA-MM-DD>.csv` e aceita sobrescrita do nome.
- Parâmetros escopados ao subcomando correto (`--categoria` só em `consultar fatos`, `--palavra` só em `consultar noticias`, datas apenas onde aplicáveis).
- `README.md`, `docs/misc/mcp.md` e specs atualizadas para a nova superfície.

#### Removed

- Flags planas de leitura `--vwap`, `--structured-earnings`, `--fatos-relevantes`, `--noticias`, `--regulacao`, `--data-inicio`, `--data-fim`, `--output`, `--categoria` e `--palavra`, sem aliases de compatibilidade.
- Caminho standalone `flowscope --tickers ARQUIVO`.
- Alias legado `flowscope --mcp`.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.5.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
