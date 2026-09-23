## Why

O FlowScope não expõe suas informações institucionais (versão, data de lançamento, licença e apresentação) nem formas rápidas de acessar o repositório, o log da aplicação e eventuais atualizações. Hoje o usuário precisa consultar arquivos ou o terminal para obter esses dados, o que dificulta o suporte e a descoberta de novas versões.

## What Changes

- Nova aba de nível superior **"Sobre"**, posicionada imediatamente após **"Análise do Ticker"**, com conteúdo próprio com rolagem vertical. O painel de orientação à direita permanece inalterado.
- Conteúdo da aba, em ordem: ícone da aplicação; nome e versão (`FlowScope vX.Y.Z`); data de lançamento em formato ISO (`YYYY-MM-DD`); licença de software livre (GNU GPLv3); texto de apresentação derivado da descrição do `README.md`; botão para o repositório no GitHub; e botão para abrir o log da aplicação.
- Verificação automática de nova versão ao abrir a aba, no máximo **uma vez por sessão**, em background; quando houver versão mais recente, exibe aviso ao final do texto e um botão que abre a página da release no navegador padrão.
- Nova constante `__release_date__` em `src/flowscope/__init__.py`, e o fluxo de release passa a atualizá-la junto de `__version__`.
- Correção dos metadados de licença do `pyproject.toml` de MIT para `GPL-3.0-only`, com elevação do `setuptools` mínimo para 77 (PEP 639).

## Capabilities

### New Capabilities
- `gui-about`: Aba "Sobre" — posicionamento, layout rolável, informações institucionais, apresentação, link do repositório, acesso ao log e aviso de nova versão.
- `update-check`: Verificação de disponibilidade de nova versão no repositório GitHub, comparação semântica e URL da release para abertura no navegador.
- `release-versioning`: Constante de data de lançamento e sua atualização coordenada pelo fluxo de release.

### Modified Capabilities
- `project-scaffold`: metadados de licença do `pyproject.toml` (GPL-3.0-only) e versão mínima do `setuptools` (`>=77`).

## Impact

- `src/flowscope/__init__.py` — nova constante `__release_date__`.
- `src/flowscope/presentation/gui/` — registro e tratamento da aba "Sobre" (`app_layout.py`, `app_tab_layout.py`, `app_tab_actions.py`, `app_actions.py`), novos módulos de conteúdo do Sobre e de verificação de versão.
- `pyproject.toml` — campo `license` e `build-system.requires`.
- `.opencode/skills/release-version/SKILL.md` — passa a atualizar `__release_date__`.
- Novo uso de rede (GitHub Releases) e de `webbrowser`; sem novas dependências Python.
