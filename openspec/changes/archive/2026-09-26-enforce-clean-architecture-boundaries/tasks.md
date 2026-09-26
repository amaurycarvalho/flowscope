## 1. Portas de aplicação e adaptadores

- [x] 1.1 Criar a porta `ReleaseChecker` e `verificar_nova_versao` em `application` (usando `domain.version.is_newer`) com adaptador em `infrastructure/releases`; verificar com testes puros de versão mais nova, igual e ausente
- [x] 1.2 Criar `LLMConfigPort` em `application` (presets, load/save, deps, `create_provider`, `default_config`) com adaptador em `infrastructure/llm`; verificar com testes puros sobre um armazenamento fake
- [x] 1.3 Criar `ImageClipboardPort` e `ClipboardError` em `application` com adaptador em `infrastructure`; verificar com testes puros de sucesso e de falha traduzida

## 2. Apresentação consome apenas portas

- [x] 2.1 Injetar as portas pelo composition root (`app_wiring.py`/`app.py`) e atualizar `app_about_actions.py` para consumir `ReleaseChecker` sem importar `infrastructure`; verificar a aba "Sobre" com fakes
- [x] 2.2 Atualizar `app_actions.py` para consumir a porta de clipboard sem importar `infrastructure`; verificar a cópia de gráfico com fakes
- [x] 2.3 Atualizar `llm/config_dialog.py` para consumir `LLMConfigPort` (recebida em `app_tab_actions`) sem importar `infrastructure`; verificar o diálogo com fakes

## 3. Fechamento da fronteira

- [x] 3.1 Esvaziar `tests/architecture/allowlist.txt` e ajustar o teste de fronteira para exigir zero violações e zero entradas; verificar `find_violations() == set()`
- [x] 3.2 Criar/ajustar testes puros em `tests/test_application` e de apresentação com fakes, sem `DISPLAY`; verificar ausência de `DISPLAY` e cobertura das funções

## 4. Verificação final

- [x] 4.1 Rodar `make test` e `make complexity` e confirmar tudo verde com a allowlist vazia e o guardrail de fronteira incluído
