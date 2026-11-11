# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [chat-fontes-estruturadas](openspec/changes/chat-fontes-estruturadas) Fontes consultadas pelo Chat AI separadas da resposta em campo estruturado, com checkbox "Exibir fontes" e cópia seguindo a tela

### [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui o placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional

### [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões

### [litellm-model-cost-map-offline](openspec/changes/litellm-model-cost-map-offline) Primeira importação do `litellm` usa o catálogo local de model cost map, sem busca externa automática em máquinas offline

### [llm-chat-rag](openspec/changes/llm-chat-rag) Recuperação vetorial como evolução da `llm-chat`, com VectorStore SQLite, embeddings e indexação de documentos consultada pela aba "Chat AI"

### [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado, com gauge de concentração, card informativo e timeline AFT

## [1.8.1] - 2026-11-11

### [resiliencia-resolucao-fundos-b3](openspec/changes/archive/2026-11-11-resiliencia-resolucao-fundos-b3) Listagem de fundos da B3 completa e resiliente a páginas vazias, com chaves de cache versionadas e identidade persistida por ticker como fallback dos dados fiscais dos FIIs

#### Added

- Adicionar cache persistente ticker → `idFNET` → CNPJ, com nome e tipo do fundo, escrito a cada resolução bem-sucedida e consultado como fallback quando a B3 estiver indisponível ou a listagem vier incompleta.

#### Changed

- Tornar a listagem de fundos da B3 completa e resistente a respostas vazias intermitentes: `pageSize=120` (máximo aceito), repetição de páginas vazias com backoff e cache somente quando `len(results) == totalRecords`.
- Preservar a última listagem completa em caso de atualização parcial/indisponível, em vez de sobrescrever o cache com uma lista truncada.
- Invalidar as chaves de cache legadas de listagem e de resolução (versionar as chaves) para descartar listas parciais e ausências já gravadas.
- Tratar corpo vazio intermitente do `GetListClassFund` como conteúdo inválido repetível, usando o validador do motor de retry central.
- Não persistir resultados negativos (ticker sem correspondência) para não congelar falhas transitórias.
- Garantir que a identidade persistida esteja versionada, com escrita atômica e tolerância a corrupção, e que o CNPJ alimente o fallback CVM Anual mesmo quando a B3 falhar.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.8.1...HEAD
[1.8.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.8.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
