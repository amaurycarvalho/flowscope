## Purpose

Sub-aba da "Análise Geral" que compara o retorno acumulado de cada ticker com o do seu índice de referência, exibindo o excesso de retorno em pontos percentuais e sinalizando quando um evento societário suspeito pode distorcer a comparação.

## ADDED Requirements

### Requirement: Sub-aba Performance na Análise Geral

O sistema DEVE adicionar a sub-aba "Performance" ao sub-notebook da aba "Análise Geral", posicionada entre "Dominância do Pregão" e "Rede de Correlação". A sub-aba DEVE ser atualizada ao ser selecionada.

#### Scenario: Sub-aba presente na Análise Geral
- **WHEN** o usuário navega para a aba "Análise Geral"
- **THEN** o sistema DEVE exibir a sub-aba "Performance" entre "Dominância do Pregão" e "Rede de Correlação"

#### Scenario: Seleção da sub-aba renderiza o gráfico
- **WHEN** o usuário seleciona a sub-aba "Performance" com tickers selecionados e dados já carregados
- **THEN** o sistema DEVE exibir o gráfico de excesso de retorno para os tickers elegíveis

### Requirement: Gráfico de barras de excesso de retorno

O sistema DEVE exibir uma barra por ticker elegível, com o eixo Y em pontos percentuais do excesso de retorno (`retorno do ticker − retorno do índice`). O zero DEVE representar o índice; barras positivas indicam desempenho acima do índice e negativas, abaixo.

#### Scenario: Ticker acima do índice
- **WHEN** o retorno do ticker supera o retorno do índice no período
- **THEN** a barra correspondente DEVE ser positiva, acima da linha do zero

#### Scenario: Ticker abaixo do índice
- **WHEN** o retorno do ticker fica abaixo do retorno do índice no período
- **THEN** a barra correspondente DEVE ser negativa, abaixo da linha do zero

#### Scenario: Hover com os retornos
- **WHEN** o usuário posiciona o mouse sobre a barra de um ticker
- **THEN** o painel DEVE exibir o retorno do ticker, o retorno do índice e o excesso em pontos percentuais

### Requirement: Seleção do benchmark e elegibilidade por tipo de ativo

O combobox de benchmark DEVE oferecer IFIX quando houver ao menos um FII entre os tickers selecionados e IBOV e IDIV quando houver ao menos uma ação. O default DEVE ser IFIX para o primeiro ticker FII e IBOV para o primeiro ticker ação.

#### Scenario: Watchlist só com FIIs
- **WHEN** os tickers selecionados são todos FIIs
- **THEN** o combobox DEVE oferecer apenas IFIX

#### Scenario: Watchlist só com ações
- **WHEN** os tickers selecionados são todos ações
- **THEN** o combobox DEVE oferecer IBOV e IDIV, sem IFIX

#### Scenario: Default pelo primeiro ticker
- **WHEN** o primeiro ticker selecionado é um FII
- **THEN** o benchmark inicial DEVE ser IFIX

#### Scenario: Default para ação
- **WHEN** o primeiro ticker selecionado é uma ação
- **THEN** o benchmark inicial DEVE ser IBOV

### Requirement: Elegibilidade dos tickers por benchmark

Apenas tickers do tipo correspondente ao benchmark DEVEM entrar no gráfico: FII no IFIX; ação no IBOV ou IDIV. ETF, BDR e tickers de tipo desconhecido NÃO DEVEM entrar no gráfico.

#### Scenario: IFIX exibe apenas FIIs
- **WHEN** o benchmark selecionado é IFIX
- **THEN** apenas tickers do tipo FII DEVEM ser exibidos

#### Scenario: IBOV e IDIV exibem apenas ações
- **WHEN** o benchmark selecionado é IBOV ou IDIV
- **THEN** apenas tickers do tipo ação DEVEM ser exibidos

#### Scenario: Tipos não elegíveis ficam fora
- **WHEN** a seleção contém ETF, BDR ou ticker de tipo desconhecido
- **THEN** esses tickers NÃO DEVEM aparecer no gráfico

### Requirement: Base de retorno por benchmark

O retorno do ticker DEVE usar a mesma base do benchmark: preço para IBOV; total para IFIX e IDIV. O retorno do índice DEVE ser calculado pela variação de fechamento no mesmo intervalo. O ticker e o índice DEVEM ser comparados nas mesmas datas.

#### Scenario: IBOV compara retorno de preço
- **WHEN** o benchmark selecionado é IBOV
- **THEN** o retorno do ticker DEVE ser calculado apenas pela variação de preço, sem proventos

#### Scenario: IFIX compara retorno total
- **WHEN** o benchmark selecionado é IFIX
- **THEN** o retorno do ticker DEVE incluir rendimentos reinvestidos

#### Scenario: IDIV compara retorno total
- **WHEN** o benchmark selecionado é IDIV
- **THEN** o retorno do ticker DEVE incluir dividendos e JCP reinvestidos

#### Scenario: Datas alinhadas
- **WHEN** o ticker e o índice têm observações em datas diferentes
- **THEN** o cálculo DEVE usar apenas as datas comuns, com o mesmo início e fim para os dois

### Requirement: Proventos no retorno total

No retorno total, o provento DEVE ser incorporado no primeiro pregão amostrado igual ou posterior à data ex, reinvestido ao fechamento desse pregão. A data ex DEVE ser derivada do próximo dia útil após a data-com informada pela fonte. A convenção e a aproximação DEVEM ser documentadas.

#### Scenario: Provento dentro do período
- **WHEN** há um provento com data ex dentro do período do retorno total
- **THEN** o valor DEVE ser incorporado ao retorno do ticker na primeira observação igual ou posterior à data ex

#### Scenario: Período sem provento
- **WHEN** não há provento no período
- **THEN** o retorno total DEVE coincidir com o retorno de preço, salvo eventos societários

### Requirement: Respeito aos combos globais de período e amostragem

O painel NÃO DEVE ter seletor de período ou amostragem próprio. O cálculo DEVE usar a carga corrente, conforme os combos globais. Ao alterar período ou amostragem com a sub-aba ativa, o gráfico DEVE ser recalculado.

#### Scenario: Período e amostragem da carga
- **WHEN** o usuário carrega dados com um período e uma amostragem e abre a sub-aba
- **THEN** o gráfico DEVE refletir essa janela e essa amostragem

#### Scenario: Mudança de combo recalcula
- **WHEN** a sub-aba está ativa e o usuário altera o período ou a amostragem
- **THEN** o sistema DEVE recarregar os dados e recalcular o gráfico

### Requirement: Cache pré-calculado dos resultados

O sistema DEVE manter um cache pré-calculado dos resultados, identificado por versão de schema, índice, data de referência, período, amostragem, conjunto ordenado de tickers e base de retorno. Resultados com a mesma chave DEVEM ser reutilizados sem recálculo.

#### Scenario: Mesma entrada reutiliza o cache
- **WHEN** o usuário reabre a sub-aba com os mesmos parâmetros da última execução
- **THEN** o sistema DEVE reutilizar o resultado em cache, sem recalcular

#### Scenario: Mudança de parâmetro invalida
- **WHEN** o período, a amostragem, o índice ou o conjunto de tickers muda
- **THEN** o sistema DEVE recalcular e atualizar o cache

### Requirement: Limitação de eventos societários e aviso

O sistema NÃO DEVE ajustar preços para split, grupamento, desdobramento ou bonificação. A limitação DEVE ser documentada na orientação da sub-aba. Quando o sistema detectar um evento suspeito, DEVE avisar que o retorno pode estar distorcido, sem alterar o valor calculado.

#### Scenario: Evento suspeito sinalizado
- **WHEN** a variação de um ticker num intervalo é compatível com split, grupamento ou bonificação
- **THEN** o painel DEVE sinalizar o ticker com aviso de possível distorção

#### Scenario: Limitação documentada
- **WHEN** o usuário abre a sub-aba
- **THEN** a orientação DEVE informar que eventos societários não são ajustados

#### Scenario: Aviso não corrige o retorno
- **WHEN** um evento suspeito é sinalizado
- **THEN** o valor exibido DEVE permanecer o retorno calculado, sem correção automática

### Requirement: Estado vazio e ausência de dados

Quando não houver tickers elegíveis, dados carregados ou ao menos duas observações alinhadas, o painel DEVE exibir uma mensagem de estado vazio. Quando a série do índice não estiver disponível, o painel DEVE informar que o benchmark está indisponível.

#### Scenario: Sem tickers elegíveis
- **WHEN** a sub-aba é aberta sem tickers do tipo do benchmark
- **THEN** o painel DEVE exibir a mensagem de estado vazio

#### Scenario: Observações insuficientes
- **WHEN** um ticker tem menos de duas observações alinhadas com o índice
- **THEN** o ticker NÃO DEVE ser exibido no gráfico

#### Scenario: Série do índice indisponível
- **WHEN** a série do benchmark não pôde ser obtida
- **THEN** o painel DEVE informar que o benchmark está indisponível, sem exibir barras inválidas

### Requirement: Barra de ferramentas padrão (paridade com o VWAP)

O painel DEVE usar a mesma barra de ferramentas da sub-aba VWAP (`ToolbarBR`), com Início, Voltar, Avançar, Mover, Ampliar, Salvar e "Copiar Gráfico". O botão "Copiar Gráfico" DEVE copiar a figura para a área de transferência como imagem.

#### Scenario: Controles disponíveis
- **WHEN** o painel é exibido
- **THEN** a barra de ferramentas DEVE oferecer os mesmos controles da sub-aba VWAP

#### Scenario: Copiar a figura
- **WHEN** o usuário aciona "Copiar Gráfico"
- **THEN** a figura DEVE ser copiada para a área de transferência como imagem

### Requirement: Orientação da sub-aba

O OrientationPanel DEVE exibir o conteúdo da sub-aba "Performance" com objetivo, pergunta respondida, indicadores envolvidos, como interpretar e a limitação de eventos societários.

#### Scenario: Conteúdo da orientação
- **WHEN** o usuário seleciona a sub-aba "Performance"
- **THEN** o OrientationPanel DEVE exibir o título e o texto explicativo da sub-aba
