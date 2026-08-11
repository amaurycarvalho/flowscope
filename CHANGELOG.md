# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [core-implementation](openspec/changes/archive/2026-06-27-core-implementation) Fundação do projeto: Clean Architecture, ingestão de dados B3, indicadores de fluxo, CLI e GUI
- [default-gui-mode](openspec/changes/archive/2026-06-29-default-gui-mode) GUI passa a ser o modo padrão ao executar `flowscope` sem argumentos
- [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional
- [documentos-relevantes](openspec/changes/documentos-relevantes) Extração de documentos relevantes (PDFs) da B3 via GetReportsRelevants com cache e integração com VectorStore
- [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões
- [especificacoes-vs-implementacao-diffs](openspec/changes/archive/2026-06-27-especificacoes-vs-implementacao-diffs) Auditoria comparativa entre especificações e implementação com correções de docs e specs
- [fix-verification-issues](openspec/changes/archive/2026-06-27-fix-verification-issues) Correções de issues de verificação no CLI, GUI e charts (export com filtro, quiver, auto-refresh, exit code)
- [idiv-portfolio-default-filter](openspec/changes/archive/2026-06-27-idiv-portfolio-default-filter) Pré-carregamento da carteira IDIV como filtro padrão com cache TTL e filtro de segmento CASH
- [informe-mensal](openspec/changes/informe-mensal) Extração de Informes Mensais Estruturados (type=40) da B3 com entidades próprias e parsing multi-tabela
- [llm-chat](openspec/changes/llm-chat) Assistente RAG integrado à GUI com VectorStore SQLite, embeddings e chat LLM via liteLLM
- [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado com gauge de concentração, card informativo e timeline AFT
- [redesign-amplitude-panel](openspec/changes/archive/2026-07-01-redesign-amplitude-panel) Painel Amplitude de Preço redesenhado com timeline, range% histórico e gauges de eficiência e CLV
- [regulacao-mercado](openspec/changes/regulacao-mercado) Dados regulatórios e de mercado da B3 (fatos relevantes, notícias, censuras, condições excepcionais) integrados ao llm-chat
- [replace-buttons-with-icons](openspec/changes/archive/2026-06-28-replace-buttons-with-icons) Botões da top bar e sidebar substituídos por ícones e índices IBOV/IDIV/IFIX movidos para a linha de ações
- [structured-earnings](openspec/changes/structured-earnings) Extração de rendimentos e amortizações de FIIs via API B3 com entidades de domínio, cache e CLI
- [ui-ajustes-filtro-statusbar](openspec/changes/archive/2026-06-27-ui-ajustes-filtro-statusbar) Barra de status reposicionada e filtro de tickers alterado de automático para manual via botão Filtrar
- [ui-polish-and-usability](openspec/changes/archive/2026-06-27-ui-polish-and-usability) Passo de polimento da UI com ícone, loading guard, atalhos, tooltips, statusbar e persistência de layout
- [wait-cursor-refactor](openspec/changes/archive/2026-06-29-wait-cursor-refactor) Cursor watch adicionado a operações síncronas de refresh de painel e cópia de gráfico

## [0.7.0] — 2026-08-11

### [kill-mutation-survivors](openspec/changes/archive/2026-08-11-kill-mutation-survivors) Eleva o mutation score de 61.95% para >= 80% com novos testes unitários, asserts mais fortes e padrões do_not_mutate para os 886 mutantes sobreviventes

#### Added
- Novos testes unitários para funções/métodos que hoje não possuem cobertura de teste, focando nos 886 mutantes sobreviventes agrupados por módulo
- Padrões adicionados ao `do_not_mutate_patterns` do mutmut para mutações impossíveis de matar com testes unitários

#### Changed
- Fortalecimento de asserts em testes existentes que cobrem o código mas não são sensíveis o suficiente para detectar mutações (ex: mocks que validam apenas que a chamada ocorreu, sem verificar argumentos específicos)

### [log-timestamps](openspec/changes/archive/2026-08-11-log-timestamps) Logs passam a incluir timestamp (data/hora) via basicConfig configurado globalmente no main.py

#### Changed
- `logging.basicConfig` configurado em `src/flowscope/presentation/main.py` com formato de log que inclui timestamp
- Timestamps em formato ISO 8601 com milissegundos (ex.: `2026-08-11 14:23:07,120`)
- Formato aplicado globalmente a todos os handlers via `basicConfig` (um único `format` para todo o processo)
- Testes de logging ajustados para o novo formato quando asserem na saída de log

### [quality-gate-ci](openspec/changes/archive/2026-08-11-quality-gate-ci) Implementa o quality gate completo da RFC-005 (lint, complexidade, duplicação, cobertura, mutação, segurança) e acopla-o ao pipeline de release

#### Changed
- `ci.yml` reescrito como workflow reutilizável (`workflow_call`) com 3 jobs encadeados (lint → test → quality-gate), usando Python 3.12 e 3.13
- `release.yml` ganha job `ci` que invoca o workflow reutilizável antes do build; jobs `build` e `release` passam a depender de `ci`
- Makefile com 30+ targets de qualidade: `venv`, `install-quality-tools`, `quality-gate`, `complexity`, `duplication`, `mutation-*`, `security*`
- `pyproject.toml` com dependências `dev` e `quality` e configurações `[tool.ruff]`, `[tool.pytest.ini_options]`, `[tool.mutmut]`, `[tool.coverage]`
- RFC-005 corrigida (target `build` como PyInstaller, remoção de menções a `build-wheel.yml`)

#### Added
- Scripts `scripts/quality_gate.py`, `scripts/complexity_metrics.py`, `scripts/check-mutation-score.py`
- Entradas `.gitignore` para `mutants/` e `.mutmut-cache`

### [remember-last-tickers](openspec/changes/archive/2026-08-11-remember-last-tickers) Persiste e restaura a última lista de tickers usada em `~/.flowscope/config.json`

#### Added
- Persistência da última lista de tickers em `~/.flowscope/config.json` sob a chave `last_tickers`
- Restauração da lista salva no startup sem disparar download de dados
- Testes unitários para `load_preferences` / `save_preferences` cobrindo o round-trip de `last_tickers`

#### Changed
- Salvamento da lista ao fechar o app (`_on_close`)
- Persistência da lista também quando muda via load-from-file / troca de diretório, sobrevivendo a crashes e saídas não-graciosas
- Contador de tickers no startup mostra `Tickers (N)` em vez de `Exibindo 0 de N ativos`

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.7.0...HEAD

[0.7.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.7.0
See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
