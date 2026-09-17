# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional
- [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões
- [llm-chat](openspec/changes/llm-chat) Assistente RAG integrado à GUI com VectorStore SQLite, embeddings e chat LLM via liteLLM
- [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado com gauge de concentração, card informativo e timeline AFT

## [1.0.0] — 2026-09-17

### [corrigir-cursor-fundamentos](openspec/changes/archive/2026-09-17-corrigir-cursor-fundamentos) Corrige o cursor de espera e os controles que ficavam presos quando uma análise fundamentalista em background era substituída por outra antes de concluir

#### Changed

- Compensar o ciclo de vida do job fundamentalista substituído: todo `on_fundamental_started` deve ter exatamente um `on_fundamental_finished` correspondente, mesmo quando um novo job assume o lugar do anterior.
- Impedir que a análise fundamentalista manual (botão "Atualizar fundamentos") deixe os controles habilitados: os botões passam a ser desabilitados já no início da análise, e um novo disparo é bloqueado enquanto um job estiver ativo.
- Cobrir a regressão com testes de controller/presenter e um teste de GUI (quando houver display) verificando que o cursor do `Treeview` da tabela de Fundamentos volta ao valor original.

### [documentos-aquisicao](openspec/changes/archive/2026-09-17-documentos-aquisicao) Orquestração da aquisição sob demanda dos documentos de um ticker, escolhendo a fonte pelo tipo (ações/BDR via material facts; FII via documentos relevantes e informe mensal) e gravando nos caches existentes

#### Added

- Nova orquestração de aquisição sob demanda dos documentos de um ticker, escolhendo a fonte pelo tipo: ações/BDRs via material facts (`GetMaterialFacts`) com download do PDF no visualizador da CVM e validação `%PDF`; FIIs via documentos relevantes (`GetReportsRelevants`) e informe mensal estruturado (HTML).
- Gravação nos caches existentes: `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf` e `<cache>/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`.

#### Changed

- Ao abrir a sub-aba "Documentos", exibir somente os documentos constantes no catálogo de leitura do cache do ticker apresentado (sincronizado com "Evolução dos Fundamentos"), sem acionar download.
- Acionar a aquisição apenas sob demanda pelo botão "Atualizar": buscar e baixar uma janela de 12 meses de documentos do ticker até a data de referência, reutilizando sem novo download os que já estiverem em cache, em worker, com remontagem da árvore ao final.
- Durante a execução do "Atualizar", desabilitar os botões da aplicação, ativar o cursor de espera (hourglass) e atualizar a barra de status e a barra de progresso com o andamento do processo; restaurar os controles ao término.
- Integrar os botões "Atualizar" e "Abrir documento" da sub-aba ao mesmo mecanismo de bloqueio global dos demais botões, ficando desabilitados também durante as cargas de dados e demais operações da aplicação.
- Renomear o botão de abertura para "Abrir documento", habilitando-o somente quando um documento estiver selecionado.
- Reutilizar `B3FundosClient` (resolução de ticker/codeCVM, `GetReportsRelevants`, `GetMaterialFacts`), os provedores `DocumentosRelevantesProvider` e `InformeMensalArquivoProvider`, o catálogo `DocumentCatalog` e o mecanismo CVM `ExibirPDF`.
- Limitar o timeout das requisições de documento do FundosNet (PDF e HTML) para que uma conexão que aceita e não responde falhe rápido e o retry reabra a conexão, em vez de travar a aquisição por dezenas de segundos por tentativa.
- Sem nova fonte para tickers sem documentos: falha de rede ou ausência de dados resulta em cache vazio, sem erro.

#### Fixed

- Corrigir a resolução `ticker → codeCVM` para consultar `GetInitialCompanies` (endpoint real do cadastro de empresas da B3) filtrando por `company` e casando o registro cujo `issuingCompany` é a raiz do ticker; a chave de cache passa a ser versionada para descartar `None` envenenado por execuções anteriores.
- Corrigir o payload do `GetMaterialFacts` para os nomes de campo aceitos pela API (`language`, `dateInitial`, `dateFinal`, `category`), sem os quais a listagem retorna vazia.

### [documentos-relevantes](openspec/changes/archive/2026-09-17-documentos-relevantes) Listagem de documentos não estruturados da B3 (Assembleias, Comunicados, Fatos Relevantes e Relatórios) via `GetReportsRelevants`, com download validado e cache em árvore por ticker/ano/mês/categoria

#### Added

- Novo método `listar_documentos_relevantes(id_fnet, data_inicio, data_fim, category)` no `B3FundosClient`, usando `GetReportsRelevants` com iteração pelas 4 categorias (1=Fatos Relevantes, 2=Assembleias, 3=Comunicados, 7=Relatórios), paginação e cache de listagem (TTL 1 dia).
- Download dos PDFs via `exibirDocumento?id=` com validação de assinatura `%PDF`.
- Cache binário em `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`, sem expiração.
- Nova entidade `DocumentoRelevante` com metadados (ticker, id, categoria, descrição, datas, url).
- Mapeamento de categorias da API para nomes e slugs de pasta.

#### Changed

- Ticker-agnóstico: retorna lista vazia quando a resolução falha ou o ticker não tem documentos.

#### Removed

- Remover do escopo a preparação para o `llm-chat` (`DocumentoRelevante.to_text()`, `RelevantesSource`/`DocumentSource`, extração de texto para embedding), transferida para a change `llm-chat`.

### [fix-fundamentos-fiagro-bdr](openspec/changes/archive/2026-09-17-fix-fundamentos-fiagro-bdr) Preenche os campos de Fundamentos de FIAGROs e BDRs, resolvendo identidade B3 multi-tipo, proventos `fii_proventos.php` e dividendos de BDR via Plantão de Notícias

#### Added

- Nova fonte de dividendos para BDRs via **Plantão de Notícias da B3**: lista `Aviso aos Acionistas` mês a mês, baixa o PDF do documento na CVM (POST `ExibirPDF`, base64), cacheia por ticker/ano/mês, extrai último dividendo, dividendo anterior, data-com, ISIN, depositário e empresa, e calcula P/L e Dividend Yield com anualização trimestral (×4).

#### Changed

- Resolução de fundo na B3 passa a iterar os tipos de fundo `FII`, `FIAGRO`, `FIP` e `FIDC`, desbloqueando a cadeia B3/CVM para FIAGROs (nome, CNPJ, administrador, gestor, patrimônio, cotas, cotistas, indexadores e proventos B3).
- Histórico de proventos do Fundamentus passa a ler `fii_proventos.php` para FIIs/FIAGROs (tabela `Última Data Com`/`Tipo`/`Data de Pagamento`/`Valor`), preenchendo data-com, dividendo anterior, tendência e o P/L derivado.
- Classificação determinística de FIAGRO passa a reconhecê-los como `FII` com sub-tipo `FIAGRO`, eliminando `Desconhecido` no fallback e mantendo-os fora da elegibilidade FFO.
- A sub-aba Fundamentos passa a exibir, para BDRs, o sub-tipo `BDR`, o nível do programa (ex.: `Nível I Não Patrocinado`) e a observação fiscal do aviso (dedução de IR/IOF/tarifa) em `Informações adicionais`, e, quando não houver identidade fiscal, o depositário (ex.: `Banco B3 S.A.`), a empresa (ex.: `Exxon Mobil Corporation`) e o ISIN em `Dados fiscais`.

### [informe-mensal](openspec/changes/archive/2026-09-17-informe-mensal) Persistência em arquivo do HTML do Informe Mensal Estruturado (type=40) da B3, organizada por ticker/ano/mês, para leitura pelo catálogo de documentos

#### Added

- Persistir o HTML do informe mensal em `~/.cache/flowscope/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`, com ano/mês derivados da data de referência do documento.
- Expor a leitura dessa árvore (existência, caminho e conteúdo) para o catálogo de documentos.

#### Changed

- Reutilizar a listagem type=40 e o download HTML já existentes no `B3FundosClient`, **sem alterar** as entidades de leitura (`B3InformeMensal`, parser e repositório).

#### Removed

- Remover do escopo: domínio rico (`Carteira`, `Resultados`, `Indicadores`, `InformeMensal`), value object `Percentual`, `InformeMensalRepository`/`ExtrairInformeMensalUseCase`, parser multi-tabela, CLI `--informe-mensal` e `to_text()`/preparação de VectorStore (transferida para `llm-chat`).

### [reorganizacao-abas-ticker](openspec/changes/archive/2026-09-17-reorganizacao-abas-ticker) Reorganiza as sub-abas da Análise do Ticker e torna a linha selecionada na tabela de Fundamentos a fonte única do ticker analisado

#### Changed

- Mover a sub-aba "Fundamentos" para a **primeira** posição na aba "Análise Geral".
- Reordenar as sub-abas da "Análise do Ticker": "Evolução dos Fundamentos" em primeiro e "Documentos" em último.
- Deixar **invisíveis** as três sub-abas sem painel implementado — "Participação Institucional", "Eficiência do Movimento" e "Resumo Geral" — que têm changes dedicadas (`participation-negociacoes`, `eficiencia-do-movimento`, `diagnosis-panel`).
- Tornar a linha selecionada na tabela da sub-aba "Fundamentos" a **fonte única** do ticker analisado em todas as sub-abas da "Análise do Ticker" (Dominância, Amplitude, Fluxo, Evolução dos Fundamentos e Documentos) e na cópia CSV dessa aba.
- Desvincular o ticker analisado da seleção na TickerList: a lista continua definindo **quais linhas** aparecem na tabela de Fundamentos e governa a "Análise Geral", mas não define mais o ticker das sub-abas por ticker.
- Ao carregar os fundamentos, **auto-selecionar a primeira linha** da tabela quando houver dados; sem dados, permanecer sem seleção e sem ticker analisado.
- Manter o duplo-clique na linha de Fundamentos como atalho: seleciona o ticker e navega para "Análise do Ticker" → "Evolução dos Fundamentos".
- **BREAKING** (comportamento observável): a seleção na TickerList deixa de atualizar as sub-abas da "Análise do Ticker"; o requisito correspondente é removido e substituído.

### [visualizacao-documentos](openspec/changes/archive/2026-09-17-visualizacao-documentos) Adiciona a sub-aba Documentos na Análise do Ticker com catálogo hierárquico de caches, pré-visualização textual e abertura no aplicativo padrão

#### Added

- Catálogo de documentos que varre as raízes de cache (`bdr/`, `informe-mensal/`, `documentos-relevantes/`) e normaliza os arquivos em uma hierarquia `ticker → ano → mês → categoria → arquivos`, com tipo (`pdf`/`html`) e caminho.
- Nova sub-aba **"Documentos"** na "Análise do Ticker" com uma árvore hierárquica, o nome do ticker no topo e as categorias derivadas da fonte/ pasta.
- Pré-visualização textual em caixa de texto somente-leitura ao selecionar um arquivo, com extração sob demanda (HTML→texto; PDF→`pypdf`) executada fora da thread da interface.
- Abertura do arquivo no aplicativo padrão do sistema operacional (PDF→leitor de PDF; HTML→navegador) por duplo-clique, tecla Enter ou botão "Abrir".
- Ordenação (ano/mês decrescentes, categorias alfabéticas, arquivos do mais recente ao mais antigo), estado vazio e atualização manual.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.0.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
