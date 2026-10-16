## Why

O nome exibido "FlowScope" colide com duas soluções já existentes de mesmo nome (`flowscope.com` e `flowscope.net`), o que gera ambiguidade para quem procura o projeto. Distinguir o produto exibindo "FlowScopeBR" resolve a colisão sem custo técnico, já que a mudança é puramente textual.

## What Changes

- Renomear "FlowScope" para "FlowScopeBR" em todos os **textos visíveis** da aplicação:
  - título da janela;
  - aba "Sobre" (nome+versão e textos de orientação);
  - textos renderizados no chat de IA e os *system prompts* enviados à LLM;
  - saída e ajuda da CLI;
  - campo `Name=` do atalho de desktop (Linux);
  - `README.md` e docs atuais (`docs/PRD.md`, `docs/misc/*.md`).
- O formato de nome+versão exibido na aba "Sobre" passa de `FlowScope vX.Y.Z` para `FlowScopeBR vX.Y.Z`.
- Preservar, deliberadamente, tudo que não é texto visível: nomes de classes, módulos, funções e variáveis; docstrings internas; o literal `USER_AGENT = "FlowScope/1.0"`; o caminho de conhecimento `/flowscope`; nomes de pastas (incluindo `~/.flowscope` e o repositório); o nome do pacote/binário `flowscope`; e os registros históricos `docs/rfcs/`, `docs/adrs/` e `CHANGELOG-ARCHIVE.md`.
- A prosa das specs OpenSpec que apenas descreve o produto NÃO é renomeada; apenas o requisito que fixa o nome exibido é atualizado (ver Capabilities).

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `gui-about`: o formato do nome exibido na aba "Sobre" muda de `FlowScope vX.Y.Z` para `FlowScopeBR vX.Y.Z` (requisito e cenário de valores de versão).

## Impact

- Apresentação GUI: `src/flowscope/presentation/gui/app_constants.py` (`TITLE_PREFIX`), `widgets/about_panel.py`, `app_tabs.py`.
- Chat/LLM: `src/flowscope/application/chat/manifesto.py`, `consultar.py`, `conhecimento.py`.
- CLI: `src/flowscope/presentation/cli.py` (cabeçalho e help).
- Atalho de desktop: `src/flowscope/presentation/shortcuts.py` (`Name=`).
- Docs: `README.md`, `docs/PRD.md`, `docs/misc/*.md`.
- Sem mudança de comportamento funcional, de contratos públicos ou de dependências; alteração estritamente textual e exibida.
