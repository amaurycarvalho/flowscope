# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui o placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional

### [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões

### [llm-chat-rag](openspec/changes/llm-chat-rag) Recuperação vetorial como evolução da `llm-chat`, com VectorStore SQLite, embeddings e indexação de documentos consultada pela aba "Chat AI"

#### Added

- VectorStore em SQLite puro, com busca top-k por cosine similarity e filtro opcional por ticker.
- Módulo de embeddings com dois provedores: `fastembed` (local, default) e liteLLM (API).
- Porta `DocumentoIndexavel`/`DocumentSource` e fontes concretas, com extração de texto (HTML e PDF).
- Pipeline de indexação (`IndexarDocumentosUseCase`) e consulta RAG (`ConsultarDocumentosUseCase`) consumindo a porta `LLMPort` da `llm-core`.
- Integração da consulta RAG à aba "Chat AI" como fonte adicional de contexto, pelo ponto de extensão da `llm-chat`.
- Chunker de texto em Python puro.
- Configuração de embedding persistida em `llm.embedding` e presets de provedores de embedding.
- Dependência opcional `fastembed` no grupo `[llm]`.
- CLI `--index <TICKER>` com `--data-inicio` e `--data-fim`.

### [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado, com gauge de concentração, card informativo e timeline AFT

## [1.3.0] — 2026-09-25

### [correlation-cointegration-panel](openspec/changes/archive/2026-09-25-correlation-cointegration-panel) Nova sub-aba "Rede de Correlação" na "Análise Geral" com grafo force-directed, codificando a correlação assinada na cor da aresta e a cointegração (Engle-Granger + ADF em `numpy` puro) no estilo/espessura

#### Added

- Nova sub-aba "Rede de Correlação" na "Análise Geral", com grafo force-directed (nós = papéis, arestas = pares com relação relevante).
- Codificação visual dupla: cor da aresta = correlação de curto prazo assinada (colormap divergente, escala fixa `[-1, +1]`); estilo/espessura = cointegração de longo prazo (sólido/grosso quando cointegrado, tracejado/fino caso contrário).
- Cor do nó = comunidade da rede; tamanho do nó = centralidade (grau).
- Cálculo de correlação e cointegração (Engle-Granger + ADF) implementado em `numpy` puro, sem `statsmodels`/`scipy`.
- Rede calculada sobre o resultado já carregado na análise corrente, filtrado pelos tickers selecionados no Listbox, sem leitor de cache, download, janela própria ou job em background.
- Recálculo automático quando o período ou a amostragem mudam com a sub-aba ativa.
- Gates por densidade: correlação exige ≥ 30 observações alinhadas; cointegração exige ≥ 40, com diagnóstico de gaps (mín/mediana/máx em dias úteis) e span de calendário.
- `networkx` adicionado para layout (`spring_layout`), detecção de comunidades e centralidade.
- Texto de orientação (OrientationPanel) e a mesma barra de ferramentas (`ToolbarBR`) da sub-aba VWAP, incluindo "Copiar Gráfico".

### [llm-chat](openspec/changes/archive/2026-09-25-llm-chat) Aba de topo "Chat AI" que responde em linguagem natural sobre os dados carregados, os documentos em cache e o próprio FlowScope, com cascata de recuperação sobre resumos e texto e histórico de conversa em memória

#### Added

- Aba de topo "Chat AI", única e sempre visível, entre "Análise do Ticker" e "Sobre", como ponto único de entrada do chat.
- Sem seletor de escopo: o contexto cobre a watchlist completa e a LLM infere o ticker referido na pergunta.
- Contexto com três origens: conhecimento do próprio FlowScope, tabela de fundamentos carregada e documentos em cache (watchlist completa).
- Cascata de documentos: resumos curtos → resumos longos → texto integral dos alvos, com interrupção antecipada ao obter resposta.
- Histórico textual da conversa com teto de 10 mensagens e 8.000 caracteres; erros e avisos fora do histórico e sessão em memória, sem persistência.
- Confirmação ao usuário conforme a quantidade de documentos-alvo (até 3 prossegue; 4 a 7 lista os nomes; 8 ou mais informa a quantidade).
- Cabeçalho com "Limpar", "Copiar chat" e "Configuração"; campo de entrada e "Enviar" habilitados apenas com a LLM configurada e fundamentos carregados.
- Botão "Limpar" com confirmação (Sim/Não); "Limpar" e "Copiar chat" habilitados apenas quando há conteúdo textual.
- Bloqueio de "Limpar", "Copiar chat", "Configuração" e "Enviar" durante o envio, com restauração ao término ou cancelamento.
- Quadro de texto orientativo das abas "Chat AI" e "Sobre"; a cópia de dados CSV inclui o conteúdo do chat quando a aba está ativa.
- Respostas em campo somente-leitura com cursor, seleção e atalhos de teclado; erros da LLM na statusbar e no log.
- Caches da sub-aba "Notícias" oferecidos como fonte adicional de contexto do chat.

#### Changed

- Sem VectorStore, embeddings, chunker, indexação ou `--index`, itens que migram para a change `llm-chat-rag`.

### [llm-config-por-provedor](openspec/changes/archive/2026-09-25-llm-config-por-provedor) Persistência da configuração de completion por provedor no bloco `llm.chat`, com restauração da configuração salva ao trocar de provedor e migração do formato plano anterior

#### Added

- Mapa `providers` no bloco `llm.chat` com `api_url`, `model`, `api_key` e `rpm` por provedor, mantendo `provider` como a seleção ativa.
- Restauração automática da configuração salva ao trocar de provedor; sem configuração salva, aplica os defaults do preset e limpa a chave, sem herdar a de outro provedor.
- Selecionar `none` limpa os campos ativos sem apagar as configurações dos demais provedores, permitindo voltar a qualquer um e retomar o que foi salvo.
- Gravação em disco apenas ao clicar em "Salvar"; edições ainda não salvas ficam em memória durante a sessão do diálogo.
- Migração automática do formato plano (sem `providers`) na primeira gravação, sem perder a configuração existente.

#### Changed

- `load_llm_config()` continua devolvendo o dicionário plano resolvido do provedor ativo, preservando os consumidores atuais (factory, resumo de documentos, guidance e chat).

### [noticias-b3](openspec/changes/archive/2026-09-25-noticias-b3) Nova sub-aba "Notícias" na Análise Geral, com aquisição e cache do corpo dos artigos, pré-visualização, resumos por LLM e disponibilização como contexto do "Chat AI"

#### Added

- Sub-aba "Notícias" na Análise Geral com árvore, pré-visualização e botões "Atualizar", "Abrir", "I.A." e "Resumir pendentes".
- Categorias de topo "Geral", "Censuras Públicas", "Condições Excepcionais" e "Programas de Aquisição de Ações", cada uma seguindo a sub-estrutura ano → mês → categoria → item.
- Categoria "Geral" lista o Plantão B3 do último ano, somente casos excepcionais de mercado, com carga incremental dia a dia e marcadores persistidos da data mais antiga processada e da última carga.
- Fontes regulatórias ("Censuras Públicas", "Condições Excepcionais" e "Programas de Aquisição de Ações") carregadas com histórico completo e tolerância à falha individual.
- Cache próprio do HTML das notícias, reuso dos caches de texto e resumos da sub-aba "Documentos" e índice de metadados para exibição sem rede.
- Carga inicial somente do cache local; a listagem e a aquisição de novos itens ocorrem apenas pelo botão "Atualizar", em segundo plano.
- Status por categoria durante o "Atualizar", carga parcial preservada a cada item processado e escritas do índice agrupadas em lotes.
- Corpo do artigo da "Geral" extraído de `#conteudoDetalhe`, com resolução sob demanda de documentos vinculados da CVM RAD e do FNET.
- Extração de texto (HTML → texto), resumo curto/longo por LLM, pré-visualização e abertura do artigo no navegador.
- Conteúdo disponibilizado como fonte adicional de contexto da aba "Chat AI", cobrindo as quatro categorias, com o ticker inferido pela LLM.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
