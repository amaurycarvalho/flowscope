## MODIFIED Requirements

### Requirement: Título do gráfico e análise textual substituídos por notebook de abas

O sistema DEVE substituir o seletor de visualização por RadioButtons e o label de título por um ttk.Notbook principal com duas abas: "Análise Geral" e "Análise do Ticker". Cada aba principal DEVE conter um sub-ttk.Notebook com suas respectivas sub-abas. O frame "Visualização" e os RadioButtons DEVEM ser removidos.

#### Scenario: Navegação entre abas principais

- **WHEN** o usuário clica na aba "Análise Geral"
- **THEN** o sistema DEVE exibir o sub-notebook com as abas "VWAP" e "Quadrantes"

#### Scenario: Navegação para análise de ticker

- **WHEN** o usuário clica na aba "Análise do Ticker"
- **THEN** o sistema DEVE exibir o combobox de seleção de ticker e o sub-notebook com as 5 sub-abas placeholder

### Requirement: Análise textual substituída por OrientationPanel

O sistema DEVE substituir o widget AnalysisText por um OrientationPanel que exibe conteúdo explicativo fixo associado à sub-aba ativa. Cada sub-aba (VWAP, Quadrantes, Dominância do Pregão, Fluxo Financeiro, Participação Institucional, Eficiência do Movimento, Resumo Geral) DEVE ter seu próprio texto explicativo contendo objetivo, indicadores envolvidos e como interpretá-lo.

#### Scenario: OrientationPanel atualizado ao trocar sub-aba

- **WHEN** o usuário seleciona a sub-aba "VWAP" no sub-notebook de Análise Geral
- **THEN** o OrientationPanel DEVE exibir o título "VWAP — Volume Weighted Average Price" e o texto explicativo correspondente

#### Scenario: OrientationPanel vazio ao selecionar sub-aba placeholder

- **WHEN** o usuário seleciona a sub-aba "Quadrantes"
- **THEN** o OrientationPanel DEVE exibir o título "Quadrantes" e o texto "Em desenvolvimento"

## REMOVED Requirements

### Requirement: Gráfico de dispersão VWAP × CVD

**Reason**: Eliminado como parte da migração do seletor de visualização baseado em RadioButtons para navegação por abas. O gráfico de dispersão não se alinha ao novo modelo de análise que separa visão geral (VWAP + Quadrantes) de análise por ticker.
**Migration**: Substituído pelo sub-notebook de Análise do Ticker, que reserva espaço para indicadores por ticker a serem desenvolvidos futuramente.

### Requirement: CVD Histogram

**Reason**: Eliminado como parte da migração para navegação por abas. O histograma CVD não se alinha ao novo modelo de análise.
**Migration**: Substituído pelo sub-notebook de Análise do Ticker.

### Requirement: Campo multilinha de seleção de tickers

**Reason**: O campo multilinha de tickers e seu comportamento (filtro manual via botão "Filtrar", carregar de arquivo sem atualizar gráficos, duplo clique filtra ticker, menu de contexto) foi simplificado. O filtro agora é aplicado automaticamente após cada edição — o botão "Filtrar" e o comportamento de não-atualizar-gráficos-ao-editar são removidos.
**Migration**: O TickerList continua existindo, mas o filtro é aplicado automaticamente. Qualquer edição no campo de tickers atualiza os gráficos imediatamente.

### Requirement: Duplo clique filtra ticker

**Reason**: O filtro automático após cada edição torna o duplo clique redundante.
**Migration**: Removido.

### Requirement: Menu de contexto no campo de tickers

**Reason**: Simplificação do TickerList. As operações de copiar/selecionar/limpar permanecem disponíveis via atalhos de teclado padrão do sistema.
**Migration**: Menu de contexto removido.
