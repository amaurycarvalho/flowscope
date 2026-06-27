## Context

A TickerList atualmente aplica o filtro de tickers a cada tecla pressionada via evento `<KeyRelease>`, e também ao carregar um arquivo. A barra de status aparece acima dos botões de ação por causa da ordem de empacotamento no layout. Ambas as decisões originais foram tomadas para simplicidade inicial, mas causam problemas de usabilidade: recálculos lentos durante digitação e posicionamento não intuitivo da barra de status.

## Goals / Non-Goals

**Goals:**
- Barra de status sempre visível na parte inferior da janela, abaixo dos botões de ação
- Filtro de tickers acionado exclusivamente pelo botão "Filtrar"
- Indicador visual na barra de status quando o filtro é aplicado

**Non-Goals:**
- Alterar a lógica de filtragem (tickers ausentes em `_current_data` são omitidos)
- Adicionar validação de tickers
- Modificar o layout geral além da ordem barra de status / botões

## Decisions

1. **Pack order invertido**: `_build_statusbar()` agora é chamado antes de `_build_action_buttons()`. Como ambos usam `side=BOTTOM`, o primeiro widget empacotado ocupa a posição mais inferior. Assim, a barra de status fica no fundo absoluto e os botões acima dela.

2. **Botão "Filtrar"**: Novo botão no `btn_frame` ao lado de "Salvar Tickers" e "Carregar Tickers". Dispara o mesmo callback `on_change` que o KeyRelease disparava antes. O callback `_on_ticker_edit` agora também atualiza a barra de status com "Filtro aplicado!".

3. **Remoção do filtro automático**: O bind `<KeyRelease>` foi removido. A chamada a `self._on_change()` dentro de `_load()` também foi removida — carregar um arquivo apenas preenche o campo, sem aplicar o filtro.

## Risks / Trade-offs

- Usuário pode editar a lista de tickers e esquecer de clicar "Filtrar", ficando com o gráfico desatualizado. Mitigação: a barra de status mostra quando o último filtro foi aplicado, e o botão "Carregar" (data) já aplica o filtro automaticamente.
