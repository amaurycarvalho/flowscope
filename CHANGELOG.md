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

## [0.9.0] — 2026-09-15

### [evolucao-fundamentos](openspec/changes/archive/2026-09-15-evolucao-fundamentos) Sub-aba "Evolução dos Fundamentos" na aba "Análise do Ticker" com small multiples da evolução temporal dos campos Cotação, VP, P/VP, DY, Último dividendo, Nº de cotistas e Nº de cotas

#### Added

- Criar a sub-aba "Evolução dos Fundamentos" na aba "Análise do Ticker", exibindo a evolução temporal (timeseries) dos campos Cotação, VP, P/VP, DY, Último dividendo, Nº de cotistas e Nº de cotas para o ticker selecionado.

#### Changed

- Ler os dados exclusivamente do cache histórico de fundamentos, sem qualquer aquisição de rede ao abrir a sub-aba.
- Amostrar as datas do cache por Fibonacci de forma acumulada a partir da observação mais recente (gaps de 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377 dias), aproximando cada alvo para a data de cache mais próxima e incluindo sempre a mais antiga e a mais recente, exibidas em ordem crescente.
- Representar os campos em small multiples (um mini-gráfico de linha por campo, eixo X de datas compartilhado e escala própria), preservando a leitura dos valores absolutos por um leigo.
- Permitir que o duplo clique em uma linha da tabela da sub-aba "Fundamentos" (aba "Análise Geral") fixe o ticker e torne ativa a sub-aba "Evolução dos Fundamentos".
- Popular a sub-aba de forma preguiçosa (somente quando selecionada), funcionando apenas com o cache mesmo sem carga B3 corrente.
- Exibir estado vazio quando não houver histórico retido para o ticker e preencher o quadro de texto orientativo da sub-aba no mesmo padrão explicativo das demais.

### [fundamentos-cache-historico](openspec/changes/archive/2026-09-15-fundamentos-cache-historico) Cache histórico estruturado da tabela de Fundamentos por `(ticker, data)`, com read-through, retenção de 365 dias e atualização forçada

#### Added

- Introduzir um cache estruturado do resultado da análise fundamentalista (o conteúdo da linha da tabela "Fundamentos"), chaveado por `(ticker, data escolhida na GUI)`, com a `data_referencia` guardada dentro do registro.

#### Changed

- Persistir o `AnaliseFundamental` estruturado (não os valores formatados), com `schema_version` por observação, em um arquivo JSON por ticker contendo um mapa `data -> observação`.
- Reter um histórico deslizante de 365 dias, com prune na escrita e observações expiradas ignoradas na leitura.
- Integrar o cache como read-through no `FundamentalAnalysisUseCase`: em HIT, pular todo o pipeline de aquisição; em MISS, executar o caminho atual e registrar.
- Nunca gravar observações com `erro`; observações parciais (sem identidade do Fundamentus) podem ser sobrescritas no mesmo dia; observações completas são imutáveis no dia (first-write-wins).
- Tornar a leitura estrita para o HIT do dia (exige `schema_version` atual) e tolerante para consultas de histórico (best-effort, marcando a versão).
- Expor uma porta de recuperação (`obter`, `historico`, `datas`, `registrar`) para as futuras consultas de evolução do ticker.
- Ligar o cache por padrão e oferecer um caminho explícito de bypass para forçar recomputo e sobrescrever a observação do mesmo dia.
- Aplicar a todos os tickers (FII e Papel).

### [fundamentos-numero-cotas](openspec/changes/archive/2026-09-15-fundamentos-numero-cotas) Adiciona a coluna `Nº de cotas` (quantidade de cotas/ações emitidas) antes de `Nº de cotistas`, priorizando B3/CVM para FIIs e o Fundamentus para Papéis

#### Added

- Adiciona a coluna `Nº de cotas` imediatamente antes de `Nº de cotistas`, alinhada à direita e formatada como inteiro com separador de milhar.

#### Changed

- Expõe no Fundamentus a quantidade de cotas/ações emitidas: `Nro. Cotas` (FII) e `Nro. Ações` (Papel), normalizados em `Decimal`.
- Resolve a quantidade por tipo de ativo: para **FII**, prioriza a B3 (Informe Mensal) e a CVM como fallback, usando o Fundamentus como fallback final; para **Papel**, usa o Fundamentus (única fonte disponível), exibindo `N/A` quando ausente.
- Propaga o valor resolvido por `AnaliseFundamental.cotas`, reutilizando o `PatrimonioFii` já buscado e memorizado (sem novo acesso à rede).
- Atualiza a lista/ordem de colunas, o alinhamento numérico e o quadro de orientações da sub-aba "Fundamentos".
- A contagem de colunas passa de 29 (2 fixas + 27 roláveis) para 30 (2 fixas + 28 roláveis).

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.9.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
