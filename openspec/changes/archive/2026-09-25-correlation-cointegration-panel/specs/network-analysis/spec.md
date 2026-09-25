## Purpose

Núcleo de cálculo puro que transforma séries de preço alinhadas — provenientes das observações disponíveis na análise corrente — em matrizes de correlação e cointegração, métricas de reversão à média e uma rede de papéis com comunidades, sem executar I/O nem desenhar.

## ADDED Requirements

### Requirement: Alinhamento de séries de preço

O sistema DEVE alinhar as séries de preço dos tickers por interseção de datas (inner join), usando apenas as datas presentes em todos os tickers considerados, e DEVE usar o preço de fechamento (`last_price`) de cada observação. Tickers sem dados DEVEM ser excluídos do resultado, e o número de observações alinhadas DEVE ser reportado.

#### Scenario: Datas comuns entre tickers

- **WHEN** dois tickers têm séries com datas parcialmente diferentes
- **THEN** o alinhamento DEVE conter apenas as datas presentes em ambos

#### Scenario: Ticker sem dados é excluído

- **WHEN** um ticker selecionado não tem nenhuma observação no período
- **THEN** ele NÃO DEVE participar das matrizes nem do grafo

### Requirement: Retornos entre observações consecutivas

O sistema DEVE calcular os retornos entre observações consecutivas da grade alinhada, como `r_t = p_t / p_{t-1} − 1`, para cada ticker. Observações com preço ausente ou não positivo NÃO DEVEM gerar retorno. O sistema DEVE reportar o número de observações e o tamanho dos gaps (mínimo, mediana e máximo em dias úteis) entre observações consecutivas.

#### Scenario: Retorno entre observações consecutivas

- **WHEN** a grade alinhada tem as observações `d1 < d2 < d3`
- **THEN** os retornos DEVEM ser calculados entre `d1` e `d2` e entre `d2` e `d3`, com intervalos idênticos para todos os tickers

#### Scenario: Preço ausente não gera retorno

- **WHEN** uma observação não tem preço ou tem preço não positivo
- **THEN** ela NÃO DEVE participar do cálculo de retorno

#### Scenario: Diagnóstico de gaps reportado

- **WHEN** os retornos são calculados
- **THEN** o resultado DEVE informar o número de observações e os gaps mínimo, mediano e máximo em dias úteis

### Requirement: Matriz de correlação assinada

O sistema DEVE produzir uma matriz de correlação N×N simétrica, com diagonal unitária e valores no intervalo [−1, 1], preservando o sinal da correlação.

#### Scenario: Matriz simétrica com diagonal unitária

- **WHEN** a matriz de correlação é calculada para N tickers
- **THEN** ela DEVE ser simétrica e todos os elementos da diagonal DEVEM ser 1

#### Scenario: Sinal preservado

- **WHEN** dois tickers se movem em direções opostas
- **THEN** a correlação do par DEVE ser negativa

### Requirement: Cointegração par-a-par

Para cada par de tickers com densidade suficiente, o sistema DEVE estimar a relação de equilíbrio de longo prazo (Engle-Granger com OLS + teste ADF em `numpy`) e classificar o par como cointegrado ou não, segundo um nível de significância predefinido. O resultado DEVE indicar, por par, se há cointegração e DEVE reter a estatística do teste. A direção da regressão DEVE ser determinística.

#### Scenario: Par cointegrado

- **WHEN** o teste do par indica relação de equilíbrio significativa
- **THEN** o par DEVE ser marcado como cointegrado

#### Scenario: Par não cointegrado

- **WHEN** o teste do par não indica relação de equilíbrio significativa
- **THEN** o par NÃO DEVE ser marcado como cointegrado

#### Scenario: Direção determinística

- **WHEN** o teste é repetido para o mesmo par
- **THEN** a regressão DEVE usar a mesma variável dependente e independente em ambas as execuções

### Requirement: Gate de densidade por observações

O sistema DEVE calcular a correlação somente quando o número de observações alinhadas for maior ou igual a 30 e a cointegração somente quando for maior ou igual a 40. Abaixo desses limites, o resultado DEVE indicar a indisponibilidade por insuficiência de densidade, sem erro.

#### Scenario: Cointegração indisponível por densidade

- **WHEN** o número de observações alinhadas é inferior a 40
- **THEN** o sistema NÃO DEVE calcular a cointegração e DEVE sinalizar a indisponibilidade

#### Scenario: Correlação indisponível por densidade

- **WHEN** o número de observações alinhadas é inferior a 30
- **THEN** o sistema NÃO DEVE calcular a correlação nem a cointegração

#### Scenario: Cointegração disponível

- **WHEN** o número de observações alinhadas é maior ou igual a 40
- **THEN** o sistema DEVE calcular a cointegração para os pares

### Requirement: Half-life do spread

Para cada par avaliado, o sistema DEVE calcular a meia-vida de reversão à média do spread, reportando-a em **número de observações**. Quando possível, DEVE reportar também uma aproximação em dias. Pares sem reversão identificável NÃO DEVEM reportar half-life.

#### Scenario: Par com reversão à média

- **WHEN** o spread do par apresenta reversão à média
- **THEN** o sistema DEVE reportar a meia-vida em número de observações para o par

### Requirement: Filtro de arestas

O sistema DEVE incluir uma aresta entre dois tickers quando o valor absoluto da correlação exceder um limiar configurado OU quando o par for classificado como cointegrado, evitando grafos densos demais.

#### Scenario: Aresta por correlação forte

- **WHEN** dois tickers têm correlação absoluta acima do limiar
- **THEN** DEVE existir uma aresta entre eles

#### Scenario: Aresta por cointegração

- **WHEN** dois tickers são cointegrados, ainda que a correlação absoluta fique abaixo do limiar
- **THEN** DEVE existir uma aresta entre eles

### Requirement: Construção do grafo, comunidades e centralidade

O sistema DEVE construir um grafo com um nó por ticker e uma aresta por par filtrado, atribuir cada nó a uma comunidade da rede e calcular a modularidade da partição e uma medida de centralidade por nó. O resultado DEVE ser determinístico para a mesma entrada.

#### Scenario: Nós e arestas correspondem aos tickers e pares

- **WHEN** o grafo é construído
- **THEN** DEVE haver um nó por ticker participante e uma aresta por par filtrado

#### Scenario: Comunidades e modularidade reportadas

- **WHEN** o grafo é construído
- **THEN** o resultado DEVE incluir a atribuição de comunidade por nó e a modularidade da partição

#### Scenario: Determinismo do resultado

- **WHEN** o cálculo é repetido para a mesma entrada
- **THEN** o grafo, as comunidades e a modularidade DEVEM ser idênticos
