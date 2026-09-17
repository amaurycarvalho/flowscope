## Why

A sub-aba "Documentos" só exibe arquivos que já existam nas raízes de cache. Hoje apenas os avisos de BDR são adquiridos pelo app; os provedores de `documentos-relevantes` (FIIs, `GetReportsRelevants`) e de `informe-mensal` nunca são chamados, e ações como PETR3 não têm nenhuma fonte de aquisição. Como resultado, a sub-aba aparece vazia para a maior parte da watchlist.

## What Changes

- Nova orquestração de aquisição sob demanda dos documentos de um ticker, escolhendo a fonte pelo tipo:
  - **Ações/BDRs**: material facts (`GetMaterialFacts`) — fatos relevantes e assembleias — com download do PDF no visualizador da CVM e validação `%PDF`.
  - **FIIs**: documentos relevantes (`GetReportsRelevants`) e o informe mensal estruturado (HTML).
- Gravação nos caches existentes: `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf` e `<cache>/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`.
- Ao abrir a sub-aba "Documentos", exibir somente os documentos constantes no catálogo de leitura do cache do ticker apresentado (sincronizado com "Evolução dos Fundamentos"), sem acionar download.
- Acionar a aquisição apenas sob demanda pelo botão "Atualizar": buscar e baixar uma janela de 12 meses de documentos do ticker até a data de referência, reutilizando sem novo download os que já estiverem em cache, em worker, com remontagem da árvore ao final.
- Durante a execução do "Atualizar", desabilitar os botões da aplicação, ativar o cursor de espera (hourglass) e atualizar a barra de status e a barra de progresso com o andamento do processo; restaurar os controles ao término.
- Integrar os botões "Atualizar" e "Abrir documento" da sub-aba ao mesmo mecanismo de bloqueio global dos demais botões, ficando desabilitados também durante as cargas de dados e demais operações da aplicação.
- Renomear o botão de abertura para "Abrir documento", habilitando-o somente quando um documento estiver selecionado.
- Reutiliza `B3FundosClient` (resolução de ticker/codeCVM, `GetReportsRelevants`, `GetMaterialFacts`), os provedores `DocumentosRelevantesProvider` e `InformeMensalArquivoProvider`, o catálogo `DocumentCatalog` e o mecanismo CVM `ExibirPDF`.
- Sem nova fonte para tickers sem documentos: falha de rede ou ausência de dados resulta em cache vazio, sem erro.

## Capabilities

### New Capabilities

- `documentos-aquisicao`: orquestração da aquisição sob demanda dos documentos de um ticker — seleção de fonte por tipo (ação/BDR via material facts; FII via documentos relevantes e informe mensal), resolução de identidade, download com validação e gravação nos caches existentes, tolerante a falhas.
- `documentos-aquisicao-painel`: exibição do catálogo de leitura ao abrir a sub-aba "Documentos" e acionamento sob demanda da aquisição pelo botão "Atualizar" (janela de 12 meses), com estado de carregamento, execução fora da thread da interface, remontagem da árvore e botão "Abrir documento" habilitado conforme a seleção.

### Modified Capabilities

_Nenhuma. A sub-aba e o catálogo introduzidos por `visualizacao-documentos` não têm requisitos alterados; esta change adiciona a aquisição que os popula._

## Impact

- **Código**: `infrastructure/b3/` (orquestrador de aquisição e download CVM de material facts) e `presentation/gui/` (acionamento no painel de documentos).
- **Cache**: passa a popular `documentos-relevantes/` (ações e FIIs) e `informe-mensal/` (FIIs); a árvore `bdr/` permanece.
- **APIs**: `GetReportsRelevants` e `GetStructuredReports(type=40)` (FundosNet), `GetMaterialFacts` (B3) e `ExibirPDF` (CVM).
- **Dependências**: `pypdf` já presente; sem novas dependências.
- **Rede**: aquisição sob demanda por ticker, disparada pela interface; não onera a carga geral de fundamentos.
