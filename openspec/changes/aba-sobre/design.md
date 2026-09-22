## Context

A navegação principal é um `ttk.Notebook` (`_main_notebook`) com as abas "Análise Geral" e "Análise do Ticker" (`app_layout.py:137`, `app_tab_layout.py:65`). Vários caminhos assumem que toda aba de nível superior que não seja "Análise Geral" possui `_ticker_notebook`: `_current_tabs()` (`app_tab_actions.py:16`), `_resolve_chart()`/`_resolve_current_chart()` (`app_actions.py:83`) e `_restore_tabs()` (`app_tab_layout.py:107`). Uma terceira aba de nível superior exige tratamento explícito nesses pontos.

A versão é uma fonte única em `src/flowscope/__init__.py` (`__version__`), já usada por `app_constants.TITLE_PREFIX`; não há data de lançamento em runtime e o `CHANGELOG.md` não é empacotado no binário (`flowscope.spec` inclui apenas `src/flowscope/icons`). O log fica em `~/.flowscope/logs/flowscope.log` (`main.py:124`) e a abertura de arquivos no app padrão já existe em `document_actions.py:9`. `requests` é dependência existente e `responses` é dependência de desenvolvimento para simular HTTP; `webbrowser` (stdlib) ainda não é usado.

O `pyproject.toml` declara `license = { text = "MIT" }`, divergente do arquivo `LICENSE` (GNU GPL v3). O `build-system` exige `setuptools>=64`; a expressão SPDX no campo `license` (PEP 639) requer `setuptools>=77`.

## Goals / Non-Goals

**Goals:**

- Adicionar a aba "Sobre" sem perturbar a resolução de gráficos/sub-abas nem o painel de orientação à direita.
- Expor versão, data, licença, apresentação, repositório e log de forma legível e ordenada.
- Verificar nova versão no GitHub uma vez por sessão, sem bloquear a interface e sem depender de API autenticada.
- Manter a lógica de comparação de versões testável fora da GUI.
- Alinhar a licença declarada à licença real e à documentação.

**Non-Goals:**

- Não criar um visualizador de log dentro da aplicação (o log é aberto no app padrão).
- Não implementar download/atualização automática; apenas avisar e abrir a página da release.
- Não alterar o painel de orientação à direita para a aba "Sobre".
- Não reestruturar a navegação existente nem mover abas.

## Decisions

### 1. Aba de nível superior com conteúdo rolável próprio

A aba "Sobre" é adicionada ao `_main_notebook` após "Análise do Ticker". O conteúdo é um `Frame` próprio dentro de um `Canvas` com `Scrollbar` vertical (mousewheel com suporte a Linux `Button-4/5` e demais plataformas). O painel direito permanece como está.

*Alternativas:* usar o `OrientationPanel` à direita (rejeitado — não comporta ícone e botões e o pedido é manter o painel intocado); criar sub-aba dentro de "Análise Geral" (rejeitado — o pedido é uma aba após "Análise do Ticker").

### 2. Tratamento dedicado de "Sobre" no ciclo de troca/restauração de abas

`_current_tabs()` passa a reconhecer "Sobre" e a troca de aba retorna cedo para ela, sem resolver gráfico nem atualizar o `OrientationPanel`; apenas persiste `last_tab`. `_restore_tabs()` seleciona "Sobre" sem tocar nos sub-notebooks. O bloqueio global de botões (`app_status.py:82`) já atua sobre uma lista fixa e não afeta os botões do Sobre.

*Alternativa:* deixar a resolução atual (rejeitada — resolveria "Sobre" como sub-aba de ticker, atualizaria o painel direito e poderia persistir `last_subtab` indevidamente).

### 3. Conteúdo institucional embutido como constante

O ícone vem de `flowscope.png` via `_load_icon`; versão de `flowscope.__version__`; data de `flowscope.__release_date__` (ISO); a apresentação é um texto curado derivado da seção de descrição do `README.md`, mantido em uma constante com comentário apontando a origem. O link do repositório usa `https://github.com/amaurycarvalho/flowscope`.

*Alternativas:* empacotar e renderizar o `README.md` (rejeitado — exigiria incluir o arquivo no `flowscope.spec` e renderizar Markdown no Tk, com custo desproporcional).

### 4. Data de lançamento como constante no pacote

Adicionar `__release_date__ = "2026-09-18"` em `src/flowscope/__init__.py`, no formato ISO. O fluxo de release (skill `release-version`) passa a atualizá-la junto de `__version__`.

*Alternativas:* parsear `CHANGELOG.md` em runtime (rejeitado — não empacotado no binário); derivar da tag git (rejeitado — indisponível no binário).

### 5. Verificação de versão sem API, uma vez por sessão

A checagem usa `requests.get("https://github.com/amaurycarvalho/flowscope/releases/latest", allow_redirects=True, timeout=~5s)` e extrai a tag do caminho final (`/releases/tag/vX.Y.Z`). Executa em thread daemon e publica o resultado na thread do Tk via `self.after(...)`. O resultado é memoizado (`self._update_checked`), então só ocorre uma verificação por sessão. Falhas são silenciosas (opcionalmente `logging.warning`).

*Alternativas:* API `api.github.com/repos/.../releases/latest` (rejeitada — limite de 60 req/h por IP e JSON desnecessário); verificar a cada abertura da aba (rejeitada — chamadas repetidas e instabilidade visual).

### 6. Separação em camadas para permitir testes

- `src/flowscope/domain/version.py`: funções puras `parse_version` e `is_newer` (tolerantes a prefixo `v` e segmentos inválidos), cobertas por testes unitários.
- `src/flowscope/infrastructure/releases/`: cliente HTTP que retorna `(versao, url)` ou `None`, testável com `responses`.
- `src/flowscope/presentation/gui/widgets/about_panel.py`: construção do conteúdo e botões.
- Ligação da thread e publicação do aviso no mixin de ações da GUI.

*Alternativa:* concentrar tudo em `presentation/gui/*` (rejeitado — a pasta é excluída de cobertura e mutação, deixando a comparação de versões sem verificação).

### 7. Abertura de URLs e do log

URLs (repositório e release) são abertas com `webbrowser.open` (stdlib, multiplataforma). O log reutiliza `abrir_no_aplicativo` (`document_actions.py:9`), com o caminho do log extraído para uma constante compartilhada, evitando duplicação com `main.py:124`. Se o arquivo não existir, a barra de status informa a indisponibilidade.

*Alternativas:* usar `xdg-open`/`open` diretamente para URLs (rejeitado — `webbrowser` já resolve o navegador padrão); visualizador de log interno (rejeitado — fora de escopo).

### 8. Correção de licença e do build system

Trocar `license = { text = "MIT" }` por `license = "GPL-3.0-only"` (expressão SPDX) e elevar `build-system.requires` para `setuptools>=77`. A escolha `-only` reflete um `LICENSE` com o texto base da GPLv3 sem declaração explícita de "ou versões posteriores".

*Alternativas:* manter a forma de tabela `{ text = "GPL-3.0-only" }` (rejeitada — deprecada); `GPL-3.0-or-later` (rejeitada — exigiria intenção explícita do projeto).

### 9. Atualização da skill de release

A skill `.opencode/skills/release-version/SKILL.md` ganha um passo que grava `__release_date__` com a data do lançamento e a etapa de verificação de consistência passa a cobri-la.

*Alternativa:* deixar a data como follow-up separado (rejeitada — a data ficaria desatualizada já no próximo release).

## Risks / Trade-offs

- [Chamada de rede automática ao abrir a aba] → apenas GET público ao GitHub, uma vez por sessão, sem payload; falhas silenciosas e timeout curto.
- [Bloqueio da interface durante a verificação] → thread daemon + `after`, jamais tocar widgets fora da thread do Tk.
- [Limite/instabilidade do endpoint de redirect] → tratar ausência de tag como "sem novidade"; opcionalmente registrar aviso no log.
- [Deriva entre o texto embutido e o README] → comentário junto à constante apontando a origem; revisão no release.
- [Deriva da `__release_date__`] → atualizar a skill de release no mesmo change e verificar consistência com o `CHANGELOG.md`.
- [Mousewheel do frame rolável varia por plataforma] → bind explícito para `<MouseWheel>` e `<Button-4/5>`.
- [PEP 639 exige setuptools recente] → elevar `build-system.requires` para `>=77`; ambiente atual já usa 82.
- [Regressão no tratamento de abas] → cenários de troca e restauração cobertos por specs e testes de apresentação.

## Migration Plan

1. Adicionar `__release_date__` e corrigir `pyproject.toml` (metadados; sem impacto em runtime).
2. Introduzir helpers de versão e o cliente de releases, com testes.
3. Construir a aba "Sobre" e ligá-la ao notebook, com o tratamento dedicado de abas.
4. Atualizar a skill `release-version`.
5. Rollback: reverter os commits; a preferência `last_tab` com valor "Sobre" em configs antigas é ignorada com segurança (a seleção falha e mantém a aba padrão).

## Open Questions

Nenhuma pendente; as decisões necessárias à especificação, à abordagem e ao fatiamento de tarefas foram resolvidas.
