# correlation-network-panel Specification

## Purpose

Sub-aba da "Análise Geral" que exibe a rede de relações entre os papéis selecionados — correlação de curto prazo e cointegração de longo prazo na mesma imagem — revelando agrupamentos naturais (clusters) e a topologia da carteira, a partir dos dados já carregados pelos seletores globais de período e amostragem.

## Requirements

### Requirement: Sub-aba Rede de Correlação na Análise Geral

O sistema DEVE adicionar a sub-aba "Rede de Correlação" ao sub-notebook da aba "Análise Geral", posicionada após "Dominância do Pregão", exibindo um grafo dos tickers selecionados no Listbox. A sub-aba DEVE ser atualizada ao ser selecionada.

#### Scenario: Sub-aba presente na Análise Geral

- **WHEN** o usuário navega para a aba "Análise Geral"
- **THEN** o sistema DEVE exibir a sub-aba "Rede de Correlação" no sub-notebook

#### Scenario: Seleção da sub-aba renderiza o grafo

- **WHEN** o usuário seleciona a sub-aba "Rede de Correlação" com tickers selecionados e dados já carregados
- **THEN** o sistema DEVE exibir o grafo de correlação/cointegração para os tickers selecionados

### Requirement: Codificação visual dupla da rede

O sistema DEVE representar cada ticker como um nó e cada par relevante como uma aresta, codificando: correlação de curto prazo pela cor da aresta (colormap divergente com escala fixa de −1 a +1, refletindo o sinal da correlação), cointegração de longo prazo pelo estilo e espessura da aresta (sólida/grossa quando cointegrado; tracejada/fina caso contrário), cluster pela cor do nó e centralidade pelo tamanho do nó. O painel DEVE exibir uma colorbar para a correlação e uma legenda distinguindo arestas cointegradas das demais.

#### Scenario: Cor da aresta representa a correlação assinada

- **WHEN** o grafo é exibido
- **THEN** cada aresta DEVE ter cor proporcional ao valor assinado da correlação do par, em escala fixa de −1 a +1, com colorbar associada

#### Scenario: Estilo da aresta representa a cointegração

- **WHEN** um par é classificado como cointegrado
- **THEN** sua aresta DEVE ser desenhada com estilo e espessura distintos dos pares não cointegrados, com legenda explicativa

#### Scenario: Cor do nó representa o cluster

- **WHEN** o grafo é exibido
- **THEN** nós pertencentes à mesma comunidade DEVEM compartilhar a mesma cor

### Requirement: Uso dos seletores globais de período e amostragem

O painel NÃO DEVE ter seletor de janela próprio. Ele DEVE calcular a rede a partir dos dados já carregados pela análise corrente, conforme os combos globais de período e amostragem, restringindo-se aos tickers selecionados no Listbox. Quando período ou amostragem mudarem com a sub-aba ativa, a rede DEVE ser recalculada.

#### Scenario: Rede usa os dados dos combos globais

- **WHEN** o usuário carrega dados com um determinado período e amostragem e abre a sub-aba "Rede de Correlação"
- **THEN** a rede DEVE ser calculada sobre os dados dessa carga, sem nova leitura de cache nem download

#### Scenario: Mudança de combo recalcula a rede

- **WHEN** a sub-aba "Rede de Correlação" está ativa e o usuário altera o período ou a amostragem
- **THEN** o sistema DEVE recarregar os dados e recalcular a rede automaticamente

### Requirement: Gate de densidade por número de observações

O sistema DEVE calcular a correlação apenas quando houver ao menos 30 observações alinhadas entre os tickers e a cointegração apenas quando houver ao menos 40 observações alinhadas. Quando o número de observações for inferior a 30, o painel DEVE exibir o estado vazio. Quando estiver entre 30 e 39, o painel DEVE exibir apenas as arestas de correlação e uma mensagem informando que a cointegração requer no mínimo 40 observações.

#### Scenario: Densidade suficiente para correlação e cointegração

- **WHEN** os tickers selecionados têm 40 ou mais observações alinhadas
- **THEN** o sistema DEVE calcular e exibir as arestas de correlação e de cointegração

#### Scenario: Densidade suficiente apenas para correlação

- **WHEN** os tickers têm entre 30 e 39 observações alinhadas
- **THEN** o sistema DEVE exibir apenas as arestas de correlação e uma mensagem informando que a cointegração requer no mínimo 40 observações

#### Scenario: Densidade insuficiente para correlação

- **WHEN** os tickers têm menos de 30 observações alinhadas
- **THEN** o painel DEVE exibir o estado vazio, sem grafo

### Requirement: Diagnóstico de amostragem

O painel DEVE reportar o número de observações alinhadas, o span de calendário coberto e o tamanho dos gaps entre observações consecutivas (mínimo, mediana e máximo em dias úteis), para que o usuário interprete corretamente a esparsidade da amostragem.

#### Scenario: Reporte do diagnóstico

- **WHEN** o grafo é exibido
- **THEN** o painel DEVE informar o número de observações, o período coberto e o tamanho dos gaps

### Requirement: Reprodutibilidade do layout

O layout do grafo DEVE ser determinístico: a mesma seleção de tickers e a mesma grade de observações DEVEM produzir a mesma disposição de nós em execuções repetidas.

#### Scenario: Mesma entrada produz mesmo layout

- **WHEN** o grafo é gerado duas vezes para a mesma seleção e a mesma grade de observações
- **THEN** as posições dos nós DEVEM ser idênticas nas duas execuções

### Requirement: Estado vazio e ausência de dados

Quando não houver tickers selecionados, não houver dados carregados para os tickers selecionados, ou as observações alinhadas forem insuficientes, o painel DEVE exibir uma mensagem de estado vazio em vez de um grafo vazio ou incorreto.

#### Scenario: Sem tickers selecionados

- **WHEN** a sub-aba é aberta sem tickers selecionados
- **THEN** o painel DEVE exibir a mensagem de estado vazio

#### Scenario: Sem dados carregados

- **WHEN** os tickers selecionados não têm dados na carga corrente
- **THEN** o painel DEVE exibir a mensagem de estado vazio

### Requirement: Mensagem de estado vazio contida na área de exibição

A mensagem de estado vazio exibida quando as observações alinhadas são insuficientes DEVE ser ajustada (quebrada em múltiplas linhas) para caber dentro da largura da figura, sem transbordar a área de exibição.

#### Scenario: Mensagem longa se ajusta à largura da figura

- **WHEN** o painel exibe o estado vazio por observações alinhadas insuficientes
- **THEN** a mensagem DEVE ser renderizada em múltiplas linhas, com largura não superior à da figura

### Requirement: Barra de ferramentas padrão (paridade com o VWAP)

O painel DEVE usar a mesma barra de ferramentas da sub-aba VWAP (`ToolbarBR`), com os mesmos controles — Início, Voltar, Avançar, Mover, Ampliar, Salvar e "Copiar Gráfico" — e o mesmo comportamento (Mover e Ampliar mutuamente exclusivos; Início desmarca ambos). O botão "Copiar Gráfico" DEVE copiar a figura exibida para a área de transferência como imagem.

#### Scenario: Controles da toolbar disponíveis

- **WHEN** o painel é exibido
- **THEN** a barra de ferramentas DEVE oferecer Início, Voltar, Avançar, Mover, Ampliar, Salvar e "Copiar Gráfico", idênticos aos da sub-aba VWAP

#### Scenario: Toolbar visível em janela baixa

- **WHEN** a sub-aba é exibida em uma janela com pouca altura disponível para o gráfico
- **THEN** a barra de ferramentas DEVE permanecer visível, sem ser espremida pelo canvas da figura

#### Scenario: Copiar a figura da rede

- **WHEN** o usuário aciona "Copiar Gráfico" com o grafo exibido
- **THEN** a figura DEVE ser copiada para a área de transferência e o sistema DEVE confirmar a ação na barra de status
