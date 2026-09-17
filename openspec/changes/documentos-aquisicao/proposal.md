## Why

A sub-aba "Documentos" só exibe arquivos que já existam nas raízes de cache. Hoje apenas os avisos de BDR são adquiridos pelo app; os provedores de `documentos-relevantes` (FIIs, `GetReportsRelevants`) e de `informe-mensal` nunca são chamados, e ações como PETR3 não têm nenhuma fonte de aquisição. Como resultado, a sub-aba aparece vazia para a maior parte da watchlist.

## What Changes

- Nova orquestração de aquisição sob demanda dos documentos de um ticker, escolhendo a fonte pelo tipo:
  - **Ações/BDRs**: material facts (`GetMaterialFacts`) — fatos relevantes e assembleias — com download do PDF no visualizador da CVM e validação `%PDF`.
  - **FIIs**: documentos relevantes (`GetReportsRelevants`) e o informe mensal estruturado (HTML).
- Gravação nos caches existentes: `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf` e `<cache>/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`.
- Acionamento ao abrir/atualizar a sub-aba "Documentos" para o ticker apresentado (sincronizado com "Evolução dos Fundamentos"), em worker, com estado de carregamento e remontagem da árvore ao final.
- Reutiliza `B3FundosClient` (resolução de ticker/codeCVM, `GetReportsRelevants`, `GetMaterialFacts`), os provedores `DocumentosRelevantesProvider` e `InformeMensalArquivoProvider`, o catálogo `DocumentCatalog` e o mecanismo CVM `ExibirPDF`.
- Sem nova fonte para tickers sem documentos: falha de rede ou ausência de dados resulta em cache vazio, sem erro.

## Capabilities

### New Capabilities

- `documentos-aquisicao`: orquestração da aquisição sob demanda dos documentos de um ticker — seleção de fonte por tipo (ação/BDR via material facts; FII via documentos relevantes e informe mensal), resolução de identidade, download com validação e gravação nos caches existentes, tolerante a falhas.
- `documentos-aquisicao-painel`: acionamento da aquisição pela sub-aba "Documentos" ao abrir/atualizar, com estado de carregamento, execução fora da thread da interface e remontagem da árvore.

### Modified Capabilities

_Nenhuma. A sub-aba e o catálogo introduzidos por `visualizacao-documentos` não têm requisitos alterados; esta change adiciona a aquisição que os popula._

## Impact

- **Código**: `infrastructure/b3/` (orquestrador de aquisição e download CVM de material facts) e `presentation/gui/` (acionamento no painel de documentos).
- **Cache**: passa a popular `documentos-relevantes/` (ações e FIIs) e `informe-mensal/` (FIIs); a árvore `bdr/` permanece.
- **APIs**: `GetReportsRelevants` e `GetStructuredReports(type=40)` (FundosNet), `GetMaterialFacts` (B3) e `ExibirPDF` (CVM).
- **Dependências**: `pypdf` já presente; sem novas dependências.
- **Rede**: aquisição sob demanda por ticker, disparada pela interface; não onera a carga geral de fundamentos.
