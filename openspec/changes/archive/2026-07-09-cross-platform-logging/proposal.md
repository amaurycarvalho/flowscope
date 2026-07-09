## Why

Erros técnicos (HTTP 500, timeout, parse failure) são atualmente exibidos como mensagens genéricas na statusbar ou engolidos silenciosamente — o logging está desabilitado via `NullHandler`. Não há persistência de logs, impossibilitando diagnóstico pós-facto de falhas.

## What Changes

- Adicionar `LogPort` (Protocol) na camada application como porta de logging, seguindo o padrão Clean Architecture já usado com `DataRepository`
- Criar `PythonLogAdapter` na infraestrutura que implementa `LogPort` delegando para o módulo `logging` stdlib
- Configurar handlers nativos por plataforma no `main.py`: `SysLogHandler` (Linux/macOS), `NTEventLogHandler` (Windows), `RotatingFileHandler` (fallback universal em `~/.flowscope/logs/`)
- Injetar `LogPort` no `FlowScopeController` para logar erros técnicos antes de exibir mensagem na statusbar
- Atualizar `FlowScopePresenter` com `on_technical_error()` que exibe mensagem amigável orientando o usuário a consultar o log
- Remover `NullHandler` de `main.py`

## Capabilities

### New Capabilities
- `logging-platform`: Cross-platform technical error logging — erros são registrados no syslog (Linux), Event Log (Windows), ou arquivo rotativo (fallback universal), com mensagem guiada na statusbar para o usuário.

### Modified Capabilities
- *(nenhuma — requisitos de capabilities existentes não são alterados)*

## Impact

- `application/logging_port.py` — novo arquivo (~20 linhas): `LogEntry`, `LogReference` dataclasses e `LogPort` Protocol
- `infrastructure/logging/python_log_adapter.py` — novo arquivo (~30 linhas): adapter que implementa `LogPort` via stdlib logging
- `presentation/main.py` — configurar handlers de logging (remove `NullHandler`)
- `presentation/gui/controller.py` — receber `LogPort` no `__init__`, logar nos blocos `except Exception`
- `presentation/gui/presenter.py` — adicionar `on_technical_error()`
- `presentation/gui/app.py` — instanciar `PythonLogAdapter` e passar ao controller (`_wire_controller`)
- `infrastructure/b3/client.py` — já usa `logger`; passa a funcionar (não vai mais para o NullHandler)
- Nenhuma dependência externa nova (`pywin32` é opcional, só Windows)
- **Target**: Release 0.5.2
