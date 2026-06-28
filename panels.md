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
- **Visualização:** Gráfico de violino (violin plot) utilizando Matplotlib, com barra de ferramentas para zoom, pan, salvar e copiar imagem.
- **Objetivo:** Comparar a distribuição de preços de todos os ativos em relação ao seu respectivo VWAP no período.
- **Indicadores envolvidos:** VWAP (linha zero), Volume Profile (largura do violino), preço mínimo/máximo (traço vertical), último preço (losango vermelho).
- **Como interpretar:**
  - A linha tracejada em 0% representa o VWAP de cada ativo.
  - A largura do violino em cada faixa de percentual indica a concentração de volume financeiro — quanto mais largo, maior o volume negociado naquela faixa de preço.
  - O traço vertical preto mostra a amplitude (mínima a máxima) dos preços do dia em percentual de desvio do VWAP.
  - O círculo preto sobre a linha zero é o VWAP; o losango vermelho é o último preço (fechamento).
  - Um fechamento acima de 0% sugere viés comprador no fechamento; abaixo, viés vendedor.
  - Passe o mouse sobre cada violino para ver detalhes: ticker, VWAP em R$, desvios máximo/mínimo, último preço e volume total.

### Sub-aba: Quadrantes
- **Visualização:** Gráfico de dispersão bidimensional (bubble chart) utilizando Matplotlib, com setas de trajetória temporal (quiver) e barra de ferramentas para zoom, pan, salvar e copiar imagem.
- **Objetivo:** Representar simultaneamente a direção do fluxo comprador/vendedor (CLV), a posição do fechamento em relação ao preço justo (VWAP Distance) e a intensidade da participação (volume de instrumentos).
- **Indicadores envolvidos:**
  - **Eixo X:** CLV (Close Location Value) — varia de −1 (fechamento na mínima) a +1 (fechamento na máxima).
  - **Eixo Y:** VWAP Distance — desvio percentual do último preço em relação ao VWAP diário: `(LastPric − TradAvrgPric) / TradAvrgPric`.
  - **Tamanho da bolha:** Raiz quadrada do `FinInstrmQty` (quantidade de instrumentos negociados), normalizado.
  - **Cor da bolha:** Colormap divergente RdYlGn — verde para CLV positivo (pressão compradora), vermelho para CLV negativo (pressão vendedora).
- **Como interpretar:**
  - As bolhas representam o **último dia** de cada ativo. As setas cinzas mostram a trajetória dos dias anteriores.
  - **Q1 (CLV > 0, acima do VWAP):** Compradores dominaram o pregão e o fechamento ficou acima do preço médio. Movimento consistente.
  - **Q2 (CLV < 0, acima do VWAP):** O ativo permaneceu acima do VWAP, mas perdeu força no fechamento. Possível realização de lucros.
  - **Q3 (CLV < 0, abaixo do VWAP):** Vendedores dominaram durante todo o pregão. Fechamento abaixo do preço justo. Pressão vendedora consistente.
  - **Q4 (CLV > 0, abaixo do VWAP):** Reação compradora no final, mas insuficiente para recuperar o preço médio. Possível início de acumulação.
  - Passe o mouse sobre cada bolha para ver detalhes: ticker, data, CLV, VWAP Distance e quantidade de instrumentos.
  - O painel de orientação exibe um resumo textual automático da distribuição dos ativos entre os quadrantes.

---

## Aba Principal: "Análise do Ticker"

Esta aba exibe indicadores calculados **por ticker**. Selecione o ativo desejado no combobox logo acima das sub-abas. Os dados são atualizados automaticamente ao trocar de ticker ou de sub-aba.

### Sub-aba: Dominância do Pregão
- **Objetivo:** Analisar a amplitude da oscilação e as diferentes métricas de preço do ativo no pregão.
- **Indicadores envolvidos:**
  - `Range` — Amplitude absoluta (máxima − mínima)
  - `Range Percentual` — Amplitude relativa ao preço médio
  - `Typical Price` — Média de máxima, mínima e fechamento
  - `Median Price` — Ponto médio entre máxima e mínima
  - `Weighted Close` — Média com peso duplo no fechamento
- **Como interpretar:**
  - Range alto indica alta volatilidade intradiária.
  - Range% permite comparar volatilidade entre ativos de preços distintos.
  - Compare Typical vs. Median vs. Weighted Close para identificar viés do fechamento em relação ao centro do range.

### Sub-aba: Fluxo Financeiro
- **Objetivo:** Mensurar a direcionalidade do fluxo de ordens — pressão compradora versus vendedora.
- **Indicadores envolvidos:**
  - `CLV` (Close Location Value) — Posição do fechamento no range (−1 a +1)
  - `Money Flow Multiplier` — Idêntico ao CLV
  - `Money Flow Volume` — CLV × Volume Financeiro, acumulado no período
  - `Buying Pressure` — Percentual do range ocupado pelo movimento comprador
  - `Selling Pressure` — Percentual do range ocupado pelo movimento vendedor
- **Como interpretar:**
  - CLV positivo indica fechamento na metade superior do range (viés comprador); negativo, metade inferior (viés vendedor).
  - Buying + Selling Pressure = 1. Se Buying > Selling, a pressão compradora foi dominante.
  - Money Flow Volume positivo ao longo dos dias → acúmulo (instituições comprando). Negativo → distribuição.

### Sub-aba: Participação Institucional
- **Objetivo:** Estimar o perfil dos participantes do pregão (institucional vs. varejo) com base no tamanho médio das negociações.
- **Indicadores envolvidos:**
  - `Average Trade Size` — Quantidade média de ações por negócio
  - `Average Financial Ticket` — Valor financeiro médio por negócio
- **Como interpretar:**
  - Tickets médios elevados (ex.: milhares de ações ou dezenas de milhares de reais por negócio) sugerem participação de investidores institucionais (fundos, bancos).
  - Tickets baixos sugerem predomínio de pessoa física.
  - A evolução ao longo de múltiplos dias revela mudanças na composição do fluxo.

### Sub-aba: Eficiência do Movimento
- **Objetivo:** Medir se o range do dia resultou em deslocamento efetivo do preço ou foi apenas ruído (oscilação sem direção).
- **Indicadores envolvidos:**
  - `Daily Efficiency` — `|Fechamento − Preço Médio| / Range`
- **Como interpretar:**
  - Eficiência ≈ 0 (ex.: 0,05) → pregão lateral. O preço oscilou mas retornou ao ponto de partida. Indecisão.
  - Eficiência ≈ 1 (ex.: 0,85) → dia direcional forte. O range foi totalmente aproveitado para deslocamento líquido. Convicção.
  - Valores intermediários sugerem movimentos parciais.

### Sub-aba: Resumo Geral
- **Objetivo:** Consolidar todos os indicadores disponíveis em uma única visualização para o ticker selecionado.
- **Indicadores envolvidos:**
  - **Preço:** Range, Range%, Typical Price, Median Price, Weighted Close
  - **Fluxo:** CLV, Money Flow Multiplier, Money Flow Volume, Buying Pressure, Selling Pressure
  - **Tamanho:** Average Trade Size, Average Financial Ticket
  - **Eficiência:** Daily Efficiency
  - **Densidade:** Financial Density, Trade Density, Volume Density
  - **Adicionais:** VWAP do período, Money Flow Volume acumulado
- **Como interpretar:** Use este painel para uma visão panorâmica de todos os indicadores, facilitando a correlação entre diferentes dimensões (preço, fluxo, tamanho, eficiência e densidade).

---

## Painel Lateral Direito

### Filtro de Tickers (TickerList)
- **Componente:** `tk.Text` com scrollbar
- **Descrição:** Lista editável de tickers, um por linha. Permite salvar/carregar listas de arquivos `.txt` e aplicar filtro.
- **Objetivo:** Controlar quais tickers são exibidos nos gráficos e análises. Funciona como uma "carteira" ou "watchlist".
- **Funcionalidades:**
  - Duplo clique em um ticker → isola apenas aquele ticker na lista.
  - Clique direito → menu de contexto (copiar ticker, remover do filtro, selecionar todos, limpar).
  - Botão "Salvar Tickers" → exporta a lista atual para arquivo.
  - Botão "Carregar Tickers" → importa lista de arquivo.
  - Botão "Filtrar" → aplica o filtro, recarregando gráficos e listas de tickers.
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
