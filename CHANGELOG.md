# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional
- [documentos-relevantes](openspec/changes/documentos-relevantes) Extração de documentos relevantes (PDFs) da B3 via GetReportsRelevants com cache e integração com VectorStore
- [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões
- [informe-mensal](openspec/changes/informe-mensal) Extração de Informes Mensais Estruturados (type=40) da B3 com entidades próprias e parsing multi-tabela
- [llm-chat](openspec/changes/llm-chat) Assistente RAG integrado à GUI com VectorStore SQLite, embeddings e chat LLM via liteLLM
- [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado com gauge de concentração, card informativo e timeline AFT

## [0.8.0] — 2026-09-09

### [structured-earnings](openspec/changes/archive/2026-09-09-structured-earnings) Extração de rendimentos e amortizações de FIIs via API B3 com entidades de domínio, cache e CLI

### [regulacao-mercado](openspec/changes/archive/2026-09-09-regulacao-mercado) Dados regulatórios e de mercado da B3 (fatos relevantes, notícias, censuras, condições excepcionais) integrados ao llm-chat

### [b3-cache-documentos-identidade](openspec/changes/archive/2026-09-10-b3-cache-documentos-identidade) Cacheia HTML de documentos FundosNet e respostas de identidade da B3, com chaves versionadas por parser

#### Added

- Cobrir com testes a ausência de requisição HTTP na segunda chamada (documento e identidade) e a invalidação por versão.

#### Changed

- Cachear o HTML do documento FundosNet em `B3FundosClient.buscar_html_documento`, indexado pelo `id` do documento e aplicável tanto a proventos (`type=41`) quanto ao informe mensal (`type=40`), evitando o rebaixamento a cada análise.
- Cachear `GetListClassFund` em `B3FundosClient.listar_candidatos`, indexado pelo `id` primário do fundo, para que `B3FundRepository.find_by_ticker` não reconsulte a B3 a cada execução.
- Consistência: centralizar TTLs e nomes de chave em constantes do cliente e versionar as chaves de cache com a versão do parser/aquisição, de modo que uma mudança de parser invalide os registros anteriores.

### [b3-fii-identity-and-dividends](openspec/changes/archive/2026-09-10-b3-fii-identity-and-dividends) Primeira fase do programa Fundamentos: aquisição B3 de identidade e dividendos e wiring da análise em background na GUI

#### Added

- Nova camada de aquisição B3 (`fundsListedProxy`) conforme RFC-008, escopo identidade + dividendos: resolução de ticker para `idFNET` (heurística `idMain`), listagem paginada de `GetStructuredReports(type=41)`, download e parsing de documento FundosNet, retry para erros transitórios, rate-limit por host, cache e preservação de metadados de aquisição.
- Modelos de domínio B3 normalizados (`B3Fund`, `B3ReportReference`, `AcquisitionMetadata`, `AcquisitionResult`) que distinguem lista vazia de falha de aquisição.
- Adaptador `FiiFundamentalRepository` apoiado na camada B3 para nome e proventos; `Dividend Yield` calculado como dividendo por cota / preço de fechamento, desacoplado de NAV e FFO.

#### Changed

- Wiring da GUI: o `FundamentalAnalysisUseCase` passa a ser instanciado e executado após cada carga de dados, em thread de background com reporte de progresso; os resultados são publicados na thread do Tk via fila e consumidos pela sub-aba "Fundamentos". Um token de geração descarta resultados obsoletos quando uma nova carga começa.
- Sem mudanças de contrato nas fontes CVM/Fundamentus nesta fase; o `FundamentusProvider` permanece como fonte primária, e a camada B3 desta change atua como fallback de identidade e dividendos.

### [conditional-cache-fundamentus-cvm](openspec/changes/archive/2026-09-10-conditional-cache-fundamentus-cvm) Abstração de cache condicional com revalidação por data/HTTP, aplicada ao Fundamentus e à CVM (corrige frescura do ZIP anual)

#### Added

- Introduzir uma abstração genérica de cache condicional que separa _frescor_ (quando o valor é considerado válido), _revalidação_ (checagem barata contra a fonte remota) e _retenção_ (quando evictar do disco), com protocolo de `Validator` plugável.
- Adicionar validadores concretos: `DateValidator` (campo `Data últ cot`) e `HttpValidator` (`ETag`/`Last-Modified`, `304`), com chaves versionadas por `parser_version`/`SOURCE_SCHEMA_VERSION`, escrita atômica e coalescência de checagens de rede.

#### Changed

- Aplicar ao provider do Fundamentus: revalidar o snapshot por `Data últ cot` (primário) e validadores HTTP (secundário), cachear HTML cru com versão do parser e devolver o resultado do cache (hit/revalidado/atualizado) para a camada de apresentação.
- Propagar o resultado do cache até a statusbar para exibir "Dados atualizados" quando houver atualização real, sem acoplar infraestrutura à GUI.

#### Fixed

- Corrigir o bug da CVM: revalidar o arquivo anual contra a fonte remota (validador HTTP) antes de reutilizar o ZIP local, rebaixando apenas quando a fonte mudou; em falha de revalidação, servir o arquivo local (stale-on-failure) e atualizar os metadados.

### [copy-fundamentos-csv](openspec/changes/archive/2026-09-10-copy-fundamentos-csv) Botão Copiar Dados passa a copiar a tabela de Fundamentos quando essa sub-aba está ativa

#### Changed

- Quando a aba principal for "Análise Geral" e a sub-aba selecionada for "Fundamentos", o botão "Copiar Dados" (e `Ctrl+Shift+C`) copia o conteúdo da tabela de Fundamentos (cabeçalho + uma linha por ticker exibido) em vez do CSV bruto de negociações.
- A cópia da tabela reutiliza o mesmo mecanismo de clipboard (`pyxclip` primário, fallback Tkinter) e o mesmo feedback na statusbar do fluxo existente.
- Fora dessa combinação de abas, o fluxo de cópia atual permanece inalterado.

### [cvm-monthly-fund-data](openspec/changes/archive/2026-09-10-cvm-monthly-fund-data) Segunda fase: extração do Informe Mensal Estruturado da CVM como fallback de patrimônio/cotas/cotistas e P/VP

#### Added

- Nova camada de aquisição CVM (`dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL`) por CNPJ: download do ZIP anual, extração dos CSVs, descoberta/versionamento de schema, filtro por CNPJ e competência, seleção da reapresentação mais recente e preservação de hash/metadados.
- Resolução de identidade (`FundIdentity`): ticker → CNPJ + idFNET + codeCVM, combinando a identidade B3 (change anterior) com o cadastro CVM.
- Normalização de patrimônio (`PatrimonioFii`): `VL_PATRIM_LIQ`, `QT_COTA`, `NR_COTST` a partir do schema 2025+, com aliases legados (`CNPJ_Fundo`, `QUANT_COTA`).

#### Changed

- Atualização/encapsulamento do `CvmFiiAdapter` existente para consumir o novo repositório, removendo o acoplamento ao schema antigo.
- O patrimônio da CVM passa a ser usado como fallback para `P/VP` quando o Fundamentus não fornecer o dado; `FFO Yield`, `P/FFO` e `FFO Trend` permanecem `N/A`.

### [deterministic-ffo-engine](openspec/changes/archive/2026-09-10-deterministic-ffo-engine) Terceira fase: motor determinístico de FFO a partir de componentes estruturados da CVM (Informe Trimestral + DFIN)

#### Added

- Nova camada de aquisição CVM do Informe Trimestral Estruturado e das Demonstrações Financeiras (DFIN) por CNPJ, sobre o pipeline de dados abertos da CVM.
- Classificador determinístico de componentes de resultado (`RECURRING`, `FAIR_VALUE`, `DISPOSAL`, `NON_RECURRING`, `UNKNOWN`), com regra conservadora: apenas `RECURRING` entra no FFO.
- Motor de FFO: FFO mensal → FFO 12m → FFO por cota (média ponderada de cotas) → FFO Yield e P/FFO, com qualidade (`HIGH`/`MEDIUM`/`LOW`) e proveniência por componente.
- Reconciliação com DFIN/Informe Trimestral, gerando warning quando a diferença exceder o limite configurável.

#### Changed

- O FFO calculado passa a atuar como fallback do Fundamentus: quando o Fundamentus não fornece FFO, as métricas usam o motor determinístico.
- Integração com o motor de métricas existente, definindo uma única fonte de verdade para `FFO Yield` e `P/FFO`.

### [fii-patrimonio-cotistas-provider](openspec/changes/archive/2026-09-10-fii-patrimonio-cotistas-provider) Preenche cotistas/patrimônio/VP-Cota via B3 (type=40) com fallback CVM e corrige a resolução de ticker na B3

#### Changed

- BREAKING (resolução B3): a resolução de ticker passa a usar `GetListFunds` (busca por `acronym` → `id` primário) e a consultar `GetListClassFund` por `idFNET`; corrige a resolução hoje quebrada, pré-requisito de toda a aquisição B3.
- A B3 passa a listar e extrair o Informe Mensal Estruturado (`GetStructuredReports`, `type=40`), baixando o documento do FundosNet e extraindo por rótulo: `Número de cotistas`, `Patrimônio Líquido`, `Número de Cotas Emitidas` e `Valor Patrimonial das Cotas`.
- A B3 (type=40) passa a ser a fonte primária de cotistas/patrimônio/cotas/VP-Cota, por ser mais atual: disponível por ticker assim que o informe é entregue (ex.: referência 07/2026 entregue em 14/08/2026), contra ~3 semanas de latência do arquivo anual da CVM (revalidado em 05/09/2026).
- A CVM permanece como fallback, passando a ler o layout multi-arquivo atual (`inf_mensal_fii_complemento_*`: `Total_Numero_Cotistas`, `Patrimonio_Liquido`, `Cotas_Emitidas`, `Valor_Patrimonial_Cotas`), sem abortar a leitura por `CvmSchemaError` de um arquivo isolado.
- As colunas "Nº de cotistas", "Patrimônio" e "VP (VP/Cota)" passam a ser preenchidas a partir da fonte consolidada.

### [fundamental-dividend-consolidation](openspec/changes/archive/2026-09-10-fundamental-dividend-consolidation) Tendência do dividendo por comparação direta e consolidação de data-com/dividendos de B3, CVM e Fundamentus

#### Changed

- BREAKING (rótulos): a tendência do dividendo passa a ser `Neutro` (igual), `Crescimento` (acima) e `Redução` (abaixo), por comparação direta entre o último dividendo e o anterior, sem banda de tolerância.
- A última data-com e o par último/anterior de dividendos passam a ser consolidados a partir do histórico B3 (primário), CVM (secundário) e Fundamentus (fallback), preenchendo o que estiver faltando.
- A coluna "Última data-com" da tabela passa a ser preenchida para todos os tickers em que houver dado consolidado.

### [fundamental-metrics-table](openspec/changes/archive/2026-09-10-fundamental-metrics-table) Tabela fundamentalista "Fundamentos" na aba "Análise Geral" com FFO Yield, Dividend Yield, P/FFO e P/VP para FIIs elegíveis

#### Added

- Nova sub-aba "Fundamentos" no sub-notebook da aba "Análise Geral", com uma tabela (`ttk.Treeview`) alimentada pela watchlist de tickers
- Colunas de identidade para todos os tickers: ticker, nome, tipo (ação/FII/ETF/BDR) e sub-tipo (FII: tijolo/papel/híbrido/fiagro/fiinfra; ação: ordinária/preferencial/ETF)
- Classificação de tipo/sub-tipo: tipo e sub-tipo de ação derivados sintaticamente do ticker e cruzados com `code-cvm-resolution`; sub-tipo de FII via taxonomia versionada
- Colunas de dividendo para todos os tickers: última data-com, último dividendo (somente `Rendimento`; amortização excluída) e tendência do dividendo (último vs. anterior, banda de ±5% configurável, `N/A` sem dividendo anterior)
- Colunas fundamentalistas apenas para FIIs elegíveis (tijolo/híbrido): FFO Yield, Dividend Yield 12m, P/FFO, P/VP, FFO Trend, nº de cotistas + classe e patrimônio + classe — conforme RFC-006/007; ações/ETF/papel/fiagro exibem `N/A`
- Adapter CVM para NAV, nº de cotas e nº de cotistas; provedor Fundamentus para FFO 12m/3m
- Camada de domínio isolada (funções puras, `decimal.Decimal`, evidência por métrica) conforme RFC-007

#### Changed

- Reuso do preço de fechamento dos dados B3 já baixados (sem novo adapter de mercado)

### [fundamentos-correcoes](openspec/changes/archive/2026-09-10-fundamentos-correcoes) Corrige parser de proventos B3, expõe VPA e histórico de proventos do Fundamentus e padroniza casas decimais

#### Added

- Fundamentus (Papel): expor o indicador `VPA` como `vp_cota` para ações e prover o histórico de proventos de `proventos.php` como uma implementação de `DividendHistoryProvider`.

#### Changed

- Layout: formatar com exatamente 2 casas decimais as colunas "Último dividendo", "Dividendo anterior", "Dividend Payout (DY/FFOY)", "P (Cotação)" e "VP (VP/Cota)".
- Dividendos: ligar o `historico_dividendos` no wiring e consolidar B3 (FII) + histórico Fundamentus para preencher data-com, último/anterior e tendência em FII e Papel.
- BREAKING (dados exibidos): para FIIs, "Último dividendo" passa a ser o rendimento mais recente da B3 (com data real) em vez do `Dividendo/cota` do Fundamentus; a formatação fixa de 2 casas altera a saída textual e o CSV.

#### Fixed

- B3 (FII): corrigir o parser do documento FundosNet para o layout real de duas colunas (`Rendimento | Amortização`), identificando o tipo pela coluna que contém o valor e extraindo a `Data-base` do rótulo parentético. Adicionar fixture de contrato do documento real.

### [fundamentos-pl-acionistas-layout](openspec/changes/archive/2026-09-10-fundamentos-pl-acionistas-layout) Reordena colunas com P/L, número de acionistas via FRE e rótulos descritivos de tendência

#### Added

- P/L (Papel): expor o indicador `P/L` do Fundamentus como campo fundamentalista e exibi-lo na tabela.
- P/L (FII): calcular `P/L = Preço / (Último dividendo × 12)`, anualizando o dividendo mensal para expressar a quantidade de anos, por função pura de domínio, com `N/A` quando o último dividendo for ausente ou zero.
- Nº de acionistas (Papel): obter a quantidade de acionistas do FRE (`distribuicao_capital`, somando pessoa física, pessoa jurídica e investidores institucionais) usando a ponte ticker→CNPJ do FCA (`valor_mobiliario`), preenchendo "Nº de cotistas" e reutilizando `classificar_cotistas` para "Classe de cotistas". FII mantém a fonte atual (Informe Mensal/B3).

#### Changed

- Layout: reordenar as colunas da tabela de Fundamentos para `Ticker;Nome;Tipo;Sub-tipo;P (Cotação);VP (VP/Cota);P/VP;P/L;Dividend Yield;Última data-com;Último dividendo;Dividendo anterior;Tendência do dividendo;FFO Yield;Dividend Payout (DY/FFOY);FFO Trend;P/FFO;Nº de cotistas;Classe de cotistas;Patrimônio;Classe de patrimônio;Data de referência`, adicionando a coluna `P/L` após `P/VP` e alinhando-a à direita.
- Rótulos de tendência: exibir rótulos descritivos no lugar dos identificadores do enum: `FORTE_ALTA` = `Forte Alta`, `ALTA` = `Leve Alta`, `ESTAVEL` = `Estável`, `QUEDA` = `Leve Queda` e `FORTE_QUEDA` = `Forte Queda`.
- Tendência do dividendo: classificar em cinco faixas percentuais com os mesmos rótulos do FFO Trend: `Forte Alta` (≥ +5%), `Leve Alta` (> 0% e < +5%), `Estável` (= 0%), `Leve Queda` (≥ −5% e < 0%) e `Forte Queda` (< −5%).
- BREAKING (valores exibidos): os valores de `TendenciaDividendo` deixam de ser `Crescimento`/`Redução`/`Neutro` e passam às faixas do FFO Trend, alterando a saída textual/CSV e os testes de tendência; "FFO Trend" deixa de exibir `FORTE_ALTA` e passa a exibir `Forte Alta`.

### [fundamentos-table-columns](openspec/changes/archive/2026-09-10-fundamentos-table-columns) Adiciona dividendo anterior, payout, P e VP/Cota e reordena/alinha as colunas da tabela de Fundamentos

#### Added

- Novas colunas:
- Dividendo anterior: valor do dividendo imediatamente anterior (`UltimoDividendo.valor_anterior`).
- Dividend Payout (DY/FFOY): razão `Dividend Yield / FFO Yield`.
- P (Cotação): preço de mercado do ativo (campo `cotacao` do Fundamentus).
- VP (VP/Cota): valor patrimonial por cota reportado pelo Fundamentus.
- O Fundamentus passa a expor `VP/Cota` como campo normalizado da análise fundamentalista.

#### Changed

- BREAKING (colunas): a tabela fundamentalista passa a exibir, nesta ordem: Ticker, Nome, Tipo, Sub-tipo, Última data-com, Último dividendo, Dividendo anterior, Tendência do dividendo, FFO Yield, Dividend Yield, Dividend Payout (DY/FFOY), FFO Trend, P (Cotação), VP (VP/Cota), P/FFO, P/VP, Nº de cotistas, Classe de cotistas, Patrimônio, Classe de patrimônio, Data de referência.
- "FFO Trend" é movida para logo após "Dividend Payout (DY/FFOY)".
- Alinhamento à direita do conteúdo das colunas: Último dividendo, Dividendo anterior, FFO Yield, Dividend Yield, Dividend Payout (DY/FFOY), P, VP, P/FFO, P/VP, Nº de cotistas e Patrimônio.
- O sub-tipo passa a concatenar suas partes com `", "` em vez de `"; "` (tanto para FII quanto para Papel).
- Fora de escopo: congelamento das colunas Ticker/Nome (não será implementado).

### [fundamentos-table-data](openspec/changes/archive/2026-09-10-fundamentos-table-data) Deriva Tipo/Sub-tipo do Fundamentus, remove gate de FFO e preenche colunas de cotistas/patrimônio

#### Added

- Novas colunas ao final da tabela: número atual de cotistas, classificação por número de cotistas, tamanho patrimonial do fundo, classificação por tamanho patrimonial e data de referência dos dados.

#### Changed

- BREAKING (classificação): as colunas "Tipo" e "Sub-tipo" passam a ser derivadas do Fundamentus, substituindo a taxonomia/sintaxe anteriores:
- "Tipo" = `Papel` (rótulo `Papel`) ou `FII` (rótulo `FII`);
- `Papel`: Sub-tipo = `Tipo; Setor; Subsetor` (concatenados por `"; "`);
- `FII`: Sub-tipo = `Tijolo: Segmento; Gestão` quando `Qtd imóveis > 0`, senão `Papel: Segmento; Gestão`.
- O parser do Fundamentus extrai o discriminador do ticker (`Papel`/`FII`) e os campos `Tipo`, `Setor`, `Subsetor`, `Segmento`, `Gestão`; `Qtd imóveis` (já extraído) passa a ser o balizador Tijolo/Papel.
- Todas as colunas da tabela passam a ser preenchidas quando houver dado na fonte (Fundamentus primário, B3/CVM como fallback), inclusive P/VP, Dividend Yield e dividendo para ações.
- A classificação por cotistas e por patrimônio reutiliza as faixas determinísticas já existentes.
- Quando o Fundamentus não fornecer a classificação, a taxonomia/sintaxe atual (`classificar_ticker`) permanece como fallback.

#### Removed

- O gate de elegibilidade FFO é removido: FFO Yield, P/FFO e FFO Trend são preenchidos sempre que a fonte fornecer o dado, independentemente do tipo do ticker.

### [fundamentos-table-ux](openspec/changes/archive/2026-09-10-fundamentos-table-ux) Persiste largura das colunas, melhora feedback de cache/status e mantém cursor de espera durante a análise

#### Added

- As larguras das colunas da tabela fundamentalista são persistidas no `config.json` e restauradas na próxima execução.

#### Changed

- O texto de progresso da análise fundamentalista recebe o sufixo `" - cached"` quando o dado do ticker vem do cache (resultados `HIT` e `REVALIDATED`).
- Ao final da carga, a barra de status exibe:
- `"Dados atualizados com sucesso."` quando não houve falha na captura;
- `"Dados atualizados com mitigação de falhas."` quando houve falha recuperável;
- `"Falha ao atualizar dados"` em falha catastrófica.

#### Fixed

- O cursor de espera (`watch`) permanece visível durante toda a análise fundamentalista, inclusive quando os dados vêm do cache.

### [fundamentus-fundamental-provider](openspec/changes/archive/2026-09-10-fundamentus-fundamental-provider) Provider completo do Fundamentus como fonte primária, com composição e fallback por campo (B3/CVM/motor FFO)

#### Added

- Implementação do provider do Fundamentus conforme RFC-011 (`detalhes.php?papel={TICKER}`): fetch, parsing tolerante a mudanças de layout, normalização para `Decimal`/`date` e modelo tipado para ações e FIIs.
- Novo modelo de domínio normalizado com proveniência por campo, usado para compor a análise fundamentalista.
- Camada de composição de provedores com prioridade por campo: Fundamentus primeiro; B3/CVM/motor-FFO como fallback; o resultado registra de qual fonte veio cada valor.
- Pacote `infrastructure/fii/fundamentus/` (fetch, parser, modelo), mantendo `obter_ffo` como adaptador fino para compatibilidade.

#### Changed

- Integração do provider composto ao `FundamentalAnalysisUseCase` como caminho primário; as fontes das changes anteriores deixam de ser o caminho principal e passam a ser substitutas.
- Reuso das dependências existentes (`requests` + `beautifulsoup4`), sem `httpx`/`lxml`/`pydantic`; rate-limit de 1 req/s e respeito a `robots.txt`.

### [progresso-fundamentos-statusbar](openspec/changes/archive/2026-09-10-progresso-fundamentos-statusbar) Barra de progresso na fase de Fundamentos, glifo de status consistente e cursor/controles durante a análise

#### Added

- Barra de progresso na fase de Fundamentos: exibir a barra de progresso durante a análise fundamentalista, avançando por ticker (`current`/`total`) e com um estado inicial `0/N`, mantendo-a visível até a conclusão da fase.

#### Changed

- Controles desabilitados durante a fundamental: manter botões, comboboxes, data entry e a lista de tickers desabilitados durante toda a análise fundamentalista em background, restaurando-os somente ao final, como ocorre na carga histórica.
- Ajuste de apresentação: a mensagem de progresso por ticker deixa de usar `set_status` com `ℹ` e passa a atualizar a barra de progresso com o marcador consistente. A mensagem publicada pelo job passa a carregar `current`/`total`.

#### Fixed

- Glifo de status consistente: substituir o `ℹ` por um marcador que renderize de forma confiável (ex.: `•`), alinhado aos demais glifos que já aparecem corretamente (ex.: `✓`).
- Cursor de espera em todos os widgets: propagar o cursor `watch` para os widgets interativos, inclusive os que definem cursor próprio (botões, lista de tickers, comboboxes e data entry), restaurando cada cursor ao final da operação.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.8.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
