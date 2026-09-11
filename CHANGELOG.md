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

## [0.8.1] — 2026-09-11

### [fundamentos-informacoes-adicionais-fiscais](openspec/changes/archive/2026-09-11-fundamentos-informacoes-adicionais-fiscais) Novas colunas Preço Típico, P / PT, Informações adicionais e Dados fiscais com ingestão do Informe Anual da CVM

### [fundamentos-congelar-colunas](openspec/changes/archive/2026-09-11-fundamentos-congelar-colunas) Congela as colunas Ticker e Nome na tabela de Fundamentos com dois Treeviews sincronizados

#### Added

- Congelamento: as colunas `Ticker` e `Nome` passam a ficar fixas à esquerda da tabela de Fundamentos, enquanto as demais 24 colunas rolam horizontalmente.
- Dois Treeviews sincronizados: a tabela passa a ser composta por um Treeview fixo (Ticker, Nome) e um Treeview rolável (demais colunas), lado a lado; a fronteira entre eles é a borda direita da última coluna congelada, reforçada por uma linha divisória vertical fixa (não arrastável).
- Scroll vertical compartilhado: uma única barra de rolagem vertical controla os dois Treeviews; a roda do mouse sobre qualquer um dos painéis rola ambos.

#### Changed

- Scroll horizontal: apenas o Treeview rolável possui rolagem horizontal; o painel congelado não rola.
- Largura da região congelada: a largura do painel congelado é a soma das larguras de `Ticker` e `Nome`, sem gap nem clipping; as larguras persistidas continuam sendo a única fonte de verdade.
- Seleção: a seleção de uma linha em qualquer um dos Treeviews é espelhada no outro; o modo multi-seleção é desabilitado.
- CSV inalterado: o botão "Copiar dados CSV" continua copiando a tabela inteira, com todas as 26 colunas.
- Compatibilidade: a preferência existente (`fundamental_column_widths`) permanece válida e passa a ser a única fonte de largura.

### [fundamentos-fallback-b3-cvm](openspec/changes/archive/2026-09-11-fundamentos-fallback-b3-cvm) Fallback B3/CVM para cotação, VP/Cota, classificação e FFO, e leitura do layout largo do Informe Trimestral

#### Added

- Preencher `P (Cotação)` e `Data de referência` a partir do último fechamento da B3 (`MarketPricePort`) quando o Fundamentus não fornecer.
- Preencher `VP (VP/Cota)` a partir do Informe Mensal da B3 (e da CVM como fallback), derivando `patrimônio líquido / cotas` quando o VP/Cota não vier reportado.
- Derivar `P/L` automaticamente quando `P` e a classificação FII estiverem disponíveis.
- Classificar `Tipo`/`Sub-tipo` a partir da "Classificação autorregulação" do Informe Mensal da B3 quando o Fundamentus não fornecer, produzindo rótulos como `FII` / `Papel: Outros, Ativa`.
- Preencher `Preço Típico` e `P / PT` a partir dos extremos (`Mín`/`Máx`) da janela de preços B3 já carregada em cache para a análise, restrita a 52 semanas antes da data de referência.

#### Changed

- BREAKING (comportamento do motor): restringir o motor determinístico de FFO a FIIs de tijolo/híbrido; para FII de papel, as métricas derivadas do motor permanecem `N/A`.
- Coordenação de ordem: esta change é aplicada depois de `fundamentos-informacoes-adicionais-fiscais` e constrói sobre os acréscimos daquela change nos módulos compartilhados, sem duplicar parsing nem sobrescrever campos.
- Cobertura de fallback (limites conhecidos): permanecem sem fallback B3/CVM e continuam `N/A` quando o Fundamentus não os fornece — `LPA`/`ROE`/`ROIC` (Papel) e `Qtd Imóveis`/`Cap Rate`/`Vacância Média` (FII).

#### Fixed

- Corrigir o `CvmQuarterlyRepository` para reconhecer e ler o layout largo real (`inf_trimestral_fii_resultado_contabil_financeiro_*.csv`), convertendo as colunas monetárias em componentes do FFO com código e proveniência preservados; o layout longo legado continua aceito.

### [fundamentos-orientacao-colunas](openspec/changes/archive/2026-09-11-fundamentos-orientacao-colunas) Atualiza o texto de orientação da sub-aba Fundamentos para descrever as novas colunas

#### Changed

- Atualizar o campo **Indicadores envolvidos** do conteúdo de orientação da sub-aba "Fundamentos" para descrever todas as colunas exibidas, incluindo Preço Típico, P / PT, Dividend Payout, Informações adicionais e Dados fiscais.
- Ampliar o campo **Como interpretar** com orientações sucintas sobre a leitura de Preço Típico e P / PT, do Dividend Payout, dos itens de Informações adicionais e da identidade fiscal.
- Manter o padrão existente de quatro campos na ordem **Objetivo → Responde a pergunta → Indicadores envolvidos → Como interpretar**, com formatação rica (negrito nos cabeçalhos, itálico na pergunta).

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.8.1...HEAD
[0.8.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.8.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
