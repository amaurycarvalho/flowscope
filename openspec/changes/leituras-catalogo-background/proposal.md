## Why

Além do download da B3, restam leituras de disco na thread do Tk que podem bloquear a interface em caches grandes: a varredura do catálogo de documentos ao ativar a sub-aba (`DocumentTreePanel.update`), a leitura do índice e a checagem de existência de HTML das notícias (`NoticiasPanel.update`) e a leitura do cache histórico na "Evolução dos Fundamentos" (`_update_fundamental_evolution`). Com o `BackgroundManager` da fatia A, essas leituras podem sair da thread do Tk e exibir estado de carregamento, mantendo o restante da interface responsivo.

## What Changes

- Move para o `BackgroundManager` a leitura do catálogo da sub-aba "Documentos" (varredura de raízes + índice de resumos/textos) e a remontagem da árvore passa a ocorrer por evento na thread do Tk, com estado de carregamento.
- Move para o manager a leitura do índice de notícias e a checagem de existência de HTML na sub-aba "Notícias", com remontagem por evento e estado de carregamento.
- Move para o manager a leitura do cache histórico da sub-aba "Evolução dos Fundamentos".
- Preserva o comportamento observável: leitura apenas do cache local (sem B3), estado vazio em cache frio, ordenação, filtragem de entradas sem HTML e cancelamento/descarte de leituras obsoletas quando o ticker muda.
- As leituras usam política `latest_wins` no grupo do painel, de modo que trocar de ticker descarta a leitura anterior.

## Capabilities

### New Capabilities
<!-- Nenhuma: o mecanismo é o `background-jobs` da fatia A. -->

### Modified Capabilities
- `documentos-ticker-panel`: a ativação passa a ler o catálogo fora da thread da interface, com estado de carregamento e remontagem por evento.
- `noticias-panel`: a montagem a partir do cache local passa a ocorrer fora da thread da interface, com estado de carregamento.
- `fundamental-evolution-panel`: a leitura do cache histórico passa a ocorrer fora da thread da interface, com estado de carregamento.

## Impact

- `src/flowscope/presentation/gui/charts/document_tree_panel.py` (`update`, `mostrar_carregando`) e `document_flow_mixin.py`.
- `src/flowscope/presentation/gui/charts/noticias_panel.py` (`update`).
- `src/flowscope/presentation/gui/app_actions.py` (`_update_fundamental_evolution`).
- Deltas em `openspec/specs/documentos-ticker-panel/spec.md`, `openspec/specs/noticias-panel/spec.md` e `openspec/specs/fundamental-evolution-panel/spec.md`.
- Reutiliza `ConsultarCatalogoUseCase`/`ConsultarCatalogoNoticiasUseCase` e o cache histórico como trabalho submetido; sem mudança em `application` e `infrastructure`. Depende da fatia A.
