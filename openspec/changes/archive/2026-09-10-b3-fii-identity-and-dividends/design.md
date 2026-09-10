## Context

A change `fundamental-metrics-table` entregou a sub-aba "Fundamentos", o motor de métricas, os adapters CVM/Fundamentus e o `FundamentalAnalysisUseCase`, mas nada disso é instanciado no wiring da GUI. O fluxo de exibição atual (`app_actions.py:_do_update`) passa o dicionário cru de trades ao `FundamentalTablePanel`, que cai no caminho sintético (`_linha_sintetica`) e mostra apenas ticker e classificação. Ver `proposal.md` para a motivação.

No lado da aquisição, já existe `B3FundosClient` com resolução de ticker, listagem `GetStructuredReports(type=41)` paginada, download de documento e cache, além do `structured_extractor` que faz o parsing do documento FundosNet. A RFC-008 especifica uma camada B3 mais determinística (heurística `idMain`, retry, rate-limit, metadados e distinção falha/vazio), que se sobrepõe parcialmente a esse cliente.

A GUI é síncrona na thread do Tk: não há uso de `threading`, apenas `after`. O `OperationGuard` garante execução exclusiva, e o `ProgressReporter` já suporta fases ponderadas com throttle.

## Goals / Non-Goals

**Goals:**
- Popular a sub-aba "Fundamentos" com identidade, nome, dividendos e Dividend Yield reais.
- Entregar uma camada de aquisição B3 determinística, com retry/rate-limit/metadados, reutilizando o parsing existente.
- Executar a aquisição em background, mantendo a UI responsiva e reportando progresso.
- Manter a fronteira de camadas (domínio puro, infraestrutura isolada, GUI sem rede).

**Non-Goals:**
- FFO (RFC-010) e NAV/cotas/cotistas (RFC-009) — phases seguintes.
- `GetReportsRelevants`, `GetStructuredReports(type=40)` e SIG negociações — fora do escopo desta phase.
- Paralelismo entre hosts ou entre tickers; a aquisição continua serializada.
- CLI.

## Decisions

### 1. Camada B3 normalizada sobre o cliente existente

Introduzir modelos de domínio (`B3Fund`, `B3ReportReference`, `AcquisitionMetadata`, `AcquisitionResult`) e repositórios (`fund_repository`, `reports_repository`) que encapsulam os endpoints, deixando `B3FundosClient` como transporte HTTP. O `structured_extractor` existente é reutilizado para o documento.

**Alternativas:** reescrever o cliente do zero (descarta cache/testes existentes); manter tudo no cliente (propaga nomes de campos B3 pela aplicação). Escolhido o meio: refatorar incrementalmente.

### 2. Execução em background com fila e token de geração

A análise fundamentalista roda em uma `threading.Thread`; a thread só calcula e publica mensagens numa `queue.Queue`. A thread do Tk consome a fila via `root.after` e então atualiza presenter/status/tabela. Um inteiro de geração é incrementado a cada carga; resultados com geração antiga são descartados. O `OperationGuard` continua cobrindo apenas a carga síncrona, para não travar a UI durante a aquisição.

**Alternativas:** fatiar o trabalho em callbacks `after` (não resolve o bloqueio de rede); `asyncio` (não há infraestrutura async no projeto); `thread` tocando widgets (viola a thread-safety do Tk).

### 3. Dividend Yield desacoplado de NAV/FFO

No `FundamentalAnalysisUseCase`, separar o cálculo do Dividend Yield: `dividendos_12m_por_cota / preço`. Hoje o DY só é calculado no bloco que exige patrimônio, FFO e preço simultaneamente; desacoplar permite preencher a coluna nesta phase. As métricas dependentes de FFO/NAV permanecem delegadas ao `analisar_snapshot`, resultando em `N/A`.

### 4. Resultado de aquisição e persistência

`AcquisitionResult` carrega dados, `warnings` e `errors`; "vazio" e "falha" são estados distintos (RFC-008 §39). As respostas brutas e metadados são preservados sob o `CacheManager` (`~/.cache/flowscope/`), seguindo a convenção do projeto em vez de um diretório `data/` no repositório.

### 5. Reconciliação de contrato com spike antes de alterar

Há divergências entre o código atual e a RFC-008 (chaves `dataInicial`/`dataFinal` vs `dateInitial`/`dateFinal`; `exibirDocumento` vs `visualizarDocumento`; heurística de resolução). Antes de alterar, um teste de contrato com fixture gravado confirma o comportamento real; a heurística de resolução passa a usar `idMain` (mais explícita) sem quebrar o fixture atual.

## Risks / Trade-offs

- **[Risco] Thread-safety do Tk** → Worker nunca toca widgets; comunicação exclusivamente por fila consumida com `after`.
- **[Risco] Contrato B3 instável** → Adapter isolado com `SOURCE_SCHEMA_VERSION`, testes de contrato com fixtures e falha explícita em vez de dado parcialmente incorreto.
- **[Risco] Carga de rede por ticker na thread de trabalho** → Cache por chave (ticker/período) e rate-limit por host; resultados obsoletos descartados por token.
- **[Trade-off] Colunas FFO/NAV em `N/A` nesta phase** → Aceitável no programa faseado; a tabela já trata `N/A`.
- **[Trade-off] Refatorar `B3FundosClient` pode afetar `structured-earnings`** → Preservar assinaturas/ports existentes e cobrir com os testes atuais antes de mudar.

## Migration Plan

1. Introduzir modelos e repositórios B3 sem alterar o caminho existente de proventos.
2. Adicionar retry/rate-limit e metadados de forma retrocompatível.
3. Plugar o adaptador `FiiFundamentalRepository` B3 e o caso de uso no controller em background.
4. Atualizar `_do_update` para o painel de Fundamentos.
5. Rollback: manter o caminho sintético atual como fallback enquanto a flag/estado de resultados fundamentalistas estiver vazio.
