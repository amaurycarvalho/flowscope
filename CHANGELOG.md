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

## [1.5.1] - 2026-10-18

### [facilitar-atualizacoes-container](openspec/changes/archive/2026-10-18-facilitar-atualizacoes-container) Atualizações sem `--data` usam a data de hoje e `resumir documentos` sem ticker processa toda a watchlist, simplificando o entrypoint do container MCP

#### Changed

- `flowscope atualizar fundamentos`, `flowscope atualizar documentos` e `flowscope atualizar noticias` passam a usar a **data de hoje** quando `--data` não for informado, em vez da data de referência resolvida. `--data` continua tendo precedência.
- `flowscope resumir documentos` passa a aceitar o ticker como argumento **opcional**: sem ticker, processa os pendentes de todos os tickers de `last_tickers` em uma única execução, com checagem única de LLM e sem abortar o lote quando um ticker falha.
- O resultado de `resumir documentos` sem ticker passa a ser `{"resultados": {<ticker>: <desfecho>}, "falha": <bool>}`, com falha por ticker em `{"erro": {"motivo": "falha_resumo", "detalhe": "..."}}`, `falha` sempre presente e código de saída 1 quando algum ticker falha; com ticker explícito, o formato atual é preservado.
- O entrypoint de container passa a usar `flowscope resumir documentos` sem ticker, sem percorrer a watchlist em shell; `FLOWSCOPE_REFERENCE_DATE` torna-se override opcional e, quando ausente, as atualizações usam a data de hoje no fuso do container.
- Documentação de `docs/misc/mcp.md` e `README.md` atualizada para o uso do MCP em container, as atualizações opcionais na inicialização, o novo default de data e o resumo de toda a watchlist.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.5.1...HEAD
[1.5.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.5.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
