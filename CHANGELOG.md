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

## [1.3.1] — 2026-09-26

### [add-layer-architecture-guardrails](openspec/changes/archive/2026-09-25-add-layer-architecture-guardrails) Fundação do programa de arquitetura: teste de fronteira generalizado para todas as camadas, allowlist de violações legadas que só encolhe e convenção de view-model documentada

#### Added

- Teste de fronteira generalizado para `domain`, `application`, `infrastructure` e `presentation`, cobrindo os imports proibidos definidos em `specs/layer-boundaries/spec.md`.
- Allowlist explícita das violações legadas (arquivo de dados versionado), que só pode encolher; import novo fora do permitido reprova o teste.
- Verificação de que a allowlist está vazia como critério de fechamento do programa.
- Documentação da convenção de view-model (aplicação devolve dados prontos; apresentação formata/desenha).

#### Changed

- **BREAKING (interno)**: a partir daqui, violações de fronteira novas reprovam o quality gate.

### [clean-architecture-layering](openspec/changes/archive/2026-09-26-clean-architecture-layering) Change chapéu que fixa o contrato de fronteira entre camadas, a convenção de view-model, o guardrail com allowlist decrescente e o orçamento de testes de UI, coordenando os incrementos filhos

#### Changed

- Define o contrato de fronteira entre camadas (`domain`, `application`, `infrastructure`, `presentation`) e a regra de importação de cada uma.
- Define a convenção de view-model: `application` devolve dataclasses prontas; `presentation` apenas formata e desenha.
- Estabelece um guardrail de fronteira com allowlist de violações legadas que só pode encolher, zerada no incremento de fechamento.
- Restringe o escopo dos testes de UI a wiring, estado de widget/botão, empty-state e ciclo de thread/queue; lógica pura passa a ser testada em `test_domain`/`test_application`.
- Coordena os incrementos filhos na ordem fundação, Documentos, Notícias, Correlação/Rede, Dominância, Quadrante+VWAP, Amplitude de Preço, Fluxo Financeiro, Fundamentos, Chat e fechamento.
- **BREAKING (interno)**: imports entre camadas passam a ser validados por teste; violações novas reprovam o quality gate.

### [documentos-resumo-lote-persistente](openspec/changes/archive/2026-09-25-documentos-resumo-lote-persistente) Resumo em lote dos documentos pendentes passa a persistir cada resultado imediatamente após a geração, sobrevivendo a interrupções

#### Added

- Seam reutilizável no fluxo compartilhado (`DocumentFlowMixin` + `ResumosPendentesJob`): gerar e persistir no worker e apenas refletir em memória na thread do Tk.

#### Changed

- Cada resumo passa a ser gravado imediatamente após a geração, na thread de trabalho do lote, antes de processar o próximo documento.
- `JsonDocumentSummaryStore.salvar` torna-se segura a escritas concorrentes (lock), evitando *lost update* entre o lote e a pré-visualização individual.
- Interrupção por cancelamento, fechamento do aplicativo ou crash passa a preservar todos os resumos já gerados; perde-se no máximo o item em processamento.

### [enforce-clean-architecture-boundaries](openspec/changes/archive/2026-09-26-enforce-clean-architecture-boundaries) Fechamento do programa: imports de `infrastructure` restritos ao composition root via portas de `application` e allowlist de fronteira zerada

#### Added

- Portas de `application` para releases, configuração de LLM e clipboard, com adaptadores em `infrastructure` ligados no composition root.
- Testes puros em `tests/test_application` para as portas/casos de uso.

#### Changed

- A verificação de nova versão (`obter_ultima_release`) sai de `presentation/gui/app_about_actions.py` para uma porta de `application`, com a comparação de versões usando `domain.version.is_newer`.
- O diálogo de LLM deixa de importar `infrastructure.llm.config`/`factory` e passa a receber uma porta de configuração de `application`.
- A cópia de gráfico deixa de importar `infrastructure.clipboard_image` e passa a receber uma porta de clipboard de `application`.
- O composition root (`presentation/cli.py`, `presentation/main.py` e `presentation/gui/app_wiring.py`) constrói os adaptadores de infraestrutura e injeta as portas, continuando a única exceção a `presentation -> infrastructure`.
- A allowlist de fronteira (`tests/architecture/allowlist.txt`) é zerada; o teste passa a exigir zero violações e zero entradas.

### [noticias-cache-sharding](openspec/changes/archive/2026-09-25-noticias-cache-sharding) Caches JSON de texto e resumo das notícias particionados por ano e mês, reduzindo o custo de O(N²) e migrando o `NOTICIAS.json` anterior

#### Added

- Wrapper de shard de notícias que deriva o shard da chave estável (`noticias/<ANO>/<MES>/<hash>.html`) e delega aos stores JSON existentes.

#### Changed

- Os caches JSON de texto e resumo das notícias passam a ser particionados por ano e mês (`NOTICIAS-<ANO>-<MES>.json`), levando o custo de O(N²) para a soma dos quadrados por shard.
- A leitura em massa de resumos do catálogo passa a mesclar os shards.
- `NoticiaArquivo.ticker` continua `NOTICIAS` e o fluxo compartilhado (`DocumentFlowMixin`, `DocumentSummaryService`, chat) permanece inalterado.
- **BREAKING (formato do cache de notícias)**: o `NOTICIAS.json` anterior é migrado uma única vez para os shards, sem reconverter.

### [noticias-resumo-lote-ordenado](openspec/changes/archive/2026-09-25-noticias-resumo-lote-ordenado) Resumo em lote das notícias passa a seguir ordem explícita por grupo e da mais recente para a mais antiga, persistindo cada resumo imediatamente

#### Changed

- Ordem explícita do lote por grupo ("Censuras Públicas" → "Condições Excepcionais" → "Programas de Aquisição de Ações" → "Geral") e, dentro de cada grupo, da notícia mais recente para a mais antiga.
- A ordenação deixa de ser efeito colateral da inserção na árvore e passa a ser regra explícita, com desempate determinista para datas ausentes ou empatadas.
- Cada resumo é gravado imediatamente após a geração, no worker, reutilizando o seam de `documentos-resumo-lote-persistente`.
- Interrupção (cancelar, fechar, crash) preserva os resumos já gerados; perde-se no máximo o item em processamento.

### [refactor-chat-context-layers](openspec/changes/archive/2026-09-26-refactor-chat-context-layers) Montagem de contexto do chat movida para `application`; painel restrito a widget, sessão e thread

#### Added

- Montador de contexto em `application/chat/` que reúne conhecimento, fundamentos, cascata de documentos e fontes adicionais em um `ContextoChat`, com o gate de confirmação delegado a um callback.

#### Changed

- `chat/fundamentos.py`, `chat/documentos.py` e `chat/noticias.py` saem de `presentation` para `application/chat/`.
- `chat/conhecimento.py` passa a ser montado em `application/chat/`, com os textos de interface fornecidos pela apresentação como entrada.
- A extração de texto de documentos sai de `presentation/gui/charts/document_preview.py` para `application/document_preview.py`.
- `chat_panel.py` e `envio.py` consomem o montador de `application` e mantêm apenas widget, sessão, thread/fila, cancelamento, cópia/limpeza e o diálogo de confirmação.
- Testes puros de contexto migram para `tests/test_application`; os testes de `tests/test_presentation` ficam restritos a wiring, estado de widget e thread/queue.

### [refactor-correlation-network-layers](openspec/changes/archive/2026-09-26-refactor-correlation-network-layers) Extração de séries da rede de correlação movida para `application`; painel apenas desenha

#### Changed

- O módulo puro `network_data.py` sai de `presentation` para `application/network/`, como read-model pronto (`DadosRede`, `extrair_series`, mensagens e formatadores).
- `correlation_network_panel.py` consome o read-model de `application` e permanece apenas com o desenho (grafo, colorbar, legenda, estado vazio).
- Testes puros de `tests/test_presentation/test_network_data.py` migram para `tests/test_application`; o painel mantém apenas testes de UI.

### [refactor-documentos-layers](openspec/changes/archive/2026-09-26-refactor-documentos-layers) Entidades de catálogo para `domain`, catálogo e resumo em `application`; painel de documentos apenas desenha

#### Added

- Porta `CatalogoRepository` e caso de uso de consulta do catálogo em `application`, incluindo a montagem/ordenação e a derivação da chave estável.
- Porta `DocumentSummaryStore` em `application`; `JsonDocumentSummaryStore` e `JsonDocumentTextStore` passam a implementá-la.

#### Changed

- Entidades de catálogo (`DocumentoArquivo`, `CategoriaDocumentos`, `MesDocumentos`, `AnoDocumentos`, `CatalogoTicker`) saem de `infrastructure/document_catalog.py` para `domain/documents/`.
- `infrastructure/document_catalog.py` passa a implementar a porta varrendo o cache (apenas I/O), usando as entidades de domínio.
- `DocumentSummaryService` e `GuidanceService` saem de `presentation/gui/charts/` para `application`.
- `document_tree_panel` recebe as dependências por injeção pelo composition root, sem importar `infrastructure`.
- Testes puros de documentos migram para `tests/test_domain`/`tests/test_application`.

#### Removed

- Entradas correspondentes de `tests/architecture/allowlist.txt`.

### [refactor-dominance-panels-layers](openspec/changes/archive/2026-09-26-refactor-dominance-panels-layers) Construção de ranking/timeline e geometria das hastes movidas para `application`; painéis apenas desenham

#### Added

- Testes puros em `tests/test_application` para as funções movidas, sem `DISPLAY`.

#### Changed

- A construção pura do ranking (`build_rows`, `stem_lengths`) sai de `ranking_data.py` para `application/dominance/`, como view-model pronto (`RankingRow`).
- A construção pura da linha do tempo (`build_rows`, `direction_balance`) sai de `timeline_data.py` para `application/dominance/` (`TimelineRow`).
- A geometria/cor das hastes e a localização da linha sob o cursor saem de `dominance_data.py` para `application/dominance/`.
- `dominance_ranking.py` e `dominance_timeline.py` passam a consumir `application` e mantêm apenas o desenho.

### [refactor-flow-panels-layers](openspec/changes/archive/2026-09-26-refactor-flow-panels-layers) Extração de métricas e resumo do fluxo para `application`/`domain`; painel apenas orquestra e desenha

#### Added

- Testes puros em `tests/test_application` e `tests/test_domain` para as funções movidas, sem `DISPLAY`.

#### Changed

- `extract_session_metrics` sai de `financial_flow_helpers.py` para `application/flow/`, como view-model pronto (`SessionFlowMetrics` + `build_session_metrics`).
- `generate_summary` e os trechos `flow_intensity_part`, `close_position_part`, `dominance_part` e `conviction_part` saem do helper para `application/flow/`.
- `pressure_percentages` sai do helper para `domain`.
- `financial_flow_helpers.py` permanece com a formatação, o desenho e o tooltip, consumindo `domain`/`application`.
- `financial_flow_panel.py` passa a consumir os view-models e o resumo de `application`.

### [refactor-fundamental-table-layers](openspec/changes/archive/2026-09-26-refactor-fundamental-table-layers) Linhas, CSV e evolução dos fundamentos como view-models de `application`; a tabela apenas insere e copia

#### Changed

- `montar_linhas`, `montar_csv`, o layout de colunas e os formatadores saem de `fundamental_rows.py` e `fundamental_formatters.py` para `application/fundamental/`.
- A amostragem Fibonacci e a montagem das séries de evolução (`fundamental_evolution_data.py`) saem de `presentation` para `application`.
- `app_csv.py` passa a montar o CSV da tabela a partir do view-model de `application`.
- `controller_fundamental.py` recebe o adaptador de mercado por injeção do composition root.
- Testes puros (linhas, CSV, formatação e evolução) migram para `tests/test_application`.

#### Removed

- Entrada `presentation/gui/controller_fundamental.py -> infrastructure` de `tests/architecture/allowlist.txt`.

### [refactor-noticias-layers](openspec/changes/archive/2026-09-26-refactor-noticias-layers) Classificação e entidades de notícia para `domain`/`application`; painel de notícias apenas desenha

#### Changed

- A classificação de notícias sai de `infrastructure/b3/noticias_tipos.py` para `domain`.
- Entidades de catálogo e a ordenação do lote saem de `infrastructure`/`presentation` para `domain`/`application`.
- `infrastructure/b3/noticias_catalogo.py` permanece como adaptador de leitura, implementando a porta de catálogo e reaproveitando o read-model `montar_catalogo`.
- A montagem do índice compacto do chat e a intercalação por seção passam para `application`.
- `NoticiasPanel` recebe caso de uso e portas por injeção; `NoticiasTreeView` importa entidades de `domain`.
- Testes puros de notícias migram para `tests/test_domain`/`tests/test_application`.

#### Removed

- Três entradas de notícias de `tests/architecture/allowlist.txt`.

### [refactor-price-range-layers](openspec/changes/archive/2026-09-26-refactor-price-range-layers) Classificação de pregão para `domain`; normalização e dimensionamento permanecem em `presentation`

#### Added

- Testes puros em `tests/test_domain` para a classificação movida, sem `DISPLAY`.

#### Changed

- `classify_trend` e `classify_session` (com o auxiliar `median_value`) saem de `price_range_helpers.py` para `domain`, preservando as mesmas categorias.
- `normalize`, `efficiency_color`, `size_mapper`/`_constant_size` e o desenho permanecem em `presentation`.
- `price_range_helpers.py` passa a importar `classify_session` do `domain` em `draw_classification_text`.

### [refactor-quadrant-vwap-layers](openspec/changes/archive/2026-09-26-refactor-quadrant-vwap-layers) Quadrante para `domain`; dados de VWAP e trajetórias/dispersão para `application`; painéis apenas desenham

#### Added

- Testes puros em `tests/test_domain` e `tests/test_application`, sem `DISPLAY`.

#### Changed

- `classify_quadrant` (e a constante dos quadrantes) sai de `quadrant_data.py` para `domain`, passando a operar sobre primitivos (`clv`, `vwap_dist`).
- A preparação das trajetórias e dos pontos de dispersão do quadrante vai para `application`, como view-models prontos (`PontoQuadrante`).
- As contagens/interpretação/resumo (`count_quadrants`, `pick_interpretation`, `generate_summary`) saem para `application`, preservando os mesmos textos.
- A preparação dos dados de VWAP (`to_pct`, `collect_ticker_data`, `estimate_bucket_size`, `compute_violin_shapes`) sai para `application`, como read-model pronto (`DadosVwap`).
- `quadrant_chart.py` e `vwap_hist.py` consomem `domain`/`application` e mantêm apenas o desenho.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.3.1...HEAD
[1.3.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
