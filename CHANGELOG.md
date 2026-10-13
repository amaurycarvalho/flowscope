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

## [1.3.7] — 2026-10-13

### [convencao-paths-relativos](openspec/changes/archive/2026-10-13-convencao-paths-relativos) Standard de engenharia exigindo referências a arquivos do projeto por caminhos relativos à raiz, proibindo caminhos absolutos específicos da máquina

#### Added

- Adicionar um standard de engenharia exigindo que referências a arquivos do projeto usem caminhos relativos à raiz (ou resolvidos a partir de `__file__`/configuração).

#### Changed

- Proibir caminhos absolutos específicos da máquina em código, testes, scripts e documentação.
- Estender a mesma regra a ferramentas de desenvolvimento e agentes que acessam arquivos do projeto.

### [finalizar-extracao-definitiva](openspec/changes/archive/2026-10-13-finalizar-extracao-definitiva) Confirmação ao término do lote para reprocessar ou marcar como definitivos os itens de extração não conclusiva (parcial, falha e PDF protegido), persistindo o texto definitivo com nota e gerando o resumo correspondente

#### Changed

- Ao término do lote, quando restarem itens não conclusivos (parcial + falha + protegido), o sistema informa a quantidade e pergunta se o usuário quer tentá-los novamente; em caso negativo, pergunta se quer marcá-los como definitivos.
- "Tentar novamente" reprocessa apenas os itens da lista; para os protegidos, a senha é pré-coletada (rota manual) antes do reprocessamento, e sem senha informada o item permanece pendente.
- "Marcar como definitivo" persiste o texto definitivo do item — `PARCIAL`: o texto parcial acrescido de uma nota; `FALHA`/`PROTEGIDO`: apenas a nota — e gera o resumo citando a limitação: via LLM no parcial e determinístico (sem LLM) na falha e no protegido. A partir daí o item sai dos pendentes e não é mais reextraído no lote.
- A nota de extração é embutida no próprio texto persistido, de modo que resumos futuros a citem (modifica o invariante do cache de texto, com exceção de finalização explícita).
- Escopo: extração parcial, falha crítica e PDF protegido. Ausência definitiva de texto (`SEM_TEXTO`) e apontador de notícia "Geral" não resolvido ficam fora.

### [identificar-item-timeout-noticias](openspec/changes/archive/2026-10-13-identificar-item-timeout-noticias) Watchdog nomeia a notícia em processamento no encerramento por inatividade e a resolução do documento vinculado passa a respeitar o orçamento de extração por item

#### Added

- A extração de PDF passa a oferecer o caminho orçado a partir de bytes, para que o PDF baixado de um vínculo também respeite o orçamento.

#### Changed

- O watchdog de inatividade/liveness passa a registrar, no aviso de encerramento involuntário, a descrição do item em processamento, exposta pelo worker por um novo gancho (`JobContext.descrever`) que não afeta a detecção de travamento.
- O lote de resumos (e a finalização de extração) marcam o item corrente antes de cada extração/resumo, de modo que o aviso do watchdog identifique a notícia.
- A resolução do documento vinculado de notícias "Geral" passa a ser limitada pelo mesmo orçamento de extração por item (90s, escalável em retry), cobrindo as requisições de rede e o parse do PDF baixado; ao esgotar o orçamento, a notícia permanece pendente e o evento é registrado no log nomeando o item.
- Efeito: a duração de cada notícia fica abaixo do limite de inatividade e qualquer encerramento anormal (ou estouro de orçamento) nomeia o item.

### [logs-diarios-e-housekeeping](openspec/changes/archive/2026-10-13-logs-diarios-e-housekeeping) Log diário datado com rolagem de arquivo obsoleto, housekeeping com retenção configurável, botão que abre a pasta de logs e warnings de extração parcial/sem texto

#### Changed

- **Log diário**: o arquivo ativo permanece `~/.flowscope/logs/flowscope.log`; à meia-noite ele é rotacionado para `flowscope-YYYY-MM-DD.log` e um novo arquivo ativo é aberto, de modo que cada dia corresponda a um arquivo datado.
- **Rolagem de arquivo obsoleto**: na inicialização, se o `flowscope.log` ativo for de um dia anterior (app ficou fechado na virada), ele é renomeado para `flowscope-YYYY-MM-DD.log` antes de abrir o handler diário, evitando misturar dias.
- **Housekeeping com retenção configurável**: na inicialização da GUI, backups datados com mais de `N` dias são apagados (`N` = dias anteriores a hoje, padrão `7`, ou seja, mantém hoje + 7 anteriores); `N` é lido de `~/.flowscope/config.json` (`log_retention_days`), ajustável sem recompilar.
- **Botão de log abre a pasta**: o botão "Abrir log da aplicação" passa a abrir o diretório `~/.flowscope/logs` no aplicativo padrão, em vez de um arquivo específico; a mensagem de erro técnico do apresentador aponta para a pasta.
- **Warnings de extração**: documentos das sub-abas "Documentos" e "Notícias" processados parcialmente (extração de texto) ou sem texto passam a registrar uma linha curta de `WARNING`, identificando o documento por ticker e nome e, no caso parcial, a quantidade de páginas com falha.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.3.7...HEAD
[1.3.7]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.7

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
