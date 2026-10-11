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

## [1.3.6] — 2026-10-11

### [politica-erros-http](openspec/changes/archive/2026-10-11-politica-erros-http) Política central de erros HTTP por status e motor de retry uniforme aplicado a todos os acessos de leitura/download

#### Added

- Classificador puro por código de status com quatro categorias (`PERMANENTE`, `THROTTLE`, `TRANSITORIO`, `GATEWAY`) e regra de default para `4xx`/`5xx`.
- Motor de retry central evoluído para honrar `Retry-After` (com teto), aplicar backoff com jitter e oferecer gancho de cancelamento, repetindo apenas métodos idempotentes e POSTs read-only.

#### Changed

- Adoção do motor nos acessos de aquisição/download: `funds_client` (JSON B3), fontes regulatórias, documento vinculado de notícias, PDF da CVM, corpo de notícias, BDR/B3Client, short interest e releases.
- Exceções explícitas: probes de cache condicional e o provedor de LLM ficam fora da política comum; o endpoint de programas mantém o retry de 404 por override documentado.
- 403 passa a ser permanente (não repetido), inclusive onde antes era tratado como transitório.

### [resiliencia-cota-llm](openspec/changes/archive/2026-10-11-resiliencia-cota-llm) Interrupção do lote de resumo ao esgotar a cota do provedor de IA, com desfecho único na barra de status e registro conciso

#### Added

- Interrupção imediata do lote (inclusive o contínuo de Notícias) ao encontrar `LLMRateLimitError`, preservando os resumos já gravados e mantendo os demais itens pendentes para nova tentativa.

#### Changed

- A falha de cota é reportada uma única vez na barra de status, distinguindo-a de falhas isoladas por item e orientando aguardar a renovação ou reconfigurar o provedor.
- A cota esgotada é registrada uma única vez em nível de aviso, sem traceback por item; as demais falhas transitórias mantêm o comportamento atual.

### [resumos-pendentes-e-downloads](openspec/changes/archive/2026-10-11-resumos-pendentes-e-downloads) Pendência de resumo alinhada a ausência definitiva de texto, guidance e resumos truncados, com reuso de URL e data de referência interpretada

#### Added

- Registro por escopo (ticker para documentos; global para notícias) das URLs baixadas com sucesso, consultado antes do download para impedir nova tentativa.

#### Changed

- Documentos e notícias com texto conclusivamente vazio deixam de contar como pendentes; apontadores de notícia ainda não resolvidos continuam pendentes.
- Um Relatório Gerencial já resumido que permanece `deterministico` por falha da IA não mantém o botão habilitado indefinidamente e volta a ser elegível quando a IA estiver funcional.
- `dateReference` no formato `DD/MM/AAAA HH:MM` passa a ser interpretado (hora descartada), estabilizando o caminho de cache e evitando re-download.
- A lista de pendentes de Notícias passa a regenerar resumos que não terminam em pontuação final, alinhando-se ao comportamento já existente em Documentos.

### [reuso-url-efetivo](openspec/changes/archive/2026-10-11-reuso-url-efetivo) Registro da URL no descarte por duplicidade e reuso do arquivo canônico por essa URL, em documentos e notícias

#### Changed

- Quando o download tem sucesso mas o conteúdo é descartado por duplicidade exata, a URL passa a ser registrada apontando para o caminho relativo canônico.
- Uma URL já registrada (inclusive no descarte por duplicidade) reutiliza o arquivo canônico sem nova requisição, ainda que o caminho derivado (data/categoria/slug) seja diferente.
- O serviço de deduplicação passa a expor o caminho relativo canônico do conteúdo no descarte por duplicidade.
- O registro global de URLs de Notícias passa a ser populado também no descarte por duplicidade.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.3.6...HEAD
[1.3.6]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.6

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
