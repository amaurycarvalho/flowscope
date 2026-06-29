## REMOVED Requirements

### Requirement: Seleção de ticker para análise individual

**Reason**: Substituído pela seleção direta na TickerList. O combobox era redundante — a lista de tickers no painel direito já oferece seleção múltipla com suporte a callbacks de mudança.

**Migration**: A função `_get_selected_ticker()` deve ser usada em vez de `self._ticker_combo.get()`. O ticker analisado é o primeiro item selecionado na TickerList (por ordem de aparição). Se nenhum estiver selecionado, usa o primeiro da lista completa. Se a lista estiver vazia, retorna `None`.

### Requirement: Sincronização bidirecional de comboboxes

**Reason**: Não há mais combobox para sincronizar. A seleção na TickerList é a única fonte de verdade para qual ticker está sendo analisado.

**Migration**: Remover qualquer código de sincronização entre comboboxes. O callback `_on_listbox_select` na TickerList já dispara `_on_change()` em view mode, que por sua vez chama `_refresh_current_tab()` via `_on_ticker_edit()`.

### Requirement: Sincronização sem navegação automática de aba

**Reason**: Não há mais combobox para sincronizar. O mecanismo de lazy refresh existente já garante que a aba só atualiza quando navegada (`_charts_dirty` + `_refresh_current_tab`).

**Migration**: Remover referências a este requisito. O comportamento de não navegar automaticamente permanece inalterado.

## ADDED Requirements

### Requirement: Seleção de ticker via TickerList

O sistema DEVE derivar o ticker analisado na aba "Análise do Ticker" a partir da seleção na TickerList (painel direito). O primeiro ticker selecionado no Listbox (por ordem de aparição) DEVE ser usado como ticker atual para todas as sub-abas de indicadores.

#### Scenario: Primeiro ticker selecionado é o analisado

- **WHEN** o usuário carrega dados para PETR4, VALE3, ITUB4 e seleciona VALE3 e ITUB4 no Listbox
- **THEN** a aba "Análise do Ticker" DEVE exibir indicadores para VALE3 (primeiro da ordem de seleção)

#### Scenario: Nenhum ticker selecionado usa o primeiro da lista

- **WHEN** o usuário carrega dados para PETR4, VALE3, ITUB4 e nenhum está selecionado no Listbox
- **THEN** a aba "Análise do Ticker" DEVE exibir indicadores para PETR4 (primeiro da lista completa)

#### Scenario: Lista vazia exibe mensagem

- **WHEN** a lista de tickers está vazia e o usuário navega para "Análise do Ticker"
- **THEN** as sub-abas DEVENDO exibir "Selecione um ticker"

### Requirement: Reordenação das sub-abas

A sub-aba "Evolução da Dominância" DEVE ser a primeira aba no notebook da "Análise do Ticker", antes de "Amplitude de Preço".

#### Scenario: Evolução da Dominância como primeira aba

- **WHEN** o usuário navega para "Análise do Ticker"
- **THEN** a primeira sub-aba DEVE ser "Evolução da Dominância" seguida por "Amplitude de Preço"

### Requirement: Atualização ao trocar seleção

O sistema DEVE atualizar as sub-abas da "Análise do Ticker" quando o usuário alterar a seleção na TickerList, utilizando o mecanismo de lazy refresh existente (via `_charts_dirty` e `_on_ticker_edit`).

#### Scenario: Troca de ticker atualiza abas

- **WHEN** o usuário está na aba "Análise do Ticker > Evolução da Dominância" visualizando PETR4 e clica em VALE3 no Listbox
- **THEN** o gráfico DEVE atualizar para mostrar dados de VALE3

## MODIFIED Requirements

### Requirement: Placeholder para Dominância do Pregão

O nome da sub-aba na interface é "Amplitude de Preço". A sub-aba "Amplitude de Preço" DEVE exibir os indicadores de preço: Range, Range%, Typical Price, Median Price, Weighted Close.

#### Scenario: Exibição dos indicadores de preço

- **WHEN** o usuário seleciona a sub-aba "Amplitude de Preço"
- **THEN** o sistema DEVE exibir Range, Range%, Typical Price, Median Price e Weighted Close para o ticker selecionado

*Nota: Apenas o nome do requisito foi corrigido para refletir o nome real da sub-aba na interface ("Amplitude de Preço"). Nenhuma funcionalidade foi alterada.*
