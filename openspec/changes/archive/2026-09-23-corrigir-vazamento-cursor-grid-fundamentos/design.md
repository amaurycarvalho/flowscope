## Context

Ver `proposal.md - Why`. O `StatusMixin` já centraliza o estado ocupado e a captura/restauração de cursores (`app_status.py`), e há uma normalização de cursores transitórios no snapshot. O defeito sobrevivente é um detalhe do Tk: quando o ponteiro está sobre o separador de uma coluna, `ttk::treeview::Motion` grava o cursor transitório via `ttk::setCursor`, e `widget.cget("cursor")` pode devolver o valor como **lista Tcl** — por exemplo `('sb_h_double_arrow',)`. O `str()` resultante (`"('sb_h_double_arrow',)"`) não casa com a lista de cursores transitórios, vira baseline inválido e, na restauração, `config` levanta `TclError` silenciosamente engolido, deixando o `"watch"` preso.

## Goals / Non-Goals

**Goals:**
- Normalizar de forma robusta o valor de `cget("cursor")` (string, lista ou tupla) antes de comparar com os cursores transitórios.
- Nunca deixar um widget preso em `"watch"` quando a restauração do baseline falhar.

**Non-Goals:**
- Ler ou manipular a variável interna compartilhada `ttk::treeview::State(userConfCursor)`.
- Alterar a política de estado ocupado no presenter, a API do protocolo `GUIView` ou o comportamento dos demais widgets.
- Recuperar um cursor customizado que o Tk esconda por trás do cursor transitório no instante da captura (nenhum grid da aplicação define cursor próprio).

## Decisions

### 1. Extrair o cursor de repouso num helper único

Criar `StatusMixin._cursor_de_repouso(widget)` que: lê `cget("cursor")`; se vier tupla/lista, usa o primeiro elemento; converte para string; retorna `""` para os cursores transitórios (`hresize`, `sb_h_double_arrow`, `sb_v_double_arrow`). Usar o mesmo helper no snapshot (`_set_wait_cursor`) e no hook de `<Motion>`.

- **Alternativa descartada**: comparar apenas `str(...)` — é exatamente o que falha quando o Tk devolve uma lista.
- **Alternativa descartada**: consultar `ttk::treeview::State(userConfCursor)` via Tcl — a variável é compartilhada por todos os `Treeview` e depender dela acopla o código a detalhes internos do toolkit.

### 2. Restauração com fallback para o cursor padrão

Em `_clear_wait_cursor`, se `widget.config(cursor=baseline)` levantar `TclError`, tentar `config(cursor="")`. Assim, mesmo um baseline inesperadamente inválido não deixa o widget com o cursor de espera.

- **Alternativa descartada**: continuar engolindo a exceção — é o que permite o vazamento.

## Investigação: atraso percebido no sincronismo de seleção grid1→grid2

Relato: ao clicar numa linha do grid congelado (grid1) a seleção correspondente no grid rolável (grid2) só aparece ~0,5 s depois; o inverso (grid2→grid1) parece imediato.

Análise com o painel real e o app completo (Tk 8.6, `DISPLAY` ativo), medindo o intervalo entre o clique e a seleção espelhada:

- O espelhamento de estado é **imediato**: `_espelhar_selecao` chama `selection_set` no grid destino de forma síncrona (`fundamental_table.py:235`), dentro do próprio handler do `<<TreeviewSelect>>` da árvore de origem. O evento virtual é enfileirado, mas é processado antes das tarefas ociosas de redesenho, no mesmo ciclo.
- `cProfile` sobre o `update()` posterior ao clique atribui **tempo ~0,000 s a todos os callbacks Python**; o custo está integralmente na chamada C do Tk (`_tkinter.tkapp.call`), ou seja, no redesenho.
- O custo é o **repaint do grid rolável** (28 colunas): escondendo `_frame_rolavel`, o espelhamento fixo→rolável cai de ~0,28 s para ~0,01 s. O grid congelado tem 2 colunas e repinta quase instantaneamente (~0,01 s).
- O código é **simétrico**: fixo→rolável mede ~0,23–0,32 s e rolável→fixo ~0,22–0,26 s (diferença dentro do ruído). A assimetria percebida é de atenção: o grid que se clica atualiza no mesmo instante (repaint do próprio clique), enquanto o *outro* grid depende do seu custo de repaint. Clicando no grid congelado, o “outro” é o grid largo (lento); clicando no rolável, o “outro” é o estreito (rápido).

Conclusão: **não há processamento pesado em Python nem inversão de ordem na sincronização**; o atraso percebido é o tempo de redesenho do grid de 28 colunas, inerente ao widget e proporcional ao conteúdo textual das colunas (medido: ~0,12 s com células curtas, ~0,25 s com todas longas). Nenhuma alteração de código foi necessária.

## Risks / Trade-offs

- **[Perda de um cursor customizado quando o ponteiro está sobre o separador no início da operação]** → o Tk já ocultou esse cursor atrás do transitório; usamos o repouso (`""`), que é o cursor de todos os grids da aplicação. Aceito.
- **[Hook de `<Motion>` chamar o helper a cada evento]** → continua O(1) (uma leitura de opção + comparação), sem mudança de custo relevante.
- **[Teste de regressão depende de warp do ponteiro]** → requer display; segue o padrão `needs_display` já usado na suíte.

## Migration Plan

Sem migração de dados nem de API. Rollback = reverter a mudança.
