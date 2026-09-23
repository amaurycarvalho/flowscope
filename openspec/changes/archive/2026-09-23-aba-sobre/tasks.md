## 1. Versão e licença (base)

- [x] 1.1 Adicionar `__release_date__ = "2026-09-18"` em `src/flowscope/__init__.py`; verificar com `python -c "import flowscope; print(flowscope.__release_date__)"` que a constante é exposta em formato ISO
- [x] 1.2 Corrigir `pyproject.toml`: trocar `license = { text = "MIT" }` por `license = "GPL-3.0-only"` e elevar `build-system.requires` para `setuptools>=77`; verificar que `pip install -e .` conclui sem erro de metadados de licença
- [x] 1.3 Atualizar `.opencode/skills/release-version/SKILL.md` com um passo que grava `__release_date__` junto de `__version__` e incluir a data na verificação de consistência; revisar o arquivo para confirmar que as três versões e a data são citadas

## 2. Lógica de versão e cliente de releases

- [x] 2.1 Criar `src/flowscope/domain/version.py` com `parse_version` e `is_newer` (tolerantes a prefixo `v` e segmentos inválidos); verificar com testes unitários cobrindo mais nova, igual/anterior e inválida
- [x] 2.2 Criar o cliente de releases em `src/flowscope/infrastructure/releases/` que segue o redirect de `/releases/latest`, extrai a tag do caminho final e trata timeout/sem-tag como `None`; verificar com testes usando `responses`
- [x] 2.3 Confirmar que os novos módulos estão fora de `presentation/gui/` e entram na cobertura; verificar com `make test` que a cobertura permanece `>= 85%`

## 3. Aba "Sobre"

- [x] 3.1 Criar `src/flowscope/presentation/gui/widgets/about_panel.py` com frame rolável vertical, ícone (`flowscope.png`), `FlowScope vX.Y.Z`, data ISO, licença, texto de apresentação e botões de repositório e log; verificar a construção do painel e a ordem das informações
- [x] 3.2 Extrair o caminho `~/.flowscope/logs/flowscope.log` para uma constante compartilhada e usá-la em `main.py` e no painel; verificar que o botão abre o log no app padrão e que a ausência do arquivo informa a barra de status
- [x] 3.3 Registrar a aba "Sobre" no `_main_notebook` imediatamente após "Análise do Ticker"; verificar o posicionamento ao abrir a aplicação
- [x] 3.4 Tratar "Sobre" em `_current_tabs`, `_resolve_chart`/`_resolve_current_chart`, `_restore_tabs` e `_on_tab_changed`, sem resolver gráfico/sub-aba nem alterar o painel de orientação; verificar com testes de apresentação para troca e restauração da aba

## 4. Verificação de nova versão

- [x] 4.1 Disparar a verificação ao abrir a aba, em thread daemon com publicação via `self.after`, memoizada uma vez por sessão; verificar que a interface não bloqueia e que a segunda abertura não refaz a requisição
- [x] 4.2 Exibir ao final do conteúdo o aviso "Nova versão vX.Y.Z disponível" e o botão que abre a URL da release com `webbrowser`; verificar que, sem novidade ou em falha, nenhum aviso é exibido

## 5. Qualidade

- [x] 5.1 Executar `make lint test` e corrigir eventuais erros de lint e falhas de teste
- [x] 5.2 Executar `make quality-gate` e corrigir complexidade, duplicação, mutação e segurança até o gate passar
