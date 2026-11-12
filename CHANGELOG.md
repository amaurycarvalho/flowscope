# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui o placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional

### [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões

### [llm-chat-rag](openspec/changes/llm-chat-rag) Recuperação vetorial como evolução da `llm-chat`, com VectorStore SQLite, embeddings e indexação de documentos consultada pela aba "Chat AI"

### [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado, com gauge de concentração, card informativo e timeline AFT

## [1.8.2] - 2026-11-12

### [corrigir-cnpj-papel-por-codecvm](openspec/changes/archive/2026-11-12-corrigir-cnpj-papel-por-codecvm) CNPJ de Papel resolvido pelo casamento no FCA e, como fallback, pelo `codeCVM` da B3 com o cadastro de companhias abertas da CVM

#### Added

- Adicionar a aquisição e o cache do dataset `CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv`, com parser `CD_CVM → CNPJ_CIA`, hash do arquivo e versão do parser.
- Expor a resolução `ticker → codeCVM` do `B3FundRepository` e injetá-la no `CvmAcionistasSource`, reutilizando o cache de 30 dias já existente.
- Cobrir os quatro casos da watchlist com testes de regressão (`BPAC11`, `CMIN3`, `MBRF3`, `CSNA3`) e casos sintéticos de FCA literal e de fallback.

#### Changed

- Servir o último `codeCVM` persistido quando a B3 estiver indisponível e o cache estiver expirado, evitando que uma falha transitória derrube o CNPJ de Papel.
- Exibir a razão social do Papel imediatamente após o CNPJ em `Dados fiscais`, usando `DENOM_SOCIAL` do cadastro de companhias; FIIs e BDRs mantêm o formato atual.
- Manter a resolução atual como primeira tentativa e preservar a tolerância a falhas: ausência de codeCVM, cadastro indisponível ou CNPJ inválido não devem impedir a análise dos demais tickers.
- Versionar o parser do cadastro e tolerar mapas normalizados em formato anterior, para que um cache antigo (valor string em vez de identidade) não faça o CNPJ do Papel desaparecer.

#### Fixed

- Resolver o CNPJ de Papel em duas etapas: primeiro pelo casamento exato de `Codigo_Negociacao` no FCA; se não houver correspondência, resolver o `codeCVM` via B3 e usá-lo como chave no cadastro de companhias abertas da CVM.

### [corrigir-dados-fiscais-fiagro](openspec/changes/archive/2026-11-12-corrigir-dados-fiscais-fiagro) `Dados fiscais` de FIAGROs completos com CNPJ e gestor extraídos do Informe Mensal da B3, usando a identidade persistida como fallback

#### Added

- Extrair o CNPJ do fundo do Informe Mensal aceitando os rótulos `CNPJ do Fundo/Classe` e `CNPJ do Fundo`, sem invalidar os demais campos quando o rótulo variar.
- Extrair do Informe Mensal do FundosNet o gestor (nome e CNPJ), ao lado do administrador já suportado, ampliando o modelo normalizado do informe e o provider fundamentalista da B3.

#### Changed

- Passar o gestor do FII/FIAGRO a ser resolvido primeiro pelo Informe Mensal da B3, mantendo o Informe Anual da CVM (`INF_ANUAL`) como fallback quando a B3 não fornecer o dado.
- Reutilizar a identidade persistida `ticker → idFNET → CNPJ` (já gravada pela solução de resiliência da resolução de fundos) como fonte do `idFNET` na leitura do Informe Mensal e como fallback do CNPJ fiscal quando o informe não o trouxer ou a B3 estiver indisponível, sem criar um segundo cache.
- Tornar a listagem de documentos do `GetStructuredReports` resistente a respostas vazias intermitentes: repetir uma vez a primeira página vazia, versionar a chave de cache e não persistir vazio persistente, para que administrador e gestor não desapareçam por um cache envenenado.
- Manter a proveniência (`B3`/`CVM`) por campo e a omissão de itens sem valor em nenhuma fonte.

### [fortalecer-captura-guidance-fiis](openspec/changes/archive/2026-11-12-fortalecer-captura-guidance-fiis) Guidance corrente de FIIs desempatado por método e momento da avaliação, com proveniência no ledger, leitura tolerante da resposta da IA e normalização de período

#### Added

- Registrar no ledger a proveniência da avaliação (`avaliado_em`, versão do prompt e, quando disponível, modelo) e reavaliar entradas `ia` quando a versão do prompt/modelo mudar, tratando entradas antigas sem versão como desatualizadas.
- Registrar em log o conflito em que a IA conclui ausência em todas as fontes, mas o extrator determinístico encontra guidance, sem sobrescrever automaticamente a decisão da IA.

#### Changed

- Derivar o guidance corrente com desempate explícito: entre entradas com a mesma data de relatório, `ia` prevalece sobre `deterministico`; persistir o momento da avaliação para desempatar avaliações do mesmo método.
- Tornar a interpretação da resposta da IA tolerante a formato (`R$`, separador de milhar, faixa, “por cota”) e tratar `GUIDANCE: SIM` sem valores interpretáveis como falha da IA, recorrendo à extração determinística em vez de gravar ausência indevida.
- Normalizar o período retornado pela IA, convertendo valores vagos (`não especificado`, `sem período`, `N/A`) em ausência de período e preservando períodos reconhecidos.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.8.2...HEAD
[1.8.2]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.8.2

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
