## Why

A watchlist de dezenas de papéis gera uma matriz de correlação N×N (para N=50, 1.225 pares) ilegível como tabela. O analista precisa enxergar a **topologia** — quem se agrupa com quem — e, ao mesmo tempo, distinguir o co-movimento de curto prazo (correlação de retornos) do vínculo de equilíbrio de longo prazo (cointegração do spread). Nenhuma sub-aba atual da "Análise Geral" responde a essa pergunta: VWAP, Quadrantes e Dominância do Pregão são todos univariados por pregão. Esta change materializa a RFC-013 como um painel de rede cross-seccional.

## What Changes

- Nova sub-aba **"Rede de Correlação"** na "Análise Geral", com grafo force-directed (nós = papéis, arestas = pares com relação relevante).
- Codificação visual dupla: **cor da aresta** = correlação de curto prazo (colormap divergente); **estilo/espessura** = cointegração de longo prazo (traço sólido/grosso quando cointegrado, tracejado/fino caso contrário).
- **Cor do nó** = cluster (comunidades da rede); **tamanho do nó** = centralidade (grau), opcional.
- Cálculo de correlação e cointegração (Engle-Granger + ADF) **implementado em `numpy` puro**, sem `statsmodels`/`scipy`.
- Fonte de dados **exclusivamente de cache local** (CSVs diários da B3 já baixados), com seletor de janela próprio do painel (90/180/252 pregões), independente do combo global de amostragem.
- **Gate de densidade**: a cointegração só é calculada com observações alinhadas suficientes (n ≥ 60); abaixo disso, o painel exibe apenas as arestas de correlação com aviso explícito.
- `networkx` adicionado como dependência para layout (`spring_layout`), detecção de comunidades e centralidade.
- Leitor read-only de histórico de preços alinhados a partir do cache B3, com o cache histórico de fundamentos (`cotacao`) como fonte alternativa do painel inteiro.
- Texto de orientação (OrientationPanel) e suporte ao botão "Copiar Gráfico" para a nova sub-aba.
- Sem remoção ou alteração de comportamento dos painéis existentes.

## Capabilities

### New Capabilities
- `correlation-network-panel`: Sub-aba "Rede de Correlação" da "Análise Geral" — grafo de correlação/cointegração, codificação visual dupla, seletor de janela, gate de densidade, estados vazios e texto de orientação.
- `network-analysis`: Núcleo de cálculo puro (sem I/O e sem Tk) — alinhamento de séries de preço, retornos, matriz de correlação, cointegração par-a-par (Engle-Granger + ADF em `numpy`), half-life do spread, construção do grafo, comunidades e modularidade.
- `cached-price-history`: Montagem read-only de séries de preço alinhadas a partir dos caches locais (B3 `all_days` e cache histórico de fundamentos), sem download de rede.

### Modified Capabilities
- `gui-interface`: A "Análise Geral" passa a ter a sub-aba "Rede de Correlação" no sub-notebook, com texto de orientação próprio e registro no despacho de atualização/cópia.

## Impact

- **Dependências**: adiciona `networkx` (Python puro) e declara `numpy` explicitamente em `pyproject.toml`; atualiza `flowscope.spec` (`hiddenimports`) e `requirements.txt`.
- **Domínio**: novo módulo de análise de rede (`domain/`) — matemática coberta pelo quality gate (cobertura ≥ 85% e mutation testing).
- **Aplicação**: caso de uso/porta para montar o resultado do painel a partir do histórico de preços.
- **Infraestrutura**: leitor de histórico de preços a partir dos caches (B3 e fundamentos), somente-leitura.
- **Apresentação**: novo painel e módulo de dados em `presentation/gui/charts/`; alterações em `app_tab_layout.py`, `app_layout.py`, `app_tabs.py`, `app_actions.py`.
- **Documentação**: `panels.md` e texto de orientação.
- **Sem breaking changes**: nenhuma sub-aba ou fluxo existente é alterado.
