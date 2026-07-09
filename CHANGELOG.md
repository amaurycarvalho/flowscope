# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional
- [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões
- [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado com gauge de concentração, card informativo e timeline AFT

## [0.5.2] — 2026-07-09

### [refactor-loading-architecture](openspec/changes/archive/2026-07-09-refactor-loading-architecture) Refatoração da arquitetura de carregamento com controller, presenter e guarda de operação

#### Added
- `LoadIndexPortfolioUseCase` — caso de uso em application layer para carregar carteiras de índices, eliminando a comunicação direta da GUI com o repositório
- `OperationGuard` — context manager que previne operações concorrentes, garantindo fluxos atômicos de botão-para-gráfico
- `FlowScopeController` — extrai a lógica de orquestração do `FlowScopeGUI` para uma classe separada na adapter layer
- `FlowScopePresenter` — extrai a lógica de atualização da UI do `FlowScopeGUI` para uma classe separada de apresentação

#### Changed
- `DataRepository` port ganha `get_index_tickers()` para fechar a lacuna atual do protocolo
- Todos os botões (índice, carregar, salvar, editar, selecionar todos, desmarcar todos) desabilitam durante o pipeline completo de portfólio + análise e restauram ao estado anterior ao finalizar

#### Removed
- `_fill_with_index()` e `_ensure_tickers()` do `FlowScopeGUI` — orquestração movida para o controller

### [add-presentation-layer-tests](openspec/changes/archive/2026-07-09-add-presentation-layer-tests) Testes unitários para a camada de apresentação com protocolo GUIView destacável

#### Added
- Testes unitários para `FlowScopeController.on_index_clicked()` e `on_load_data()` com dependências mockadas (sequência, erros, guard)
- Testes para `FlowScopeController._make_progress_cb()` — verifica advance/fail no callback
- Testes para `FlowScopePresenter` com mock de `GUIView` (operation_started/finished, progress, result, error, getters)
- Teste para `OperationGuard.is_busy` property
- Teste para `LoadIndexPortfolioUseCase.execute()` repassando `progress_callback`
- Testes Tkinter headless para `_disable_all_buttons()` e `_restore_all_buttons()` com snapshot de estados

#### Changed
- `FlowScopePresenter` passa a depender do protocolo `GUIView` em vez da classe concreta `FlowScopeGUI`
- `FlowScopeGUI` implementa o protocolo `GUIView` com 16 novos métodos públicos

### [testes-core](openspec/changes/archive/2026-07-09-testes-core) Testes para lacunas de cobertura nas camadas de application e infrastructure com mock HTTP

#### Added
- Testes para `AnalyzeTickersUseCase.execute()` com trades mockados (com/sem filtro de tickers, agregação diária)
- Testes para `OperationGuard.acquire()` nos estados livre e ocupado, incluindo reentrância
- Testes para `LoadIndexPortfolioUseCase.execute()` com índices válidos, inválidos, retorno vazio e sucesso
- Testes para `CacheManager.get_or_fetch()` com cache válido, expirado, ausente e falha no fetch
- Testes para `CacheManager.invalidate()` com chave existente e inexistente
- Testes para `B3Client.fetch_file()` com cache hit, cache miss (HTTP mockado) e callback de progresso
- Testes para `B3Client.fetch_portfolio()` com retorno de tickers, resposta vazia e falha HTTP
- Testes para `B3DataRepository.fetch_trades()` com parser sucesso, erro de parse e erro de download
- Testes para `B3Client._build_portfolio_url()` — verificação do encoding base64
- Dependência `responses` adicionada em `[project.optional-dependencies] dev` para mock HTTP
- `conftest.py` com fixtures padronizadas para B3Client, CacheManager e B3DataRepository mockados

### [cross-platform-logging](openspec/changes/archive/2026-07-09-cross-platform-logging) Logging técnico cross-platform com LogPort, PythonLogAdapter e handlers nativos (syslog/Event Log)

#### Added
- `LogPort` (Protocol) na camada application como porta de logging, seguindo o padrão Clean Architecture já usado com `DataRepository`
- `PythonLogAdapter` na infraestrutura que implementa `LogPort` delegando para o módulo `logging` stdlib

#### Changed
- Handlers de logging configurados por plataforma no `main.py`: `SysLogHandler` (Linux/macOS), `NTEventLogHandler` (Windows), `RotatingFileHandler` (fallback universal em `~/.flowscope/logs/`)
- `LogPort` injetado no `FlowScopeController` para logar erros técnicos antes de exibir mensagem na statusbar
- `FlowScopePresenter` ganha `on_technical_error()` que exibe mensagem amigável orientando o usuário a consultar o log

#### Removed
- `NullHandler` de `main.py` (substituído por configuração real de logging)

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.5.2...HEAD

[0.5.2]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.5.2
See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
