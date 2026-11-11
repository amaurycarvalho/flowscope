# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui o placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional

### [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões

### [llm-chat-rag](openspec/changes/llm-chat-rag) Recuperação vetorial como evolução da `llm-chat`, com VectorStore SQLite, embeddings e indexação de documentos consultada pela aba "Chat AI"

### [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado, com gauge de concentração, card informativo e timeline AFT

## [1.8.1] - 2026-11-11

### [chat-fontes-estruturadas](openspec/changes/archive/2026-11-11-chat-fontes-estruturadas) Fontes consultadas pelo Chat AI separadas da resposta em campo estruturado, com checkbox "Exibir fontes" e cópia seguindo a tela

#### Added

- Adicionar campo opcional `fontes` ao JSON de resposta do protocolo de navegação, com entradas `{caminho, rotulo}` declaradas pela LLM no turno final.
- Adicionar o checkbox "Exibir fontes" (desmarcado por padrão) na aba "Chat AI", que mostra as fontes de cada resposta e re-renderiza todas as respostas ao alternar.
- Introduzir o bloco de fontes pelo rótulo `Fontes consultadas:`, com uma linha em branco antes e quebra de linha depois.

#### Changed

- Deixar de instruir a LLM a citar fontes no corpo de `resposta`; as fontes passam a ser declaradas no campo estruturado.
- Derivar as fontes exibidas da árvore, a partir dos caminhos efetivamente navegados (`listar`, `obter`, `buscar`, `buscar_semantico`), deduplicando e usando os rótulos declarados pela LLM; caminhos declarados inexistentes são descartados.
- Guardar as fontes da mensagem do assistente como itens estruturados (`caminho` + `rotulo` opcional), sem concatená-las ao texto.
- Exibir as marcações `Você:`, `Assistente:` e `Fontes consultadas:` em negrito no campo de mensagens.
- Fazer "Copiar chat" copiar o conteúdo exibido convertido para Markdown (marcações em negrito como `**...**`), seguindo o checkbox; a cópia de CSV da aba mantém o texto simples.
- Atualizar a orientação da aba e a documentação do chat para descrever o novo contrato.
- Marcar explicitamente os usos de SHA1 para chaves e identificadores determinísticos como não criptográficos (`usedforsecurity=False`), sem alterar os valores gerados.

#### Fixed

- Corrigir a extração derivada de fontes para cobrir `obter` e as buscas, que hoje não entram na lista.

### [litellm-model-cost-map-offline](openspec/changes/archive/2026-11-11-litellm-model-cost-map-offline) Primeira importação do `litellm` usa o catálogo local de model cost map, sem busca externa automática em máquinas offline

#### Added

- Definir `LITELLM_LOCAL_MODEL_COST_MAP=True` antes do primeiro `import litellm`, preservando um override explícito do usuário (`setdefault`).
- Cobrir com teste que o import do adaptador/presets usa a fonte local e não dispara a busca remota.

#### Changed

- Centralizar o preparo em um helper compartilhado, em vez de duplicar em `presets.py` e `adapter.py`.
- Garantir que a primeira importação do liteLLM não realize busca externa do model cost map, mantendo `get_model_cost_map_source_info()["source"] == "local"`.
- Manter `litellm.suppress_debug_info = True` e o comportamento de contagem de tokens/janela de contexto.

### [resiliencia-resolucao-fundos-b3](openspec/changes/archive/2026-11-11-resiliencia-resolucao-fundos-b3) Listagem de fundos da B3 completa e resiliente a páginas vazias, com chaves de cache versionadas e identidade persistida por ticker como fallback dos dados fiscais dos FIIs

#### Added

- Adicionar cache persistente ticker → `idFNET` → CNPJ, com nome e tipo do fundo, escrito a cada resolução bem-sucedida e consultado como fallback quando a B3 estiver indisponível ou a listagem vier incompleta.

#### Changed

- Tornar a listagem de fundos da B3 completa e resistente a respostas vazias intermitentes: `pageSize=120` (máximo aceito), repetição de páginas vazias com backoff e cache somente quando `len(results) == totalRecords`.
- Preservar a última listagem completa em caso de atualização parcial/indisponível, em vez de sobrescrever o cache com uma lista truncada.
- Invalidar as chaves de cache legadas de listagem e de resolução (versionar as chaves) para descartar listas parciais e ausências já gravadas.
- Tratar corpo vazio intermitente do `GetListClassFund` como conteúdo inválido repetível, usando o validador do motor de retry central.
- Não persistir resultados negativos (ticker sem correspondência) para não congelar falhas transitórias.
- Garantir que a identidade persistida esteja versionada, com escrita atômica e tolerância a corrupção, e que o CNPJ alimente o fallback CVM Anual mesmo quando a B3 falhar.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.8.1...HEAD
[1.8.1]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.8.1

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
