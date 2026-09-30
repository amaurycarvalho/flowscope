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

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.3.3...HEAD
[1.3.3]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.3

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
