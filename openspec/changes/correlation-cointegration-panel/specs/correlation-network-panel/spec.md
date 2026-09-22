## Purpose

Sub-aba da "Análise Geral" que exibe a rede de relações entre os papéis selecionados — correlação de curto prazo e cointegração de longo prazo na mesma imagem — revelando agrupamentos naturais (clusters) e a topologia da carteira.

## ADDED Requirements

### Requirement: Sub-aba Rede de Correlação na Análise Geral

O sistema DEVE adicionar a sub-aba "Rede de Correlação" ao sub-notebook da aba "Análise Geral", posicionada após "Dominância do Pregão", exibindo um grafo dos tickers selecionados no Listbox. A sub-aba DEVE ser atualizada ao ser selecionada, reutilizando os dados já carregados quando possível.

#### Scenario: Sub-aba presente na Análise Geral

- **WHEN** o usuário navega para a aba "Análise Geral"
- **THEN** o sistema DEVE exibir a sub-aba "Rede de Correlação" no sub-notebook

#### Scenario: Seleção da sub-aba renderiza o grafo

- **WHEN** o usuário seleciona a sub-aba "Rede de Correlação" com tickers selecionados e histórico de preços em cache
- **THEN** o sistema DEVE exibir o grafo de correlação/cointegração para os tickers selecionados

### Requirement: Codificação visual dupla da rede

O sistema DEVE representar cada ticker como um nó e cada par relevante como uma aresta, codificando: correlação de curto prazo pela cor da aresta (colormap divergente), cointegração de longo prazo pelo estilo e espessura da aresta (sólida/grossa quando cointegrado; tracejada/fina caso contrário), cluster pela cor do nó e centralidade pelo tamanho do nó. O painel DEVE exibir uma colorbar para a correlação e uma legenda distinguindo arestas cointegradas das demais.

#### Scenario: Cor da aresta representa a correlação

- **WHEN** o grafo é exibido
- **THEN** cada aresta DEVE ter cor proporcional ao valor absoluto da correlação do par, com colorbar associada

#### Scenario: Estilo da aresta representa a cointegração

- **WHEN** um par é classificado como cointegrado
- **THEN** sua aresta DEVE ser desenhada com estilo e espessura distintos dos pares não cointegrados, com legenda explicativa

#### Scenario: Cor do nó representa o cluster

- **WHEN** o grafo é exibido
- **THEN** nós pertencentes ao mesmo cluster DEVEM compartilhar a mesma cor

### Requirement: Seletor de janela do painel

O painel DEVE oferecer um seletor de janela de análise próprio (por exemplo, 90, 180 e 252 pregões), independente do seletor global de período e amostragem. Alterar a janela DEVE recalcular o grafo usando apenas o histórico em cache.

#### Scenario: Janela padrão ao abrir

- **WHEN** o usuário seleciona a sub-aba pela primeira vez
- **THEN** o painel DEVE usar uma janela padrão predefinida

#### Scenario: Troca de janela recalcula o grafo

- **WHEN** o usuário altera a janela de análise
- **THEN** o sistema DEVE recalcular o alinhamento, a correlação e a cointegração e redesenhar o grafo

### Requirement: Gate de densidade da cointegração

O sistema DEVE calcular a cointegração apenas quando houver observações alinhadas suficientes entre os tickers (mínimo de 60). Quando o número de observações alinhadas for inferior a 60, o painel DEVE exibir apenas as arestas de correlação e uma mensagem explícita informando a insuficiência de densidade. Quando o número de observações for inferior ao mínimo de correlação (30), o painel DEVE exibir o estado vazio.

#### Scenario: Densidade suficiente

- **WHEN** os tickers selecionados têm 60 ou mais datas em comum no cache
- **THEN** o sistema DEVE calcular e exibir as arestas de cointegração

#### Scenario: Densidade insuficiente para cointegração

- **WHEN** os tickers têm entre 30 e 59 datas em comum
- **THEN** o sistema DEVE exibir apenas as arestas de correlação e uma mensagem informando que a cointegração requer no mínimo 60 observações

#### Scenario: Densidade insuficiente para correlação

- **WHEN** os tickers têm menos de 30 datas em comum
- **THEN** o painel DEVE exibir o estado vazio, sem grafo

### Requirement: Reprodutibilidade do layout

O layout do grafo DEVE ser determinístico: a mesma seleção de tickers e a mesma janela DEVEM produzir a mesma disposição de nós em execuções repetidas.

#### Scenario: Mesma entrada produz mesmo layout

- **WHEN** o grafo é gerado duas vezes para a mesma seleção e janela
- **THEN** as posições dos nós DEVEM ser idênticas nas duas execuções

### Requirement: Estado vazio e ausência de cache

Quando não houver tickers selecionados ou não houver histórico de preços em cache para os tickers selecionados, o painel DEVE exibir uma mensagem de estado vazio em vez de um grafo vazio ou incorreto.

#### Scenario: Sem tickers selecionados

- **WHEN** a sub-aba é aberta sem tickers selecionados
- **THEN** o painel DEVE exibir a mensagem de estado vazio

#### Scenario: Sem histórico em cache

- **WHEN** os tickers selecionados não têm nenhum dia em cache
- **THEN** o painel DEVE exibir a mensagem de estado vazio

### Requirement: Cópia do gráfico

O painel DEVE oferecer o botão "Copiar Gráfico" na barra de ferramentas, copiando a figura exibida para a área de transferência como imagem, com o mesmo comportamento dos demais painéis.

#### Scenario: Copiar a figura da rede

- **WHEN** o usuário aciona "Copiar Gráfico" com o grafo exibido
- **THEN** a figura DEVE ser copiada para a área de transferência e o sistema DEVE confirmar a ação na barra de status
