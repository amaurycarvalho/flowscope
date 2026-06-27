## ADDED Requirements

### Requirement: Botão "Hoje" na barra superior
O sistema DEVE exibir um botão "Hoje" ao lado do campo DateEntry na barra superior. Ao ser clicado, DEVE resetar o DateEntry para a data atual (`date.today()`). O botão NÃO DEVE disparar o carregamento de dados automaticamente.

#### Scenario: Botão "Hoje" restaura data atual
- **WHEN** o usuário altera o DateEntry para "2026-06-01" e clica no botão "Hoje"
- **THEN** o DateEntry DEVE exibir a data atual (ex: "2026-06-27") e os gráficos NÃO DEVEM ser recarregados

#### Scenario: Botão "Hoje" visível e clicável
- **WHEN** a interface é renderizada
- **THEN** o botão "Hoje" DEVE estar visível ao lado do DateEntry com cursor "hand2"

### Requirement: Toolbox com zoom, pan, reset e save nos charts
Cada chart (VWAP histogram, CVD histogram, scatter) DEVE exibir uma toolbar do matplotlib (NavigationToolbar2Tk) com os botões: Início (reset), Voltar (back), Avançar (forward), Mover (pan), Ampliar (zoom), e Salvar (save figure). Os labels e tooltips DEVEM estar em português.

#### Scenario: Toolbar visível no VWAP chart
- **WHEN** o usuário seleciona o chart VWAP
- **THEN** a toolbar DEVE aparecer abaixo do canvas com os botões em português

#### Scenario: Toolbar visível no CVD chart
- **WHEN** o usuário seleciona o chart CVD
- **THEN** a toolbar DEVE aparecer abaixo do canvas com os botões em português

#### Scenario: Toolbar visível no scatter chart
- **WHEN** o usuário seleciona o chart Dispersão
- **THEN** a toolbar DEVE aparecer abaixo do canvas com os botões em português

#### Scenario: Zoom retangular via toolbar
- **WHEN** o usuário clica em "Ampliar" na toolbar e arrasta um retângulo sobre o gráfico
- **THEN** a área selecionada DEVE ser ampliada para preencher o gráfico

#### Scenario: Pan via toolbar
- **WHEN** o usuário clica em "Mover" na toolbar e arrasta o gráfico
- **THEN** a visualização DEVE deslocar conforme o movimento do mouse

#### Scenario: Reset via "Início"
- **WHEN** o usuário aplica zoom e depois clica em "Início"
- **THEN** a visualização DEVE retornar ao estado original

#### Scenario: Save via "Salvar"
- **WHEN** o usuário clica em "Salvar" na toolbar
- **THEN** um diálogo nativo DEVE abrir para salvar o gráfico como imagem

### Requirement: Hover tooltip no scatter plot com coordenadas VWAP × CVD
Ao passar o mouse sobre um ponto no scatter plot VWAP × CVD, o sistema DEVE exibir um tooltip com o ticker, valor do VWAP, valor do CVD e volume financeiro.

#### Scenario: Hover sobre ponto PETR4
- **WHEN** o usuário passa o mouse sobre o ponto PETR4 no scatter plot
- **THEN** DEVE exibir tooltip com "PETR4 — VWAP: R$ 38.50 — CVD: R$ +452.30 — Vol: 2.1M"

#### Scenario: Hover sobre ponto VALE3
- **WHEN** o usuário passa o mouse sobre o ponto VALE3 no scatter plot
- **THEN** DEVE exibir tooltip com "VALE3 — VWAP: R$ 68.20 — CVD: R$ -120.50 — Vol: 1.8M"

#### Scenario: Tooltip desaparece ao sair do ponto
- **WHEN** o usuário move o mouse para fora do ponto
- **THEN** o tooltip DEVE desaparecer

### Requirement: Hover tooltip no CVD histogram com valor exato
Ao passar o mouse sobre uma barra no CVD histogram, o sistema DEVE exibir um tooltip com o ticker e o valor acumulado do CVD.

#### Scenario: Hover sobre barra PETR4
- **WHEN** o usuário passa o mouse sobre a barra PETR4 no CVD histogram
- **THEN** DEVE exibir tooltip com "PETR4 — CVD: R$ +452.30"

#### Scenario: Hover sobre barra VALE3
- **WHEN** o usuário passa o mouse sobre a barra VALE3 no CVD histogram
- **THEN** DEVE exibir tooltip com "VALE3 — CVD: R$ -120.50"

### Requirement: Hover tooltip no VWAP histogram com faixa de preço e volume
Ao passar o mouse sobre um bucket de volume no VWAP histogram, o sistema DEVE exibir um tooltip com a faixa de preço e o volume negociado naquele bucket.

#### Scenario: Hover sobre bucket PETR4
- **WHEN** o usuário passa o mouse sobre o bucket de R$ 38.50 no VWAP histogram de PETR4
- **THEN** DEVE exibir tooltip com "PETR4 — Preço: R$ 38.50 — Volume: 1.2M"
