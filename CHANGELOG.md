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

## [1.7.0] - 2026-10-31

### [calendario-feriados-anbima](openspec/changes/archive/2026-10-31-calendario-feriados-anbima) Calendário ANBIMA como fonte única de feriados por ano, com cache, fallback, aba `Feriados` e correção da data local no botão "Hoje"

#### Added

- Adotar o calendário ANBIMA como fonte única de feriados por ano, com origem por feriado, normalização de datas/nomes, validação do dia da semana, cache em arquivo por ano, TTL por recência, cache negativo para ano futuro não publicado, fallback para cache anterior e modo degradado somente-fim-de-semana.
- Adicionar a aba `Feriados` na GUI: árvore ano/mês/dia construída apenas do cache, textbox somente leitura, botão de atualização com `view-refresh`/`content-loading`, atualização em background e seleção preservada.

#### Changed

- Recuperar e adaptar o subsistema de calendário já copiado: renomear `b3_selic_pre` para `flowscope`, corrigir caminhos de cache, usar o lock/escrita atômica existentes e manter compatibilidade com Python 3.10.
- Garantir o calendário do ano da data de referência antes das cargas, de forma best-effort: falha do calendário não bloqueia a carga principal, que segue com cache anterior ou apenas fim de semana.
- Resolver a data de referência para o dia útil anterior quando ela cair em fim de semana ou feriado. A amostragem existente continua avançando para o próximo dia útil, preservando o contrato de `sampling-strategy`.
- Expor consulta e exportação: CLI com `consultar feriados`, `exportar feriados` (CSV/JSON) e `atualizar feriados`; MCP com tools `calendario_*` somente-leitura e somente-cache, sem gravar arquivos.
- Manter 24/12 e 31/12 como recesso local da B3, complementando a ANBIMA quando caem em dia de semana e não estão na página.
- Manter fora de escopo: a janela de evolução de 7/14/21/28 dias, por não ter consumidor no FlowScope atual.

#### Fixed

- Corrigir o botão "Hoje" e o `maxdate` do DateEntry para usarem a data local do processo, não UTC.

#### Removed

- Remover a lista estática de feriados e fiar a verificação de dia útil em uma porta de aplicação alimentada pelo cache do calendário.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.7.0...HEAD
[1.7.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.7.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
