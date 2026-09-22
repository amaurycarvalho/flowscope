# RFC-013: Visualização Topológica de Correlação e Cointegração entre Papéis com `networkx` + `matplotlib`

**Data:** 2026-09-22
**Status:** Proposto
**Componente:** Módulo de análise de redes de ativos

---

## P — Problem (Problema)

Precisamos visualizar simultaneamente, para **dezenas de papéis** (ações), duas relações distintas e frequentemente conflitantes:

1. **Correlação de curto prazo** — co-movimento dos retornos diários.
2. **Cointegração de longo prazo** — vínculo de equilíbrio entre os preços que faz o *spread* reverter à média.

Além disso, o analista precisa **identificar agrupamentos naturais** (clusters) de papéis semelhantes, enxergando a topologia da rede como um todo — não apenas pares isolados. A matriz de correlação N×N (para N=50, são 1.225 pares) é ilegível como tabela. Precisamos de uma representação visual que:

- Mostre a **estrutura global** (quem se agrupa com quem).
- Diferencie **curto prazo** de **longo prazo** na mesma imagem.
- Escale para dezenas de nós sem virar um "emaranhado" (hairball).
- Seja reproduzível e integrável ao pipeline Python existente.

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
- **Prós**: layout "constelação" emerge naturalmente; controle total de cor/tamanho/estilo; integra-se ao Matplotlib; `networkx` é maduro e amplamente usado.
- **Contras**: dependência extra (`networkx`); layouts force-directed são não-determinísticos (exigem `seed`); para N muito grande, o cálculo do layout pode ficar lento.

### Opção 2 — Matplotlib puro (MDS/t-SNE + `scatter`/`plot`)
- **Como funciona**: posiciona os nós em 2D via `sklearn.manifold.MDS` ou `TSNE`, depois desenha arestas com `ax.plot()`/`ConnectionPatch` e nós com `ax.scatter()`.
- **Prós**: zero dependências de grafos.
- **Contras**: reimplementa o que o `networkx` já faz; mais código; layout precisa ser gerenciado manualmente; sem semântica de grafo (graus, centralidade, etc.).

### Opção 3 — Heatmap + dendrograma (sem grafo)
- **Como funciona**: `imshow`/`pcolormesh` da matriz de correlação ordenada por clustering hierárquico, com `scipy.cluster.hierarchy.dendrogram`.
- **Prós**: simples, determinístico, ordenado.
- **Contras**: não mostra a topologia como "teia"; não representa bem cointegração simultaneamente; não é o estilo visual desejado.

### Opção 4 — Bibliotecas de visualização de grafos interativas (Plotly, PyVis, Graphviz)
- **Prós**: interatividade, layouts prontos.
- **Contras**: foge do ecossistema Matplotlib pedido; menos controle fino de estilo; dependências pesadas.

---

## B — Better Solution (Melhor Solução)

**Adotar a Opção 1: `networkx` + `matplotlib`**, com as seguintes decisões de design:

### 1. Construção do grafo
- **Nós** = papéis (tickers).
- **Arestas** = pares com relação relevante, filtradas por limiar (ex.: `|corr| > 0.5` ou cointegração significativa em p < 0.05) para evitar *hairball*.
- Cada aresta carrega **dois atributos**: `corr` (curto prazo) e `coint` (longo prazo, booleano ou p-valor).

### 2. Layout
- `nx.spring_layout(G, seed=42, k=...)` para o efeito "constelação".
- `seed` fixo garante reprodutibilidade.
- Ajustar `k` (distância ótima entre nós) conforme densidade da rede.

### 3. Codificação visual dupla
| Informação | Canal visual |
|---|---|
| Correlação de curto prazo | **Cor da aresta** (colormap divergente, ex.: `coolwarm`) |
| Cointegração de longo prazo | **Espessura** (mais grossa) e/ou **estilo** (sólida vs. tracejada) |
| Força da relação | **Alpha** da aresta |
| Cluster de semelhantes | **Cor do nó** (via `tab20` ou clusters de correlação) |
| Importância/centralidade | **Tamanho do nó** (opcional, ex.: grau ou betweenness) |

### 4. Elementos complementares
- **Colorbar** para a correlação.
- **Legenda** para estilo de aresta (cointegrado vs. não).
- **Título** e remoção dos eixos (`ax.axis('off')`).

### 5. Pipeline
```
preços alinhados
   → retornos (pct_change)
   → matriz de correlação
   → matriz de cointegração (Engle-Granger + ADF)
   → filtro de arestas
   → construção do grafo (networkx)
   → spring_layout
   → desenho (matplotlib)
   → salvar figura (PNG/SVG)
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
    corrs   = [abs(d['corr']) for _, _, d in edges]
    widths  = [3 if d['coint'] else 1 for _, _, d in edges]
    styles  = ['solid' if d['coint'] else 'dashed' for _, _, d in edges]

    nx.draw_networkx_edges(
        G, pos, width=widths, style=styles,
        edge_color=corrs, edge_cmap=plt.cm.coolwarm,
        alpha=0.6, ax=ax
    )
    nx.draw_networkx_labels(
        G, pos, labels={i: t for i, t in enumerate(tickers)},
        font_size=8, ax=ax
    )

    sm = plt.cm.ScalarMappable(cmap=plt.cm.coolwarm)
    sm.set_array(corrs)
    plt.colorbar(sm, ax=ax, label='Correlação (curto prazo)')
    ax.set_title("Rede: correlação (curto prazo) × cointegração (longo prazo)")
    ax.axis('off')
    return fig, ax
```

---

## E — Evaluate (Avaliação)

### Critérios de sucesso
| Critério | Como verificar |
|---|---|
| Escala para dezenas de nós | Testar com N=30, 50, 80; medir tempo de layout e legibilidade |
| Diferencia curto vs. longo prazo | Inspeção visual: arestas coloridas vs. espessas/tracejadas |
| Revela clusters | Comparar agrupamento visual com clusters calculados (hierárquico) |
| Reprodutível | `seed` fixo → mesma figura em execuções repetidas |
| Integrável ao pipeline | Funções puras, sem I/O embutido; salva via `fig.savefig()` |

### Riscos e mitigações
| Risco | Mitigação |
|---|---|
| *Hairball* com muitas arestas | Aumentar limiar de correlação; usar `k` maior no layout; filtrar por p-valor |
| Layout instável entre execuções | Fixar `seed`; documentar versão do `networkx` |
| Performance com N grande | Pré-filtrar arestas; considerar `nx.sparse_layout` ou layout pré-computado |
| Ambiguidade visual (cor + espessura) | Legenda explícita; colormap divergente bem escolhido |
| Cointegração mal estimada | Usar Engle-Granger com ADF e reportar p-valores; validar com Johansen |

### Métricas quantitativas sugeridas
- **Modularidade** da partição em clusters (via `networkx.algorithms.community`).
- **Tempo de execução** do layout para N crescente.
- **Densidade** da rede após filtro (arestas / arestas possíveis).

### Alternativas de fallback
- Se a rede ficar densa demais: usar **heatmap + dendrograma** (Opção 3) como complemento, não substituto.
- Se precisar de interatividade: migrar a camada de desenho para **Plotly** mantendo o layout do `networkx`.

### Decisão
**Prosseguir com a Opção 1**, com os complementos (colorbar, legenda, clusters por cor de nó). A Opção 3 pode ser adicionada como figura auxiliar no mesmo relatório para dar uma visão ordenada e determinística da matriz subjacente.

---

## Próximos passos
1. Implementar `build_graph`, `plot_network` e o cálculo de cointegração (Engle-Granger + ADF).
2. Calcular clusters (hierárquico sobre a matriz de correlação) para colorir os nós.
3. Testar com N=30 e N=50; ajustar `k` e limiares.
4. Adicionar heatmap + dendrograma como figura complementar.
5. Empacotar em módulo reutilizável com `savefig` e logging.

Se quiser, posso detalhar a etapa de cálculo de cointegração (Engle-Granger com ADF) ou o clustering hierárquico para colorir os nós.
