# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional
- [documentos-relevantes](openspec/changes/documentos-relevantes) Extração de documentos relevantes (PDFs) da B3 via GetReportsRelevants com cache e integração com VectorStore
- [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões
- [fundamentos-cache-historico](openspec/changes/fundamentos-cache-historico) Cache histórico estruturado da tabela de Fundamentos por `(ticker, data)`, com read-through, retenção de 365 dias e atualização forçada
- [fundamentos-numero-cotas](openspec/changes/fundamentos-numero-cotas) Adiciona a coluna `Nº de cotas` (quantidade de cotas/ações emitidas) antes de `Nº de cotistas`, priorizando B3/CVM para FIIs e o Fundamentus para Papéis
- [informe-mensal](openspec/changes/informe-mensal) Extração de Informes Mensais Estruturados (type=40) da B3 com entidades próprias e parsing multi-tabela
- [llm-chat](openspec/changes/llm-chat) Assistente RAG integrado à GUI com VectorStore SQLite, embeddings e chat LLM via liteLLM
- [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado com gauge de concentração, card informativo e timeline AFT

## [0.8.2] — 2026-09-14

### [fundamentos-ffo-receita](openspec/changes/archive/2026-09-14-fundamentos-ffo-receita) Recalcula o Dividend Yield de FII pelo último dividendo e substitui FFO Yield, P/FFO e Dividend Payout pelas razões FFO/Receita, Dividendos/Receita e Dividendos/FFO

#### Added

- Adicionar as colunas `FFO/Receita (12m)`, `FFO/Receita (3m)`, `Dividendos/Receita (12m)`, `Dividendos/Receita (3m)`, `Dividendos/FFO (12m)` e `Dividendos/FFO (3m)`, em notação percentual com uma casa decimal, calculadas apenas para Tipo `FII` (Tipo `Papel` exibe `N/A`).

#### Changed

- Recalcular o Dividend Yield de FIIs como `(último dividendo × 12) / P (Cotação)` quando o último dividendo e a cotação existirem; caso contrário manter o Dividend Yield do Fundamentus, preservando os fallbacks existentes para Tipo `Papel`.
- Tratar insumos negativos com texto na célula (`Receita negativa`, `FFO negativo` ou `Receita e FFO negativos`), exibindo `N/A` para divisão por zero e para dado ausente.
- Redefinir o `FFO Trend` como a diferença em pontos percentuais entre `FFO/Receita (3m)` e `FFO/Receita (12m)`, classificada nas cinco faixas existentes, posicionada após `FFO/Receita (3m)`.
- Expor `Receita` e `Rend. Distribuído` (12m e 3m) do Fundamentus na composição de campos fundamentalistas, tratando `Rend. Distribuído` como Dividendos.
- Atualizar o quadro de orientações da sub-aba "Fundamentos" para as novas colunas e sua leitura.

#### Removed

- Remover as colunas `FFO Yield`, `P/FFO` e `Dividend Payout (DY/FFOY)`.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.8.2...HEAD
[0.8.2]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.8.2

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
