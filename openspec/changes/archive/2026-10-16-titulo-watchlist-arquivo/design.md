## Context

Ver `proposal.md` — Why. O título é fixado uma única vez em `app.py:110` via `TITLE_PREFIX` (`app_constants.py`). O `TickerList` já expõe callbacks, mas sem o caminho do arquivo: `on_load` não recebe argumentos, `on_dir_changed(dir)` recebe só o diretório (disparado no load e no save), `on_change` é a mudança de **seleção** (filtro) e `on_data_needed` é disparado em `_restore_from_snapshot_edit` quando o **conteúdo** muda (`new_set != old_set`). A persistência usa `~/.flowscope/config.json` com `last_tickers`/`last_ticker_dir` (`DEFAULT_CONFIG` em `app.py`, `_on_ticker_dir_changed`, `_on_close`).

## Goals / Non-Goals

**Goals:**
- Exibir no título o nome-base do watchlist e o asterisco de alteração não salva.
- Persistir o caminho completo do arquivo de origem e restaurar o nome no startup.

**Non-Goals:**
- Não alterar o contador de tickers nem o rótulo de data.
- Não persistir o nome de índice (IBOV/IDIV/IFIX).
- Não marcar o asterisco por mudança de seleção/filtro.

## Decisions

- **D1 — Novo callback `on_file_changed(path)`.** O `TickerList` chama `on_file_changed(Path(path))` em `_load` e `_save`, expondo o caminho completo. Alternativa considerada: reaproveitar `on_dir_changed` — descartada porque ele só leva o diretório e é disparado em load e save indistintamente.
- **D2 — Sinal de edição de conteúdo.** Adicionar `on_content_changed` no ponto onde o conteúdo já é detectado como alterado (`_restore_from_snapshot_edit`, quando `new_set != old_set`), ao lado de `on_data_needed`. Alternativa considerada: usar `on_change` — descartada porque ele representa seleção/filtro, que não deve marcar alteração.
- **D3 — Estado e composição no nível da app.** Manter em `FlowScopeGUI` um `_watchlist_file: Path | None`, um `_watchlist_dirty: bool` e um `_index_name: str | None`; um método `_update_window_title()` compõe `TITLE_PREFIX + " — " + (basename(arquivo) ou _index_name ou "Nova lista.txt") + ("*" se dirty)`. Chamado no startup, load, save, clique de índice e edição de conteúdo.
- **D4 — Prefixo único.** Compor a partir de `TITLE_PREFIX` (definido pela change `renomear-flowscopebr`) em vez de duplicar o literal, evitando divergência entre as duas changes.
- **D5 — Índice não persiste.** `on_index_clicked` zera `_watchlist_file` e `_watchlist_dirty`, define `_index_name = "<ÍNDICE>.txt"` e atualiza o título; não grava a chave no config. Carregar/salvar zera `_index_name`.
- **D6 — Persistência aditiva.** Adicionar `last_ticker_file` ao `DEFAULT_CONFIG`; gravar no callback `on_file_changed` (e garantir o valor no `_on_close`); ler no startup e aplicar o basename ao título. Ausência da chave é tratada como `None`.

## Risks / Trade-offs

- [Edição via duplo clique/menu de contexto não passar pelo ponto de detecção] → Cobrir esses fluxos nos testes; se necessário, acionar `on_content_changed` também neles.
- [Confundir `on_data_needed` (recarrega dados) com "sujo"] → Manter sinais separados (D2) e testar que selecionar/filtrar não marca asterisco.
- [Config antiga sem `last_ticker_file`] → Tratar ausência como `None` (D6) e não falhar no startup.
- [Dependência do prefixo com `renomear-flowscopebr`] → Compor via `TITLE_PREFIX` (D4); se aplicada sozinha, o título usa o prefixo vigente.
