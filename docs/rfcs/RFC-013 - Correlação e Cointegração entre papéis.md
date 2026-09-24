# RFC-013: Visualização Topológica de Correlação e Cointegração entre Papéis com `networkx` + `matplotlib`

**Data:** 2026-09-22
**Status:** Proposto — em implementação pela change `correlation-cointegration-panel`
**Componente:** Módulo de análise de redes de ativos

---

## P — Problem (Problema)

Precisamos visualizar simultaneamente, para **dezenas de papéis** (ações), duas relações distintas e frequentemente conflitantes:

1. **Correlação de curto prazo** — co-movimento dos retornos calculados sobre a amostragem de datas disponível no FlowScope.
2. **Cointegração de longo prazo** — vínculo de equilíbrio entre os preços que faz o *spread* reverter à média.

Além disso, o analista precisa **identificar agrupamentos naturais** (clusters) de papéis semelhantes, enxergando a topologia da rede como um todo — não apenas pares isolados. A matriz de correlação N×N (para N=50, são 1.225 pares) é ilegível como tabela. Precisamos de uma representação visual que:

- Mostre a **estrutura global** (quem se agrupa com quem).
- Diferencie **curto prazo** de **longo prazo** na mesma imagem.
- Escale para dezenas de nós sem virar um "emaranhado" (hairball).
- Seja reproduzível e integrável ao pipeline Python existente.

### Premissa de amostragem (esparsa)

O FlowScope não entrega séries diárias contíguas. Os combos globais de **período** e **amostragem** definem as datas disponíveis (ex.: "Últimos 30 dias" + "Fibonacci" → ~7 datas com gaps). A rede deve ser calculada sobre **as observações já carregadas** por esses combos, e não sobre uma janela própria do painel.

Isso é coerente porque o cache da B3 é uma **grade compartilhada por todo o mercado**: um arquivo por data contém todos os tickers. Assim, todos os papéis compartilham exatamente as mesmas observações, e os retornos são medidos entre **observações consecutivas** com intervalos idênticos para todos os tickers — o que torna as correlações comparáveis entre pares. Em contrapartida:

- A correlação deixa de ser "diária": cada ponto cobre um intervalo de 1, 2, 5 ou mais dias.
- O ADF assume espaçamento regular; sob amostragem irregular a cointegração deve ser tratada como **indício exploratório**, não como teste estrito.
- A amostragem Fibonacci concentra datas no presente, enviesando a leitura para o curto prazo.

---

## R — Root Cause (Causa Raiz)

A dificuldade não é de cálculo, mas de **representação**. As causas raiz são:

1. **Dimensionalidade**: relações par-a-par crescem em O(N²). Tabelas e heatmaps mostram os valores, mas não a **topologia** (quem está próximo de quem no espaço de similaridade).
2. **Duas métricas ortogonais**: correlação e cointegração medem coisas diferentes (curto vs. longo prazo) e não podem ser colapsadas numa única dimensão sem perda de informação.
3. **Matplotlib puro não tem primitiva de grafo**: a página de plot types do Matplotlib cobre linhas, dispersão, barras, heatmaps, etc., mas **não oferece** um tipo nativo de "network graph". Sem uma camada de layout (force-directed), as posições dos nós seriam arbitrárias.
4. **Sem layout dedicado, o gráfico não revela clusters**: posicionar nós em círculo ou grade não evidencia proximidade topológica; é preciso um algoritmo que agrupe por similaridade (spring/force-directed).

---

## O — Options (Opções)

### Opção 1 — `networkx` + `matplotlib` (force-directed)
- **Como funciona**: `networkx.spring_layout()` calcula posições 2D onde nós conectados por arestas fortes se atraem e nós sem conexão se repelem. O `matplotlib` desenha nós, arestas e rótulos sobre um `ax`.
- **Prós**: layout "constelação" emerge naturalmente; controle total de cor/tamanho/estilo; integra-se ao Matplotlib; `networkx` é maduro, Python puro e leve.
- **Contras**: dependência extra (`networkx`); layouts force-directed são não-determinísticos (exigem `seed`); para N muito grande, o cálculo do layout pode ficar lento.

### Opção 2 — Matplotlib puro (MDS/t-SNE + `scatter`/`plot`)
- **Como funciona**: posiciona os nós em 2D via `sklearn.manifold.MDS` ou `TSNE`, depois desenha arestas com `ax.plot()`/`ConnectionPatch` e nós com `ax.scatter()`.
- **Prós**: zero dependências de grafos.
- **Contras**: reimplementa o que o `networkx` já faz; mais código; layout precisa ser gerenciado manualmente; sem semântica de grafo (graus, centralidade, comunidades).

### Opção 3 — Heatmap + dendrograma (sem grafo)
- **Como funciona**: `imshow`/`pcolormesh` da matriz de correlação ordenada por clustering hierárquico, com `scipy.cluster.hierarchy.dendrogram`.
- **Prós**: simples, determinístico, ordenado.
- **Contras**: não mostra a topologia como "teia"; não representa bem cointegração simultaneamente; não é o estilo visual desejado. Também exigiria `scipy`, fora do ecossistema atual.

### Opção 4 — Bibliotecas de visualização de grafos interativas (Plotly, PyVis, Graphviz)
- **Prós**: interatividade, layouts prontos.
- **Contras**: foge do ecossistema Matplotlib pedido; menos controle fino de estilo; dependências pesadas.

---

## B — Better Solution (Melhor Solução)

**Adotar a Opção 1: `networkx` + `matplotlib`**, com as seguintes decisões de design.

### 0. Fonte de dados: combos globais, sem I/O próprio

A rede consome o resultado **já carregado** pela análise corrente (`_current_data`), filtrado pelos tickers selecionados no Listbox. Ela **não** tem janela própria, **não** lê o cache, **não** baixa dados e **não** roda job em background. Quando os combos de período/amostragem mudam com a sub-aba ativa, a rede é recalculada pelo fluxo de atualização já existente.

### 1. Construção do grafo
- **Nós** = papéis (tickers).
- **Arestas** = pares com relação relevante, filtradas por limiar (ex.: `|corr| > 0,5` ou cointegração significativa) para evitar *hairball*.
- Cada aresta carrega **dois atributos**: `corr` (assinado, curto prazo) e `coint` (longo prazo, booleano ou p-valor).

### 2. Layout
- `nx.spring_layout(G, seed=42, k=...)` para o efeito "constelação".
- `seed` fixo garante reprodutibilidade (para a mesma grade de observações e a mesma versão do `networkx`).
- Ajustar `k` (distância ótima entre nós) conforme densidade da rede.

### 3. Codificação visual dupla
| Informação | Canal visual |
|---|---|
| Correlação de curto prazo | **Cor da aresta** com colormap divergente e escala fixa `[-1, +1]`: **correlação assinada** (positiva vs. negativa) |
| Cointegração de longo prazo | **Espessura** (mais grossa) e/ou **estilo** (sólida vs. tracejada) |
| Força da relação | **Alpha** da aresta |
| Cluster de semelhantes | **Cor do nó** (via `tab20` ou comunidades da rede) |
| Importância/centralidade | **Tamanho do nó** (opcional, ex.: grau) |

> A correlação é **assinada** e a escala é fixada em `[-1, +1]`. Mapear `|corr|` num colormap divergente (como `coolwarm`) tornaria correlações negativas indistinguíveis das positivas — um *hedge* pareceria co-movimento.

### 4. Elementos complementares
- **Colorbar** para a correlação, com `Normalize(vmin=-1, vmax=1)`.
- **Legenda** para estilo de aresta (cointegrado vs. não).
- **Título** e remoção dos eixos (`ax.axis('off')`).

### 5. Pipeline
```
dados carregados pelos combos globais (periodo + amostragem)
   → series de preco (LastPric) por ticker, filtradas pelo Listbox
   → alinhamento por interseção de datas (grade compartilhada)
   → retornos entre observacoes consecutivas
   → matriz de correlacao (assinada)
   → matriz de cointegracao (Engle-Granger + ADF, numpy puro; indicio)
   → filtro de arestas
   → construcao do grafo (networkx)
   → spring_layout(seed=42)
   → desenho (matplotlib)
   → salvar/copiar figura (PNG)
```

### 6. Código de referência
```python
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

def build_graph(tickers, corr_matrix, coint_matrix, corr_threshold=0.5):
    G = nx.Graph()
    G.add_nodes_from(range(len(tickers)))
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            corr = corr_matrix[i, j]
            coint = coint_matrix[i, j]
            if abs(corr) > corr_threshold or coint:
                G.add_edge(i, j, corr=corr, coint=coint)
    return G

def plot_network(G, tickers, clusters, seed=42):
    pos = nx.spring_layout(G, seed=seed, k=0.5)
    fig, ax = plt.subplots(figsize=(14, 10))

    nx.draw_networkx_nodes(
        G, pos, node_color=clusters, cmap=plt.cm.tab20,
        node_size=300, ax=ax
    )

    edges = list(G.edges(data=True))
    corrs  = [d['corr'] for _, _, d in edges]           # assinado (-1..1)
    widths = [3 if d['coint'] else 1 for _, _, d in edges]
    styles = ['solid' if d['coint'] else 'dashed' for _, _, d in edges]

    nx.draw_networkx_edges(
        G, pos, width=widths, style=styles,
        edge_color=corrs, edge_cmap=plt.cm.coolwarm,
        edge_vmin=-1.0, edge_vmax=1.0,
        alpha=0.6, ax=ax
    )
    nx.draw_networkx_labels(
        G, pos, labels={i: t for i, t in enumerate(tickers)},
        font_size=8, ax=ax
    )

    norm = plt.Normalize(vmin=-1.0, vmax=1.0)
    sm = plt.cm.ScalarMappable(cmap=plt.cm.coolwarm, norm=norm)
    sm.set_array(corrs)
    plt.colorbar(sm, ax=ax, label='Correlação (amostragem selecionada)')
    ax.set_title("Rede: correlação (curto prazo) × cointegração (longo prazo)")
    ax.axis('off')
    return fig, ax
```

> O parâmetro `style` aceita uma lista por aresta no `networkx` (confirmado na documentação), portanto sólidas/tracejadas por par são válidas.

---

## E — Evaluate (Avaliação)

### Critérios de sucesso
| Critério | Como verificar |
|---|---|
| Escala para dezenas de nós | Testar com N=30, 50, 80; medir tempo de layout e legibilidade |
| Diferencia curto vs. longo prazo | Inspeção visual: arestas coloridas (assinadas) vs. espessas/tracejadas |
| Revela clusters | Comparar agrupamento visual com comunidades calculadas |
| Reprodutível | `seed` fixo → mesma figura para a mesma grade de observações |
| Integrável ao pipeline | Consome `_current_data`; funções puras; sem I/O próprio |

### Riscos e mitigações
| Risco | Mitigação |
|---|---|
| *Hairball* com muitas arestas | Aumentar limiar de correlação; usar `k` maior no layout |
| Layout instável entre execuções | Fixar `seed`; fixar a versão suportada do `networkx` |
| Performance com N grande | Pré-filtrar arestas; layout pré-computado |
| Ambiguidade visual (cor + espessura) | Legenda explícita; colormap divergente com escala fixa `[-1, +1]` |
| Cointegração mal estimada | Reportar como indício; considerar Johansen / grade densa para confirmar |
| Amostragem esparsa e irregular | Gates por número de observações; diagnóstico de gaps; orientar "Todos os dias" |

### Limitações da amostragem (devem constar na orientação)
- **Não é correlação diária**: cada observação cobre um intervalo variável de dias.
- **Fibonacci enviesa para o presente**: a leitura reflete majoritariamente o curto prazo.
- **ADF aproximado** sob espaçamento irregular: cointegração é indício, não teste estrito.
- **Limiar `0,5` não é universal**: intervalos maiores tendem a elevar a correlação; o limiar é calibrável.

### Métricas quantitativas sugeridas
- **Modularidade** da partição em comunidades (`networkx.algorithms.community`).
- **Tempo de execução** do layout para N crescente.
- **Densidade** da rede após filtro (arestas / arestas possíveis).
- **N de observações e gaps** (mín/mediana/máx em dias úteis) efetivamente usados.

### Alternativas de fallback
- Se a rede ficar densa demais: usar **heatmap + dendrograma** (Opção 3) como figura auxiliar futura, não substituto — **fora do escopo desta versão**.
- Se precisar de interatividade: migrar a camada de desenho para **Plotly** mantendo o layout do `networkx`.

### Decisão
**Prosseguir com a Opção 1**, com os complementos (colorbar, legenda, clusters por cor de nó), consumindo os dados já carregados pelos combos globais e calculando correlação/cointegração em `numpy` puro (sem `statsmodels`/`scipy`). A Opção 3 fica como trabalho futuro.

---

## Próximos passos
1. Mapear `_current_data` → séries de preço alinhadas (grade compartilhada de datas).
2. Implementar `build_graph`, `plot_network` e o cálculo de cointegração (Engle-Granger + ADF em `numpy`).
3. Calcular comunidades da rede para colorir os nós e a modularidade da partição.
4. Registrar a sub-aba "Rede de Correlação" na "Análise Geral" e garantir o recálculo ao mudar período/amostragem.
5. Cobrir a matemática com testes e rodar o quality gate completo.

Se quiser, posso detalhar a etapa de cálculo de cointegração (Engle-Granger com ADF) ou as comunidades para colorir os nós.
