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

## [1.1.0] — 2026-09-18

### [documentos-resumos](openspec/changes/archive/2026-09-18-documentos-resumos) Resumos curto e longo dos documentos via LLM, com lista Markdown dos agrupamentos, pré-visualização composta, geração sob demanda persistida, campo de texto copiável e persistência da configuração de I.A.

#### Added

- Novos campos `short_summary` (até 280 caracteres, nulo quando não gerado) e `long_summary` (até 1500 caracteres, nulo quando não gerado) no catálogo de documentos, com persistência em `~/.cache/flowscope/document-summaries/<TICKER>.json` (JSON por ticker, escrita atômica, chave = caminho relativo à raiz de cache).
- Novo serviço `ResumirDocumentoUseCase` que recebe o texto de um documento e produz os dois resumos via `LLMPort`, consumindo a base da change `llm-core`.

#### Changed

- Ao selecionar um agrupador da árvore (ticker, ano, mês ou categoria), o campo de texto exibe uma lista Markdown dos documentos contidos, com níveis relativos e o `short_summary` de cada documento; sem resumo, exibe a mensagem de indisponibilidade condicional.
- Ao selecionar um documento, o campo de texto exibe `long_summary`, linha em branco, `---`, linha em branco e o texto integral; sem `long_summary`, gera os dois resumos via LLM (fórmula XYZ) e os persiste, ou exibe a mensagem de indisponibilidade quando a LLM não está configurada/funcional.
- O campo de texto permanece somente-leitura, mas passa a aceitar atalhos de seleção e cópia (Ctrl+A, Ctrl+C, Shift+setas) e a exibir o cursor de foco.
- O botão "Copiar dados CSV" passa a copiar o conteúdo do campo de texto quando a sub-aba "Documentos" está ativa, ficando habilitado nessa sub-aba mesmo sem dados da B3.

#### Fixed

- Vincular explicitamente o atalho Ctrl+A no widget, pois no X11 o evento virtual `<<SelectAll>>` do Tk mapeia para Ctrl+barra e não para Ctrl+A.
- Fazer a configuração de I.A. salva pelo diálogo persistir de fato: "Salvar" grava o bloco `llm.chat` e fecha o diálogo, e a gravação de preferências da interface deixa de sobrescrever o bloco `llm`.

### [llm-core](openspec/changes/archive/2026-09-18-llm-core) Camada base reutilizável de LLM com porta `LLMPort`, adaptador liteLLM com presets de provedores, rate limiting por RPM, bloco `llm.chat` no `config.json`, exceções tipadas e diálogo de I.A. na sub-aba Documentos

#### Added

- Novo grupo opcional `[llm]` em `pyproject.toml` com `litellm` (`pip install flowscope[llm]`).
- Novo domínio `domain/llm/`: porta genérica `LLMPort` (completion) e hierarquia de exceções (`LLMUnavailableError`, `LLMConfigurationError`, `LLMCommunicationError`, `LLMProviderError`, `LLMRateLimitError`).
- Nova infraestrutura `infrastructure/llm/`: presets de provedores (`none`, `openai`, `gemini`, `copilot`, `claude`, `deepseek`, `ollama`, `custom`), adaptador `LiteLLMChatAdapter` via `litellm.completion()` com `custom_llm_provider`, rate limiter configurável (RPM, default 5), load/save de config, detecção das dependências `[llm]` e factory `create_llm_provider(config)`.
- Bloco `llm.chat` no `~/.flowscope/config.json` com `provider` (default `none`), `api_url`, `model`, `api_key` e `rpm`, preservando as demais preferências do arquivo.
- Diálogo de configuração de LLM na GUI (modal e não redimensionável) com dropdown de presets, `api_url`, `model`, chave de API mascarada, RPM, botão "Salvar" e botão "Testar"; as falhas do teste também são registradas em log (nível aviso, no logger `flowscope`, sem a chave de API).
- Botão "I.A." na barra da sub-aba "Documentos", logo após "Abrir documento", que abre o diálogo de configuração e segue o bloqueio global dos demais botões durante as cargas de dados.

#### Changed

- O executável do PyInstaller passa a embutir o liteLLM: o alvo `build` instala `[llm]` e a especificação coleta submódulos e arquivos de dados do litellm, incluindo o pacote de plugins `tiktoken_ext.openai_public`, garantindo os recursos de I.A. em máquinas que rodam apenas o binário (sem Python/pip).
- README passa a documentar a instalação `pip install flowscope[llm]`.
- A change `llm-chat` passa a herdar `llm-core` (remove a duplicação de cliente de chat, config e diálogo, mantendo embeddings, VectorStore, RAG e o ChatPanel).

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.1.0

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
