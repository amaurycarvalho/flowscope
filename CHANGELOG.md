# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [correlation-cointegration-panel](openspec/changes/correlation-cointegration-panel) Nova sub-aba "Rede de Correlação" na "Análise Geral" com grafo force-directed, correlação de curto prazo e cointegração (Engle-Granger + ADF) calculadas em `numpy` puro sobre o cache local de preços
- [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional
- [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões
- [llm-chat](openspec/changes/llm-chat) Assistente RAG integrado à GUI com VectorStore SQLite, embeddings e chat LLM via liteLLM
- [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado com gauge de concentração, card informativo e timeline AFT

## [1.2.0] — 2026-09-23

### [aba-sobre](openspec/changes/archive/2026-09-23-aba-sobre) Nova aba "Sobre" com informações institucionais, apresentação, links para repositório e log e verificação automática de nova versão

#### Added

- Nova aba de nível superior "Sobre", posicionada imediatamente após "Análise do Ticker", com conteúdo próprio de rolagem vertical e o painel de orientação à direita inalterado.
- Conteúdo da aba com ícone da aplicação, nome e versão (`FlowScope vX.Y.Z`), data de lançamento em formato ISO, licença GNU GPLv3, texto de apresentação derivado do `README.md`, botão para o repositório no GitHub e botão para abrir o log da aplicação.
- Verificação automática de nova versão ao abrir a aba, no máximo uma vez por sessão e em background, exibindo aviso e botão para a página da release quando houver versão mais recente.
- Nova constante `__release_date__` em `src/flowscope/__init__.py`, atualizada pelo fluxo de release junto de `__version__`.

#### Fixed

- Metadados de licença do `pyproject.toml` corrigidos de MIT para `GPL-3.0-only`, com elevação do `setuptools` mínimo para 77 (PEP 639).

### [analise-short-interest](openspec/changes/archive/2026-09-23-analise-short-interest) Adiciona quatro colunas de short interest (Shorts%, Volume de Shorts, Fechamento Shorts e Risco Fechamento) à tabela de Fundamentos

#### Added

- Quatro novas colunas à tabela da sub-aba "Fundamentos", entre `Tendência do dividendo` e `FFO/Receita (12m)`: `Shorts%`, `Volume de Shorts`, `Fechamento Shorts` e `Risco Fechamento`.
- `Shorts%` = `(Ações Alugadas ÷ Free Float) × 100`, numérico em percentual com uma casa decimal, e `Volume de Shorts` como classificação categórica em cinco rótulos.
- `Fechamento Shorts` (SIR) = `Ações Alugadas ÷ Volume Médio Diário de Negociação`, em dias com sufixo `d`, e `Risco Fechamento` como classificação categórica nos mesmos cinco rótulos.
- Free float obtido do CVM FRE (`Quantidade_Total_Acoes_Circulacao`), com fallback para o total emitido; ações alugadas obtidas da B3 (BTBLendingOpenPosition) e volume médio calculado em memória a partir do `daily_data` injetado.
- Escopo por tipo (`Papel`, `FII`, `ETF`/`FIAGRO`/`BDR`), resultando em `N/A` na coluna quando o insumo não existir, sem impedir as demais.

#### Changed

- **BREAKING (colunas)**: a ordem das colunas da tabela fundamentalista muda, e o CSV copiado e o texto de orientação da sub-aba passam a incluir as novas colunas.
- Bump da versão de schema do cache histórico de fundamentos para persistir os novos campos estruturados.

### [cache-texto-documentos](openspec/changes/archive/2026-09-22-cache-texto-documentos) Cache persistente do texto extraído por documento, eliminando a reconversão e curto-circuitando o processamento quando não há texto extraível

#### Added

- Cache persistente do texto extraído por documento em `~/.cache/flowscope/document-texts/<TICKER>.json`, com escrita atômica e tolerância a arquivo ausente ou corrompido, no mesmo modelo de `document_summaries.py`.
- Marcador `Sem texto extraível para pré-visualização.` gravado no cache quando não houver texto, tratado por um predicado compartilhado `tem_texto()`.

#### Changed

- A pré-visualização passa a ler o texto do cache e só converte (`pypdf`/`BeautifulSoup`) em *miss*, gravando o resultado para os acessos seguintes, sem invalidação por alteração do arquivo.
- Sem texto extraível, não se gera resumo LLM, não se tenta extrair guidance e não se executa qualquer outro processamento do texto, mantendo disponível a abertura do documento.
- A change `fii-guidance-informacoes-adicionais` passa a consumir o texto do novo cache, em vez de reextrair, e a não avaliar guidance quando não houver texto extraível.

#### Fixed

- Corrige a barra de rolagem vertical da árvore e do campo de texto da sub-aba "Documentos", empacotando a barra primeiro (ou por `grid` com pesos) para torná-la visível e funcional, inclusive com rolagem pela roda do mouse.

### [centralizar-controle-cursor](openspec/changes/archive/2026-09-22-centralizar-controle-cursor) Centraliza a política de estado ocupado no presenter como máquina de estado `IDLE <-> BUSY`, eliminando caminhos diretos de cursor

#### Added

- Máquina de estado `IDLE <-> BUSY` no presenter, com contagem de referência e context manager `busy()` que garante entrada/saída balanceadas mesmo em exceção.

#### Changed

- Removidos os caminhos diretos de cursor (`controller.on_ticker_edit`, `actions._copy_chart`) que furam o contador do presenter.
- Garantia de que todo `on_fundamental_started` tenha exatamente um `on_fundamental_finished`, inclusive quando `job.iniciar()` ou `on_progress` falham após o incremento.
- Watchdog de inatividade/liveness e tratamento por mensagem estendidos ao job de documentos, sem impedir `on_operation_finished`.
- Snapshot da view normalizado para ignorar cursores transitórios geridos pelo Tk (`hresize`, `sb_*`) e reafirmação do cursor enquanto ocupado em `<Motion>`.
- Teste de GUI da sincronização entre os dois `Treeview` da tabela de Fundamentos e teste de cobertura que enumera as abas/sub-abas construídas.

### [corrigir-botao-resumir-durante-lote](openspec/changes/archive/2026-09-23-corrigir-botao-resumir-durante-lote) Mantém o botão "Resumir pendentes" desabilitado durante o lote, reabilitando-o apenas ao término

#### Added

- Predicado de "resumo em lote em andamento" injetado no painel de documentos, no mesmo padrão de callbacks já usados (`resumir_callback`, `ia_callback`).

#### Fixed

- O estado derivado do botão "Resumir pendentes" passa a considerar o lote em andamento, mantendo-o desabilitado em qualquer reavaliação durante o processamento (documento aplicado, resumo individual concorrente ou recarregamento do painel) e reabilitando-o somente ao término, conclusão ou interrupção.
- Cobertura de testes para a permanência do estado desabilitado ao longo do lote e para a reabilitação ao término.

### [corrigir-vazamento-cursor-grid-fundamentos](openspec/changes/archive/2026-09-23-corrigir-vazamento-cursor-grid-fundamentos) Corrige o cursor de espera preso sobre o grid rolável da sub-aba "Fundamentos"

#### Fixed

- Captura do cursor de repouso torna-se robusta a valores que o Tk devolve como lista Tcl (por exemplo `('sb_h_double_arrow',)`), filtrando cursores transitórios de separador/sash antes de usá-los como baseline.
- Restauração do cursor nunca deixa o widget preso em "watch": se a restauração do baseline falhar, o widget volta ao cursor padrão.
- Teste de regressão de GUI cobrindo o ponteiro sobre o separador no início da operação.

### [fii-guidance-informacoes-adicionais](openspec/changes/archive/2026-09-23-fii-guidance-informacoes-adicionais) Cache de guidance por FII avaliado ao ler o Relatório Gerencial na sub-aba "Documentos" (LLM preferencial com fallback determinístico) e exibido em "Informações adicionais"

#### Added

- Cache de guidance por FII em `~/.cache/flowscope/guidance/<TICKER>.json`, com informação inicial vazia, escrita atômica e tolerância a ausência/corrupção.
- Avaliação do Relatório Gerencial ao ser lido na sub-aba "Documentos" (categoria `Relatorio`), lendo o texto do cache de documentos e sem reextrair o PDF; documento sem texto extraível não dispara avaliação.
- Flag de análise de guidance via LLM (`llm.guidance.enabled`), desabilitada por padrão: com o recurso disponível e funcional, a LLM faz a avaliação específica; caso contrário, usa-se a extração determinística (`pypdf` + regex) do valor, do período de validade e da data do relatório.
- Escopo restrito à palavra literal `guidance` e a ativos do tipo `FII`.

#### Changed

- A coluna `Informações adicionais` de FIIs passa a exibir um item `Guidance ...` lido do cache, sem calcular guidance na carga de dados nem na renderização; cache vazio → item omitido.
- O botão "Resumir pendentes" também avalia o guidance dos Relatórios Gerenciais pendentes já processados, reaproveitando o texto preparado pelo lote e sem interromper o lote em caso de falha; Relatórios já resumidos continuam atualizados apenas ao serem lidos.

### [interromper-processamento](openspec/changes/archive/2026-09-23-interromper-processamento) Botão de interromper na barra de status com cancelamento cooperativo de todos os processamentos em background ativos

#### Added

- Botão de interromper (ícone `process-stop.png`) na barra de status, imediatamente à esquerda da barra de progresso, visível apenas enquanto houver ao menos um job cancelável em background ativo.
- Um único clique cancela todos os processamentos em background ativos (fundamentalista, documentos e resumos em lote).
- Cancelamento cooperativo real com token compartilhado observado no topo dos loops de trabalho, encerrando o worker por uma exceção dedicada (`OperacaoCancelada`), sem ser confundido com falha recuperável.
- Ao cancelar, barra e botão somem, controles e cursor são restaurados, os flashes de sucesso são suprimidos e a barra de status exibe "Processamento interrompido.".

### [melhorias-evolucao-fundamentos](openspec/changes/archive/2026-09-23-melhorias-evolucao-fundamentos) Adiciona o painel `Shorts%` aos small multiples de "Evolução dos Fundamentos" e tooltip de hover, e corrige o formato de data para dia/mês/ano

#### Added

- Oitavo painel `Shorts%` nos small multiples da sub-aba "Evolução dos Fundamentos", representando a evolução de `AnaliseFundamental.short.shorts_pct` em percentual com uma casa decimal.
- Tooltip de hover em todos os painéis da sub-aba, exibindo a data e o valor do ponto sob o cursor.

#### Changed

- Texto do OrientationPanel da sub-aba e documentação (`panels.md`, `TAB_CONTENT`/`TAB_CONFIGS`) atualizados para refletir os oito painéis e o novo indicador.

#### Fixed

- Rótulo de data dos eixos dos gráficos corrigido de `MM/AA` (`%m/%y`) para `DD/MM/AA` (`%d/%m/%y`).

### [mensagens-amigaveis-erros-llm](openspec/changes/archive/2026-09-23-mensagens-amigaveis-erros-llm) Humaniza as mensagens de erro de I.A. por categoria de falha e introduz `LLMServiceUnavailableError` para sobrecarga/5xx do provedor

#### Added

- Novo subtipo de domínio `LLMServiceUnavailableError` para sobrecarga/erro 5xx do provedor, exportado pelo domínio de LLM.
- Helper de apresentação (erro → texto) que traduz cada categoria de falha em mensagem amigável, sem que a GUI dependa do liteLLM.

#### Changed

- Mensagens exibidas no botão "Resumir pendentes" e no campo de status do botão "Testar" do diálogo "I.A." passam a ser humanizadas, mantendo `str(exc)` técnico e os registros de log inalterados.
- `ServiceUnavailableError` e `InternalServerError` do liteLLM passam a mapear para o novo subtipo, antes da entrada genérica `APIError`.
- Texto bruto preservado para exceções que não forem da camada de LLM (ex.: falha de conversão de PDF) e banner de depuração do liteLLM (`Give Feedback / Get Help`, `LiteLLM.Info`) silenciado no terminal.

### [resumir-pendentes-documentos](openspec/changes/archive/2026-09-22-resumir-pendentes-documentos) Botão "Resumir pendentes" para processar em lote todos os documentos do ticker sem resumo, com progresso e interrupção segura

#### Added

- Botão "Resumir pendentes" na barra de controles da sub-aba "Documentos", imediatamente após o botão "I.A.", sempre visível e habilitado apenas quando a LLM está configurada, existe documento sem `long_summary` e nenhum lote está em andamento.
- Processamento em background, em duas fases (preparar o texto reutilizando o cache e gerar o resumo) de todos os documentos do ticker sem `long_summary`, persistindo os resumos e refletindo-os no catálogo em memória.
- Andamento exibido na barra de status com a barra de progresso, uma fase por vez, mantendo botões e cursor bloqueados pela autoridade única de estado ocupado.
- Interrupção do lote em qualquer erro, reportando na barra de status o documento e o motivo da falha e liberando os controles.
- Pulo de documentos sem texto extraível (`SEM_TEXTO`), sem chamar a LLM, contabilizando-os no desfecho.

#### Changed

- Estado do botão reavaliado após salvar a configuração de I.A. e ao término do lote.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.2.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
