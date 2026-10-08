## Why

A posição do divisor horizontal (abas à esquerda / watch list à direita) não é persistida: o bloco de salvamento aborta quando `_left_pw.sash_coord(0)` levanta `TclError` (a `_left_pw` tem um único painel), antes de atribuir `sash_positions`, e a restauração exige 4 valores com índice trocado — o arquivo mantém um valor antigo e o divisor volta sempre ao mesmo lugar. Além disso, o cursor de espera pode ficar preso: um widget criado após a entrada no estado ocupado recebe `watch` pelo hook de `<Motion>` e nunca é restaurado, e um `exit` perdido deixa o hook reafirmando `watch` indefinidamente.

## What Changes

- Persistir a **largura do painel direito** (ticker + orientação) em vez da coordenada absoluta x do sash, restaurando-a após a janela estar mapeada/no tamanho final, com clamp para não colapsar o painel esquerdo. Descartar o formato legado de 4 valores e remover o tratamento morto da `_left_pw`.
- Cursor ocupado sem vazamentos: ao reafirmar `watch` sobre o widget sob o ponteiro, registrar antes o cursor de repouso dele se ainda não estiver rastreado; no mesmo hook, consultar se há operação/job ativo e, quando não houver, limpar o estado em vez de forçar `watch` (auto-limpeza). Substituir `unbind_all("<Motion>")` por remoção do binding específico para não clobberar outros bindings globais.
- Escopo de cursor: diálogos/`Toplevel` são tratados apenas pelo hover (sem forçar todos os widgets internos); managers locais (chat, pré-visualização de documentos e resumos de notícias) permanecem fora do cursor de espera global, como hoje.

## Capabilities

### New Capabilities
<!-- nenhuma capability nova -->

### Modified Capabilities
- `ui-polish`: a preferência de layout passa a persistir e restaurar a largura do painel direito do divisor principal, de forma robusta a mudanças de resolução, em vez da posição absoluta (e do divisor vertical morto).
- `loading-state-management`: o requisito do cursor de espera ganha garantia explícita de não vazamento para widgets criados durante o estado ocupado e auto-limpeza do `watch` durante o movimento quando não há operação ativa.

## Impact

- Código: `presentation/gui/app.py` (salvamento em `_on_close`), `app_layout.py` (construção/agendamento da restauração), `app_tab_layout.py` (`_restore_sashes`), `app_status.py` (máquina de cursor), possivelmente `presenter.py` (acessor público de "ocupado"). A `_left_pw` de painel único deve ser removida ou neutralizada.
- Dados: `~/.flowscope/config.json`, chave `sash_positions` — mudança de formato (largura, não posição), com descarte do valor legado incompatível.
- Testes: `tests/test_presentation/test_button_state.py` (cursor) e novos testes de persistência/restauração do divisor; testes sem display continuam pulando via `needs_display`.
