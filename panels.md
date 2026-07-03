# Painéis do FlowScope — Interface Gráfica

## Estrutura Geral

A interface é dividida em três grandes regiões:

```
┌─────────────────────────────────────────────────────────────┐
│  [Data] [Hoje] [Carregar] [Copiar Dados]                   │
├──────────────────────────────┬──────────────────────────────┤
│  Aba Principal               │  Filtro de Tickers           │
│  ┌────────────────────────┐  │  (lista editável)            │
│  │  Sub-abas              │  │                              │
│  │                        │  │  Orientação                  │
│  │                        │  │  (ajuda contextual)          │
│  └────────────────────────┘  │                              │
├──────────────────────────────┴──────────────────────────────┤
│  Status: mensagens e indicadores                            │
└─────────────────────────────��───────────────────────────────┘
```

---

## Barra Superior

### Seletor de Data

- **Componente:** `DateEntry` (tkcalendar)
- **Descrição:** Campo de seleção de data no formato `YYYY-MM-DD`.
- **Objetivo:** Definir a data de referência para carregamento dos dados da B3.
- **Uso:** Digite a data manualmente ou use o calendário suspenso. Pressione Enter ou clique em "Carregar" para iniciar a carga.

### Botão "Hoje"

- **Descrição:** Atalho para definir a data atual e carregar automaticamente.
- **Objetivo:** Agilizar a consulta do pregão mais recente disponível.

### Botão "Carregar"

- **Descrição:** Dispara o carregamento dos dados da B3 para a data selecionada.
- **Objetivo:** Obter os dados consolidados de negociação (TradeInformationConsolidated), processar todos os indicadores e popular a interface.

### Botão "Copiar Dados"

- **Descrição:** Copia para a área de transferência uma tabela CSV contendo `Ticker;VWAP;MoneyFlowVolume` para todos os ativos carregados.
- **Objetivo:** Exportação rápida dos principais indicadores agregados para análise externa (planilhas, relatórios).

---

## Aba Principal: "Análise Geral"

### Sub-aba: VWAP

- **Objetivo:** Comparar a distribuição de preços de todos os ativos em relação ao seu respectivo VWAP no período.
- **Responde a pergunta:** _Quem está acima do preço justo e quem está abaixo?_
- **Indicadores envolvidos:** VWAP (preço médio ponderado), volume por bucket de preço (volume profile), preço de fechamento (LastPric), preço mínimo e máximo (MinPric, MaxPric).
- **Como interpretar:** O VWAP é a referência de preço justo do período. Negociações acima do VWAP indicam viés comprador; abaixo, viés vendedor. A largura do violino mostra em quais faixas de preço houve maior concentração de volume. O último preço (losango vermelho) em relação ao VWAP indica se o fechamento reforça ou contradiz a tendência do período.

### Sub-aba: Quadrantes

- **Objetivo:** Classificar ativos em quatro quadrantes com base no CLV (eixo X) e no desvio do VWAP (eixo Y), revelando a interação entre fluxo comprador/vendedor e posição relativa ao preço justo.
- **Responde a pergunta:** _Quem dominou o fechamento? O preço terminou acima ou abaixo do valor justo? Quanto volume financeiro sustentou esse comportamento?_
- **Indicadores envolvidos:** CLV (Close Location Value), VWAP Distance (desvio percentual do último preço em relação ao VWAP diário), Volume (FinInstrmQty como tamanho da bolha).
- **Como interpretar:**
  - Q1 (CLV > 0, acima do VWAP): compra forte confirmada — fechamento na metade superior do range e acima do VWAP.
  - Q2 (CLV < 0, acima do VWAP): venda relativa — ativo acima do VWAP mas perdeu força no fechamento (possível realização).
  - Q3 (CLV < 0, abaixo do VWAP): venda forte confirmada — vendedores dominaram o dia.
  - Q4 (CLV > 0, abaixo do VWAP): compra em desconto — reação compradora insuficiente para recuperar o VWAP.
  - Se apenas um ticker for selecionado, as setas cinzas mostram a trajetória dos dias anteriores, evidenciando a evolução temporal de cada ativo.

### Sub-aba: Dominância do Pregão

- **Objetivo:** Visualizar rapidamente quais ativos tiveram dominância compradora ou vendedora no último pregão.
- **Responde a pergunta:** _Quem venceu a disputa diária pelo preço?_
- **Indicadores envolvidos:** CLV (Close Location Value) para direção/intensidade, Money Flow Volume (MFV) para capital envolvido.
- **Como interpretar:** Barras para a direita indicam dominância compradora (CLV positivo); para a esquerda, vendedora (CLV negativo). Quanto maior o comprimento, mais intensa a dominância. O traço horizontal sobre a barra representa o volume financeiro que sustentou o movimento. Passe o mouse sobre as barras para ver detalhes do ticker.

---

## Aba Principal: "Análise do Ticker"

O ticker analisado é determinado pelo primeiro item selecionado na TickerList (painel direito). Se nenhum ticker estiver selecionado, usa o primeiro da lista. Se a lista estiver vazia, exibe "Selecione um ticker". Os dados são atualizados automaticamente ao trocar de ticker ou de sub-aba.

### Sub-aba: Evolução da Dominância ✅

- **Objetivo:** Visualizar a evolução temporal da dominância compradora/vendedora para o ticker selecionado.
- **Responde a pergunta:** _Quem venceu a disputa diária pelo preço?_
- **Componente gráfico:** Gráfico de barras horizontais (CLV por pregão), com linha horizontal representando o fluxo financeiro diário (Daily Money Flow).
- **Indicadores envolvidos:** CLV (Close Location Value) nas barras, Daily Money Flow (traço horizontal), Eficiência (convicção no tooltip).
- **Como interpretar:** Cada barra representa um pregão. Direita = compradores dominaram; Esquerda = vendedores dominaram. O traço horizontal indica o fluxo financeiro diário (intensidade codificada pela espessura/opacidade). O rodapé mostra a proporção de dias compradores vs. vendedores. Passe o mouse sobre as barras para ver detalhes da dominância e convicção do movimento.

### Sub-aba: Amplitude de Preço ✅

- **Objetivo:** Visualizar como o preço percorreu sua faixa de negociação ao longo dos pregões, identificando se a oscilação resultou em movimento direcional convincente ou se compradores e vendedores permaneceram equilibrados.
- **Responde a pergunta:** _O preço apenas oscilou ou houve um movimento direcional convincente durante o pregão? Como a posição do fechamento dentro do range evoluiu nos últimos dias?_
- **Layout do painel:** O painel é composto por dois componentes gráficos organizados verticalmente (GridSpec com `height_ratios=[3, 0.6]`):
  ```
  ┌──────────────────────────────────────────┐
  │  Price Range Timeline       [Classificação]│
  │  (com eficiência como barra de fundo)    │
  ├──────────────────────────────────────────┤
  │  CLV Gauge                               │
  └──────────────────────────────────────────┘
  ```
- **Componentes:**
  - **Price Range Timeline (painel superior, 3/4 da altura):** Gráfico horizontal que normaliza o range [Min, Max] de cada pregão em 0-100% no eixo X. O eixo Y lista as datas cronologicamente (mais recente no topo). Cada linha possui uma **barra de fundo** cujo comprimento é a Eficiência Diária (substitui o gauge separado de eficiência): vermelha (≤ 0,30), amarela (0,30-0,60), verde (> 0,60). Sobre a barra de fundo, uma linha cinza horizontal percorre 0-100%.
    - Dia atual: exibe todos os marcadores de referência — ● (Close, tamanho proporcional ao Range%), **M** (Median Price), **T** (Typical Price), **V** (VWAP), **W** (Weighted Close).
    - Dias anteriores: ● com opacidade reduzida, conectados por setas cinzas que traçam a trajetória do fechamento.
    - **Classificação qualitativa** no canto superior direito, baseada na combinação de Range% e Eficiência Diária:
      - **Pregão Lateral:** Range% ≤ mediana histórica e Eficiência ≤ 0,30 — oscilação dentro do normal, sem direção.
      - **Volatilidade sem Direção:** Range% > mediana e Eficiência ≤ 0,30 — range ampliado mas sem convicção.
      - **Movimento Consistente:** Range% ≤ mediana e Eficiência > 0,30 — movimento direcionado mesmo com amplitude moderada.
      - **Movimento Direcional Forte:** Range% > mediana e Eficiência > 0,30 — range amplo com convicção direcional.
    - Mínima e máxima do dia mais recente exibidas como labels abaixo do eixo X.
  - **CLV Gauge (painel inferior, ~1/4 da altura):** Barra horizontal (-1 a +1) indicando onde o preço fechou dentro do range. Verde para CLV positivo (pressão compradora), vermelho para negativo (pressão vendedora), com labels "Vendedores ←" e "Compradores →".
- **Indicadores envolvidos:**
  - **Range** e **Range Percentual** medem a amplitude da oscilação diária.
  - **CLV (Close Location Value)** indica onde o preço fechou dentro dessa faixa.
  - **Daily Efficiency** mostra quanto da amplitude foi convertida em deslocamento líquido (usado como barra de fundo).
  - **Median Price**, **Typical Price**, **Weighted Close** e **VWAP** servem como referências para comparar a posição do fechamento.
- **Como interpretar:**
  - Uma amplitude elevada indica maior volatilidade, mas não significa necessariamente uma tendência forte.
  - Um **CLV** próximo de **+1** indica fechamento perto da máxima do dia; próximo de **−1**, fechamento perto da mínima.
  - Uma **Eficiência Diária** elevada mostra que a oscilação foi convertida em avanço efetivo, sugerindo convicção.
  - Quando a amplitude é alta mas a eficiência é baixa, o pregão foi marcado por disputa sem direção.
  - Dias com barra de fundo verde consecutiva = sequência direcional forte.
  - Passe o mouse sobre os marcadores do timeline para ver valores detalhados de cada pregão.

### Sub-aba: Fluxo Financeiro

- **Objetivo:** Mostrar se o movimento do preço foi acompanhado por fluxo financeiro suficiente para indicar convicção compradora ou vendedora.
- **Responde a pergunta:** _O movimento de hoje foi sustentado por fluxo financeiro?_
- **Layout do painel:** Três subplots empilhados verticalmente (GridSpec com `height_ratios=[3, 2, 3]`):
  ```
  ┌──────────────────────────────────────────┐
  │  Card de Classificação (sem eixos)       │
  │  (título, classificação, DMF,            │
  │   MFV acumulado, Range%)                 │
  ├──────────────────────────────────────────┤
  │  CLV / Score Bar                         │
  │  (marcador CLV, labels Comprador/Vendedor)│
  ├──────────────────────────────────────────┤
  │  Pressão no Range (B×S)                  │
  │  (barra empilhada Buy/Sell Pressure)     │
  └──────────────────────────────────────────┘
  ```
- **Componentes:**
  - **Card de Classificação (painel superior, eixos ocultos):** Exibe o título "Fluxo Financeiro — {ticker}", a classificação qualitativa (ex.: "Fluxo Forte"), e os valores do último pregão: Volume Financeiro (R$ X,XXM), DMF (R$ X,XXM), MFV Acumulado (R$ X,XXM) e Range% (X,X%). Borda colorida conforme a classificação.
  - **Gráfico CLV / Score (painel médio):** Barra horizontal na escala −1 a +1. Verde para fluxo comprador (CLV positivo), vermelho para vendedor (CLV negativo). Marcador triangular na posição exata do CLV, rótulos "◄ Vendedor" / "Comprador ►", escala percentual (−100% a +100%).
  - **Barra de Pressão no Range (painel inferior):** Barra empilhada horizontal com Buying Pressure (verde) e Selling Pressure (vermelha). Rótulos "Compra {bp}%" e "Venda {sp}%". Fórmulas BP e SP como referência.
- **Indicadores envolvidos:**
  - `Daily Money Flow (DMF)` — CLV × Volume Financeiro do pregão, exibido em milhões
  - `Money Flow Volume (MFV) acumulado` — soma do DMF no período, exibido em milhões
  - `CLV (Close Location Value)` — posição do fechamento no range (−1 a +1)
  - `Buying Pressure / Selling Pressure` — domínio do range (0 a 1)
  - `Score normalizado` — DMF / Volume Financeiro (comparável entre ativos)
  - `Range Percentual` — amplitude relativa do dia
- **Como interpretar:** O DMF é o indicador principal. Score > 8% sugere fluxo forte. MFV acumulado mostra tendência multidia. CLV indica onde o preço fechou. Passe o mouse sobre o card para detalhes numéricos completos.

### Sub-aba: Participação Institucional 🔒

- **Status:** Placeholder — sub-aba desabilitada (implementação futura).
- **Objetivo:** Estimar o perfil dos participantes do pregão (institucional vs. varejo) com base no tamanho médio das negociações.
- **Responde a pergunta:** _Quem parece estar negociando? Grandes participantes ou varejo?_
- **Indicadores envolvidos:**
  - `Average Trade Size` — Quantidade média de ações por negócio
  - `Average Financial Ticket` — Valor financeiro médio por negócio

### Sub-aba: Eficiência do Movimento 🔒

- **Status:** Placeholder — sub-aba desabilitada (implementação futura).
- **Objetivo:** Medir se o range do dia resultou em deslocamento efetivo do preço ou foi apenas ruído (oscilação sem direção).
- **Responde a pergunta:** _O mercado caminhou com convicção ou apenas oscilou?_
- **Indicadores envolvidos:**
  - `Daily Efficiency` — `|Fechamento − Preço Médio| / Range`

### Sub-aba: Resumo Geral 🔒

- **Status:** Placeholder — sub-aba desabilitada (implementação futura).
- **Objetivo:** Consolidar todos os indicadores disponíveis em uma única visualização para o ticker selecionado.
- **Responde a pergunta:** _O que realmente aconteceu neste ativo? Quem parece estar negociando? Grandes participantes ou varejo?_
- **Indicadores envolvidos:**
  - **Preço:** Range, Range%, Typical Price, Median Price, Weighted Close
  - **Fluxo:** CLV, Money Flow Multiplier, Money Flow Volume, Buying Pressure, Selling Pressure
  - **Tamanho:** Average Trade Size, Average Financial Ticket
  - **Eficiência:** Daily Efficiency, Dominance Score
  - **Densidade:** Financial Density, Trade Density, Volume Density
  - **Adicionais:** VWAP Distance, VWAP do período, Money Flow Volume acumulado

---

## Painel Lateral Direito

### Filtro de Tickers (TickerList)

- **Componente:** `tk.Text` (modo edição) / `tk.Listbox` com `exportselection=False` (modo visualização)
- **Descrição:** Alterna entre edição (Text) e seleção múltipla (Listbox) via toggle "Editar lista de tickers". Permite salvar/carregar listas de arquivos `.txt`.
- **Objetivo:** Controlar quais tickers são exibidos nos gráficos e análises. Funciona como uma "carteira" ou "watchlist". A seleção no Listbox também determina o ticker analisado na aba "Análise do Ticker".
- **Funcionalidades:**
  - **Modo edição:** Texto multilinha, um ticker por linha. Duplo clique isola um ticker. Clique direito → menu de contexto (copiar, remover, selecionar todos, limpar).
  - **Modo visualização:** Listbox com seleção múltipla (`EXTENDED`). Ctrl+Click e Shift+Click para selecionar múltiplos tickers.
  - Botões "Selecionar Todos" e "Desmarcar Todos" na barra superior (visíveis apenas no modo visualização).
  - Botão "Salvar Tickers" → exporta a lista atual para arquivo.
  - Botão "Carregar Tickers" → importa lista de arquivo.
  - Se nenhum ticker for fornecido, o programa carrega automaticamente a carteira IDIV (Índice Dividendos) da B3.

### Painel de Orientação (OrientationPanel)

- **Componente:** `tk.Text` somente leitura com título
- **Descrição:** Exibe texto de ajuda contextual que se atualiza conforme o usuário navega entre abas e sub-abas.
- **Objetivo:** Guiar o usuário na interpretação do painel ativo, explicando o objetivo, os indicadores envolvidos e como interpretar os resultados.
- **Conteúdo:** Dinâmico — muda automaticamente ao selecionar uma sub-aba diferente.

---

## Barra de Status

- **Componente:** `tk.Label` com `relief=SUNKEN`
- **Descrição:** Exibe mensagens de status, contagens e indicadores de progresso.
- **Objetivo:** Informar o usuário sobre o estado atual do programa (pronto, carregando, erros, confirmações).
- **Mensagens típicas:**
  - "Pronto. Selecione uma data e clique em Carregar."
  - "Carregando..." (com animação de pontos durante o carregamento)
  - "✓ 45 tickers carregados para 2025-06-15."
  - "✓ Dados copiados!"
  - "⚠ Não foi possível carregar os dados. ..."
