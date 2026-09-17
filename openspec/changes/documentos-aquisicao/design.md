## Context

Ver `proposal.md - Why`. As peças de aquisição já existem e estão testadas: `B3FundosClient` resolve ticker→`idFNET` e ticker→`codeCVM`, lista documentos relevantes (`GetReportsRelevants`), informes mensais (`GetStructuredReports(type=40)`) e material facts (`GetMaterialFacts`); `DocumentosRelevantesProvider` e `InformeMensalArquivoProvider` baixam e gravam nos caches `documentos-relevantes/` e `informe-mensal/`; `DocumentCatalog` lê essas raízes. O que falta é a orquestração que escolhe a fonte por tipo e o acionamento pela sub-aba "Documentos".

O download de PDF da CVM via `ExibirPDF` já é feito por `BdrClient.baixar_pdf` (POST com `numeroProtocolo` e decodificação base64 validando `%PDF`), reutilizável para os material facts, cuja URL de busca (`urlSearch`) carrega o `ID` do protocolo.

## Goals / Non-Goals

**Goals:**
- Orquestrador único de aquisição sob demanda por ticker, escolhendo a fonte pelo tipo.
- Popular `documentos-relevantes/` (ações e FIIs) e `informe-mensal/` (FIIs).
- Acionar a aquisição ao abrir/atualizar a sub-aba "Documentos", fora da thread da interface.

**Non-Goals:**
- OCR ou extração de texto dos PDFs (pertence a `visualizacao-documentos`/`llm-chat`).
- Alterar as raízes/layout de cache ou o catálogo de leitura.
- Baixar documentos de toda a watchlist durante a análise fundamentalista.
- Cobrir categorias de material facts sem slug correspondente no catálogo (avisos ao acionista/debenturista).

## Decisions

### 1. Orquestrador em `infrastructure/b3/` com detecção de tipo

**Decisão**: novo `AquisicaoDocumentos` em `infrastructure/b3/documentos_aquisicao.py`, que recebe o cliente B3 e os dois provedores e expõe `adquirir(ticker, reference_date)`. Ele tenta `resolver_ticker` (FII) e, se falhar, `resolver_code_cvm` (ação/BDR). Sem identidade resolvida, retorna sem download.

**Alternativas**: (a) disparar tudo pela GUI — misturaria rede com a view; (b) integrar à análise fundamentalista — baixaria documentos de toda a watchlist, onerando a carga. O orquestrador isolado é testável e mantém a GUI fina.

### 2. Fonte por tipo

**Decisão**: FIIs usam `DocumentosRelevantesProvider.sincronizar` (4 categorias) e o informe mensal mais recente via `listar_documentos(..., 40)` + `InformeMensalArquivoProvider.persistir`; ações/BDRs usam `listar_fatos_relevantes` das categorias fatos relevantes e assembleias, baixando cada PDF da CVM e gravando na árvore `documentos-relevantes/` com o slug da categoria (`fato-relevante`, `assembleia`).

**Racional**: reaproveita os provedores e o parser existentes, sem novo contrato de API.

### 3. Download CVM compartilhado

**Decisão**: extrair o download `ExibirPDF` para um helper reutilizável em `infrastructure/cvm/` (POST com `numeroProtocolo`, decodificação base64 e validação `%PDF`), usado pelos material facts. `BdrClient` pode passar a delegar a esse helper.

**Alternativas**: duplicar a lógica em um novo cliente; reusar `BdrClient` diretamente (acoplaria material facts ao domínio BDR). O helper compartilhado evita duplicação e mantém a semântica de cada fonte.

### 4. Acionamento pela sub-aba em worker, via hook do painel

**Decisão**: o `DocumentTreePanel` ganha um `acquire_callback` opcional. Quando definido, `update`/refresh o invoca com o ticker apresentado em vez de apenas varrer; a GUI fornece um método que executa `AquisicaoDocumentos.adquirir` em thread de trabalho e, ao concluir, remonta a árvore na thread do Tk (fila consumida por `after`, como no `FundamentalJob`). Sem o hook, o painel mantém o comportamento atual (só varredura), preservando os testes.

**Alternativas**: fazer o painel baixar diretamente (acopla a view à rede); acionar sem worker (bloqueia a interface). O hook mantém o painel somente-leitura e a rede fora da thread da interface.

### 5. Período de referência

**Decisão**: documentos relevantes e material facts usam janela de 12 meses até a data de referência; o informe mensal usa 24 meses e persiste o mais recente aplicável.

**Racional**: janela suficiente para os documentos usuais, alinhada à janela de proventos, sem varreduras longas.

## Risks / Trade-offs

- **[Risco] Latência ao abrir a sub-aba** → Aquisição em worker com estado de carregamento; a árvore só é remontada ao final.
- **[Risco] Contrato da CVM (`ExibirPDF`) mudar** → Reutiliza o mecanismo já testado e valida `%PDF`; falha isolada é tolerada.
- **[Risco] Muitos documentos em FIIs** → Download sequencial tolerante; cache hit evita rebaixar.
- **[Trade-off] Material facts de BDR** → BDRs podem não ter material facts; o cache BDR já cobre avisos, então a ausência não é erro.
- **[Trade-off] Duplicação de bytes** → O cache de arquivos serve à inspeção; a extração de texto é de quem consome.

## Migration Plan

1. Extrair o helper de download CVM e adicionar o orquestrador.
2. Adicionar o hook `acquire_callback` ao painel e o acionamento em worker na GUI.
3. Testes de orquestração, download e acionamento.
4. Rollback: remover o hook e o orquestrador restaura o comportamento somente-leitura; os caches permanecem válidos.
