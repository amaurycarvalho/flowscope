## Context

Ver `proposal.md - Why`. As peças de aquisição já existem e estão testadas: `B3FundosClient` resolve ticker→`idFNET` e ticker→`codeCVM`, lista documentos relevantes (`GetReportsRelevants`), informes mensais (`GetStructuredReports(type=40)`) e material facts (`GetMaterialFacts`); `DocumentosRelevantesProvider` e `InformeMensalArquivoProvider` baixam e gravam nos caches `documentos-relevantes/` e `informe-mensal/`; `DocumentCatalog` lê essas raízes. O que falta é a orquestração que escolhe a fonte por tipo e o acionamento pela sub-aba "Documentos".

O download de PDF da CVM via `ExibirPDF` já é feito por `BdrClient.baixar_pdf` (POST com `numeroProtocolo` e decodificação base64 validando `%PDF`), reutilizável para os material facts, cuja URL de busca (`urlSearch`) carrega o `ID` do protocolo.

## Goals / Non-Goals

**Goals:**
- Orquestrador único de aquisição sob demanda por ticker, escolhendo a fonte pelo tipo.
- Popular `documentos-relevantes/` (ações e FIIs) e `informe-mensal/` (FIIs).
- Acionar a aquisição somente pelo botão "Atualizar", fora da thread da interface; abrir a sub-aba apenas lê o catálogo de cache.

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

### 4. Aquisição somente pelo botão "Atualizar", via hook do painel

**Decisão**: o `DocumentTreePanel` ganha um `acquire_callback` opcional, invocado **apenas** pelo botão "Atualizar". Ao abrir a sub-aba, `update` somente lê o catálogo de leitura do cache e remonta a árvore, sem download. Quando o hook está definido, a GUI executa `AquisicaoDocumentos.adquirir` em thread de trabalho e, ao concluir, remonta a árvore na thread do Tk (fila consumida por `after`, como no `FundamentalJob`). Sem o hook, "Atualizar" apenas revarre o catálogo, preservando os testes.

**Alternativas**: adquirir ao abrir (bloqueia a abertura e baixa sem intenção do usuário); fazer o painel baixar diretamente (acopla a view à rede); acionar sem worker (bloqueia a interface). O hook mantém o painel somente-leitura e a rede fora da thread da interface.

Durante a execução, a GUI usa o presenter (`on_operation_started`/`on_operation_finished` e `on_progress`) para desabilitar os botões da aplicação, ativar o cursor de espera (hourglass) e atualizar a barra de status e a barra de progresso. O `DocumentosJob` publica mensagens de progresso na fila, consumidas na thread do Tk, e o `AquisicaoDocumentos` reporta o avanço por documento via callback opcional. Os botões "Atualizar" e "Abrir documento" do painel são expostos por `all_buttons()` e integrados ao bloqueio global (`_disable_all_buttons`/`_restore_all_buttons`), ficando desabilitados durante qualquer operação, inclusive as cargas de dados. Ao restaurar, o painel reavalia o "Abrir documento" pela seleção corrente (`refresh_open_button`), evitando que ele fique habilitado sem seleção após a remontagem da árvore. Um guard de reentrância (`_documentos_job`) evita disparar o job duas vezes.

### 5. Período de referência

**Decisão**: documentos relevantes, material facts e informe mensal usam a mesma janela de 12 meses até a data de referência; o informe persiste o mais recente aplicável dentro da janela.

**Racional**: janela única e suficiente para os documentos usuais, alinhada à janela de proventos, sem varreduras longas. Arquivos já em cache são reutilizados sem novo download.

### 6. Botão "Abrir documento" habilitado conforme a seleção

**Decisão**: o botão de abertura é rotulado "Abrir documento" e começa desabilitado; habilita quando um nó de arquivo está selecionado e volta a desabilitar quando a seleção é de pasta ou inexistente. A abertura por duplo-clique e Enter permanece.

### 7. Contratos reais da B3 na resolução e no material facts

**Decisão**: corrigir os contratos usados pela aquisição de ações para os efetivamente expostos pela B3:

- `resolver_code_cvm` consulta `GetInitialCompanies` (e não `GetListedCompany`, que responde 404) filtrando por `company=<raiz do ticker>` e casa o registro cujo `issuingCompany` é a raiz do ticker (ex.: PETR3 → PETR → codeCVM 9512). O filtro textual pode trazer homônimos, então a correspondência exata de `issuingCompany` é obrigatória; a resposta é paginada com `pageSize=120`.
- O token Base64 do `GetMaterialFacts` usa `language`, `codeCVM`, `year`, `dateInitial`, `dateFinal`, `category`, `pageNumber` e `pageSize`; os nomes `linguagem`/`dataInicial`/`dataFinal`/`categoria` são ignorados pela API, que devolve listagem vazia.

A chave de cache da resolução passa a ser versionada (`_chave_cache`), pois execuções anteriores gravaram `None` para 30 dias e o valor envenenado impediria a correção de surtir efeito.

**Racional**: validado contra a API real — AGRO3, BBAS3, BRAP3, PETR3 e VALE3 passaram a retornar `codeCVM` e a popular `documentos-relevantes/` com PDFs.

**Alternativas**: manter `GetListedCompany` (não existe); buscar todos os emissores e indexar localmente (30 requisições e cache maior, sem ganho); usar o CSV de empresas listadas como caminho primário (a URL atual devolve HTML, não CSV).

## Risks / Trade-offs

- **[Risco] Latência ao acionar "Atualizar"** → Aquisição em worker com estado de carregamento; a árvore só é remontada ao final. Abrir a sub-aba não baixa (somente cache).
- **[Risco] Contrato da CVM (`ExibirPDF`) mudar** → Reutiliza o mecanismo já testado e valida `%PDF`; falha isolada é tolerada.
- **[Risco] Muitos documentos em FIIs** → Download sequencial tolerante; cache hit evita rebaixar.
- **[Trade-off] Material facts de BDR** → BDRs podem não ter material facts; o cache BDR já cobre avisos, então a ausência não é erro.
- **[Trade-off] Duplicação de bytes** → O cache de arquivos serve à inspeção; a extração de texto é de quem consome.

## Migration Plan

1. Extrair o helper de download CVM e adicionar o orquestrador.
2. Adicionar o hook `acquire_callback` ao painel e o acionamento em worker na GUI.
3. Testes de orquestração, download e acionamento.
4. Rollback: remover o hook e o orquestrador restaura o comportamento somente-leitura; os caches permanecem válidos.
