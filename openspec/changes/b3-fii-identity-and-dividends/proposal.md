## Why

A sub-aba "Fundamentos" existe desde a change `fundamental-metrics-table`, mas a tabela nunca é populada em produção: o `FundamentalAnalysisUseCase` e seus adapters não são instanciados no wiring da GUI, então o painel só renderiza linhas sintéticas (ticker + tipo/sub-tipo, demais colunas `N/A`). Além disso, a identidade e os dividendos dependem de `structured-earnings`/CVM sem uma camada B3 própria e determinística. Esta change é a primeira fase do programa que preenche a sub-aba: entrega a aquisição B3 (RFC-008) para identidade e dividendos e liga a análise fundamentalista à GUI em background, deixando `FFO Yield`, `P/FFO`, `FFO Trend` e `P/VP` como `N/A` até as phases de CVM (RFC-009) e do motor de FFO (RFC-010).

## What Changes

- Nova camada de aquisição B3 (`fundsListedProxy`) conforme RFC-008, escopo identidade + dividendos: resolução de ticker para `idFNET` (heurística `idMain`), listagem paginada de `GetStructuredReports(type=41)`, download e parsing de documento FundosNet, retry para erros transitórios, rate-limit por host, cache e preservação de metadados de aquisição.
- Modelos de domínio B3 normalizados (`B3Fund`, `B3ReportReference`, `AcquisitionMetadata`, `AcquisitionResult`) que distinguem lista vazia de falha de aquisição.
- Adaptador `FiiFundamentalRepository` apoiado na camada B3 para nome e proventos; `Dividend Yield` calculado como dividendo por cota / preço de fechamento, desacoplado de NAV e FFO.
- Wiring da GUI: o `FundamentalAnalysisUseCase` passa a ser instanciado e executado após cada carga de dados, em **thread de background** com reporte de progresso; os resultados são publicados na thread do Tk via fila e consumidos pela sub-aba "Fundamentos". Um token de geração descarta resultados obsoletos quando uma nova carga começa.
- Sem mudanças de contrato nas fontes CVM/Fundamentus nesta fase; o `FundamentusProvider` permanece como fonte primária, e a camada B3 desta change atua como fallback de identidade e dividendos.

## Capabilities

### New Capabilities

- `b3-fii-extraction`: Aquisição determinística de identidade e documentos de FII na B3 (`GetListClassFund`, `GetStructuredReports(type=41)`, download FundosNet), com paginação, retry, rate-limit, cache, metadados e tratamento explícito de falha vs. lista vazia.

### Modified Capabilities

- `gui-interface`: A sub-aba "Fundamentos" passa a exibir a análise fundamentalista real dos tickers carregados, obtida em background com progresso e atualizada ao trocar de sub-aba, em vez de linhas sintéticas.

## Impact

- **Código afetado**: `infrastructure/b3/` (novo encoder, repositórios de fundo/relatórios, retry/rate-limit), `domain/b3/` (modelos normalizados), `infrastructure/fii/` (adaptador `FiiFundamentalRepository` B3), `application/fundamental_analysis.py` (DY desacoplado), `presentation/gui/` (`app.py`, `controller.py`, `presenter.py`, `app_actions.py`, `charts/fundamental_table.py`).
- **APIs**: `sistemaswebb3-listados.b3.com.br` (`GetListClassFund`, `GetStructuredReports`) e `fnet.bmfbovespa.com.br` (documento). Nenhuma credencial.
- **Cache**: novas chaves/arquivos em `~/.cache/flowscope/` para resolução de fundo, listagens e documentos brutos.
- **Escopo faseado**: `FFO Yield`, `P/FFO`, `FFO Trend` (RFC-010) e `P/VP` (RFC-009) permanecem `N/A` nesta change.
