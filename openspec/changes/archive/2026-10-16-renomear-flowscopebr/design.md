## Context

Ver `proposal.md` — Why. O literal "FlowScope" aparece tanto em textos visíveis quanto em identificadores internos (nomes de classes/módulos, docstrings, `USER_AGENT`, o caminho de conhecimento `/flowscope`). A mudança precisa separar as duas categorias para renomear apenas o visível. A renomeação já começou parcialmente: `about_panel.APRESENTACAO` já usa "FlowScopeBR".

## Goals / Non-Goals

**Goals:**
- Renomear para "FlowScopeBR" todos os textos exibidos ao usuário (GUI, chat, CLI, atalho, docs atuais).
- Atualizar o requisito de `gui-about` que fixa o formato `FlowScope vX.Y.Z`.

**Non-Goals:**
- Renomear classes, módulos, funções, variáveis ou docstrings internas.
- Alterar `USER_AGENT = "FlowScope/1.0"`, o node `/flowscope`, o diretório `~/.flowscope`, o repositório, o nome do pacote/binário `flowscope`, nem o nome/`Exec` do arquivo `.desktop`.
- Renomear a prosa das specs OpenSpec (apenas o requisito de `gui-about` muda).
- Renomear `docs/rfcs/`, `docs/adrs/` e `CHANGELOG-ARCHIVE.md`.

## Decisions

- **D1 — Taxonomia allow/deny.** Renomear apenas: `app_constants.TITLE_PREFIX`; nome+versão no `about_panel`; textos de "Sobre"/"Chat AI" em `app_tabs`; `PERSONA` (`manifesto.py`), `SYSTEM_PROMPT` (`consultar.py`), `_CABECALHO_SOBRE` e o cabeçalho do manifesto (`conhecimento.py`/`manifesto.py`); cabeçalho e string de `--mcp` em `cli.py`; campo `Name=` em `shortcuts.py`; `README.md`, `docs/PRD.md`, `docs/misc/*.md`. Tudo o mais fica intacto. Alternativa considerada: substituição global de "FlowScope" — descartada por atingir identificadores e caminhos.
- **D2 — Sem novo símbolo.** Aplicar substituição literal nas strings fixas já existentes, sem introduzir constante `APP_NAME` compartilhada entre camadas. Alternativa considerada: constante única em `flowscope/__init__.py` — descartada para manter o escopo mínimo; pode ser adotada depois se houver mais pontos de exibição.
- **D3 — Specs.** Manter a prosa das specs como está e registrar apenas a mudança do nome exibido via delta de `gui-about`. Alternativa considerada: renomear as 41 ocorrências nas specs — descartada por churn sem ganho de contrato.

## Risks / Trade-offs

- [Substituição cega atinge identificadores (`FlowScopeGUI`, `flowscope.`)] → Aplicar apenas nas strings visíveis da allow-list (D1) e revisar o diff.
- [`USER_AGENT` e node `/flowscope` renomeados por engano] → Deny-list explícita nas Non-Goals; conferir esses pontos no diff.
- [Testes que assertam strings antigas quebram] → Atualizar os testes relacionados (ex.: `test_about_panel`, cenário de `gui-about`) na mesma change.
- [README/docs trocam comandos `flowscope` junto com a prosa] → Mudar apenas o nome exibido; preservar comandos e caminhos que usam `flowscope`.
