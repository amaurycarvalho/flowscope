## 1. GUI

- [ ] 1.1 Atualizar `TITLE_PREFIX` em `app_constants.py` para exibir "FlowScopeBR v{__version__}"; verificar com `python -c "from flowscope.presentation.gui.app_constants import TITLE_PREFIX; print(TITLE_PREFIX)"`
- [ ] 1.2 Atualizar o nome+versão na aba "Sobre" (`about_panel.py`) para `FlowScopeBR v{__version__}`; verificar no teste `tests/test_presentation/test_about_panel.py`
- [ ] 1.3 Atualizar os textos de "Sobre" e "Chat AI" em `app_tabs.py` (`TAB_CONTENT`); verificar que não resta "FlowScope" nesses textos
- [ ] 1.4 Atualizar os testes que assertam as strings antigas (ex.: `test_about_panel.py`, cenário de `gui-about`) e rodar os testes de apresentação relacionados

## 2. Chat / LLM

- [ ] 2.1 Atualizar `PERSONA` (`manifesto.py`), `SYSTEM_PROMPT` (`consultar.py`), `_CABECALHO_SOBRE`/cabeçalho do manifesto (`conhecimento.py`, `manifesto.py`) para "FlowScopeBR"; verificar por inspeção
- [ ] 2.2 Rodar os testes de chat relacionados (`tests/test_presentation/test_chat_*.py`, `tests/test_application/test_chat_*.py`) e garantir que passam

## 3. CLI e atalho de desktop

- [ ] 3.1 Atualizar o cabeçalho de execução e a string do `--mcp` em `cli.py` para "FlowScopeBR"; verificar executando a CLI e conferindo a saída/`--help`
- [ ] 3.2 Atualizar o campo `Name=` em `shortcuts.py` para "FlowScopeBR" mantendo `Exec`, `Icon` e o nome do arquivo `flowscope.desktop`; verificar no teste de atalho
- [ ] 3.3 Rodar os testes relacionados de CLI e atalho (`tests/test_presentation/test_cli*.py`, testes de `shortcuts`)

## 4. Docs atuais

- [ ] 4.1 Atualizar `README.md`, `docs/PRD.md` e `docs/misc/*.md` para "FlowScopeBR" apenas na prosa; preservar comandos/caminhos que usam `flowscope`; verificar por inspeção

## 5. Verificação da change

- [ ] 5.1 Rodar `make lint` e garantir ausência de erros
- [ ] 5.2 Rodar `make complexity` e garantir ausência de regressões
- [ ] 5.3 Conferir no diff que `USER_AGENT`, node `/flowscope`, nomes de classe/módulo, docstrings, `~/.flowscope`, `docs/rfcs`, `docs/adrs` e `CHANGELOG-ARCHIVE.md` permanecem inalterados
- [ ] 5.4 (manual, usuário) Rodar `make test`/`make quality-gate` apenas se considerar necessário por precaução
