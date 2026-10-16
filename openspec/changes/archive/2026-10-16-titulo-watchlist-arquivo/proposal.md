## Why

Hoje o título da janela exibe apenas o nome e a versão da aplicação (`app.py:110`) e não identifica qual watchlist está aberta, deixando o usuário sem referência de qual lista está carregada nem de que há alterações não salvas. O requisito de título dinâmico da `ui-polish` (data + N ativos) nunca foi implementado e não corresponde ao comportamento atual; a data e a contagem já aparecem, respectivamente, no rótulo `_date_label` e no contador da lista.

## What Changes

- Título da janela passa a seguir o formato `FlowScopeBR v{versão} — <arquivo>[*]`:
  - `<arquivo>` é o **nome-base** (sem path) do arquivo de watchlist carregado ou salvo;
  - `[*]` é um asterisco exibido quando o **conteúdo** do watchlist foi editado e ainda não salvo;
  - na ausência de arquivo, exibe `Nova lista.txt`.
- Carregar um arquivo atualiza o título e guarda o caminho completo; **Salvar** atualiza o nome e o caminho e remove o asterisco.
- Editar o conteúdo do watchlist (adicionar/remover tickers) marca alteração não salva (asterisco); mudar seleção/filtro NÃO marca.
- Clicar em IBOV/IDIV/IFIX exibe `<ÍNDICE>.txt` (sem asterisco) e NÃO persiste o nome.
- Persistir em `~/.flowscope/config.json` o caminho completo do último arquivo de watchlist (nova chave, ex.: `last_ticker_file`).
- Aposentar o requisito "Título dinâmico da janela" (regredido) e registrar o novo formato.

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `ui-polish`: substitui o requisito "Título dinâmico da janela" pelo novo formato com o nome do watchlist e o asterisco de alteração não salva.
- `ticker-list-persistence`: adiciona a persistência do caminho do último arquivo de watchlist carregado/salvo.

## Impact

- `src/flowscope/presentation/gui/app.py` (montagem do título, `_on_close`), `app_constants.py` (prefixo `TITLE_PREFIX`).
- `src/flowscope/presentation/gui/widgets/ticker_list.py` (sinalizar o caminho no load/save e a edição de conteúdo), `app_wiring.py`/`app_layout.py` (callbacks), `app_tab_actions.py`/`controller_data.py` (índice e filtro).
- `~/.flowscope/config.json`: nova chave de caminho do arquivo.
- Complementa (não substitui) a change `renomear-flowscopebr`, que define o prefixo `FlowScopeBR`.
- Sem novas dependências.
