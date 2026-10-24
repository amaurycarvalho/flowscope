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

## [1.6.0] - 2026-10-24

### [2026-10-24-inferir-direitos-obrigacoes-resumos](openspec/changes/archive/2026-10-24-inferir-direitos-obrigacoes-resumos) Inferência opcional de direitos e obrigações no lote "Resumir pendentes", a partir dos resumos já persistidos, com cache por ticker, proveniência e precedência do dado oficial da CVM

#### Added

- Adicionar inferência opcional de "Direitos e obrigações" ao lote "Resumir pendentes", executada após o resumo dos documentos e antes da finalização.

#### Changed

- Usar como entrada os resumos longos já persistidos de Relatórios Gerenciais e Relatórios Mensais, sem reabrir PDFs nem reextrair texto.
- Persistir as inferências em cache separado por ticker, com proveniência do documento, trecho de evidência, confiança e versão do prompt; nunca sobrescrever os dados oficiais da CVM.
- Exibir os itens inferidos como nós distintos ("inferido pela IA") em Obrigações e Direitos, mantendo o dado oficial como autoritativo em caso de conflito.
- Habilitar a inferência apenas quando a flag `renda_fixa.inferir_no_resumo` estiver ligada, houver LLM configurada e a cobertura oficial do ticker estiver vazia ou parcial.
- Estender `flowscope resumir documentos` para executar a mesma fase de inferência e reportar o desfecho no JSON.
- Manter fora de escopo: inferência para ações, uso de texto integral de PDF na inferência, substituição de fontes oficiais e extração de eventos.

### [2026-10-24-titulos-renda-fixa](openspec/changes/archive/2026-10-24-titulos-renda-fixa) Títulos de renda fixa (FRE, SECURIT CRI/CRA e carteira de FII) em Obrigações e Direitos, com aquisição idempotente, cache por ticker e navegação cache-only no Chat AI

#### Added

- Criar modelo de domínio e árvore de "Direitos e obrigações" com "Obrigações" e "Direitos", sub-ramo "Títulos", tipo do título e títulos individuais; usar nós **agregados** rotulados quando só houver total por ticker e nós `sem-fonte` explícitos quando não houver fonte pública.
- Adicionar `AquisicaoTitulos` como serviço explícito, idempotente e cache-aware, acionado pelo mesmo botão "Atualizar" da sub-aba Documentos, internamente separado da aquisição de documentos.

#### Changed

- Ingerir títulos de renda fixa **emitidos** por companhias a partir do `FRE` da CVM (`outro_valor_mobiliario`), tratando CRI/CRA pelo **devedor econômico** do lastro.
- Complementar CRI/CRA com o `INF_MENSAL_CRI`/`INF_MENSAL_CRA` da CVM (SECURIT): emissor legal, devedor/cedente, garantias, subordinação, rating, situação, atrasos, contingências, impacto, desempenho e **LTV**.
- Ingerir a carteira de FIIs a partir do `INF_TRIMESTRAL/ativo` para os **direitos** por título (CRI/CRA, LCI/LCA) e do `INF_MENSAL/ativo_passivo` para os **agregados** de debêntures e CDB.
- Expor, para cada título, "Informações gerais", "Informações adicionais", "LTV" (quando aplicável) e "Documentos relacionados", com resumo estruturado e **links** — sem extração por IA nesta change.
- Estender a árvore do Chat AI com os caminhos canônicos de Obrigações e Direitos, incluindo agregados e `sem-fonte`, mantendo a navegação **cache-only**.
- Manter fora de escopo: `InstrumentRegistration` do BDI da B3 (fase 2), extração/sumarização de eventos por LLM e granularidade por título para CDB/LCI/LCA no lado Obrigações.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.6.0...HEAD
[1.6.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.6.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
