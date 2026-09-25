## Why

A watchlist de dezenas de papéis gera uma matriz de correlação N×N (para N=50, 1.225 pares) ilegível como tabela. O analista precisa enxergar a **topologia** — quem se agrupa com quem — e, ao mesmo tempo, distinguir o co-movimento de curto prazo (correlação) do vínculo de equilíbrio de longo prazo (cointegração do spread). Nenhuma sub-aba atual da "Análise Geral" responde a essa pergunta: VWAP, Quadrantes e Dominância do Pregão são todos univariados por pregão. Esta change materializa a RFC-013 como um painel de rede cross-seccional que **reutiliza os dados já carregados pelos combos globais de período e amostragem**, sem fonte, janela ou carga próprias.

## What Changes

- Nova sub-aba **"Rede de Correlação"** na "Análise Geral", com grafo force-directed (nós = papéis, arestas = pares com relação relevante).
- Codificação visual dupla: **cor da aresta** = correlação de curto prazo **assinada** (colormap divergente com escala fixa `[-1, +1]`); **estilo/espessura** = cointegração de longo prazo (traço sólido/grosso quando cointegrado, tracejado/fino caso contrário).
- **Cor do nó** = comunidade da rede; **tamanho do nó** = centralidade (grau), opcional.
- Cálculo de correlação e cointegração (Engle-Granger + ADF) **implementado em `numpy` puro**, sem `statsmodels`/`scipy`.
- **Fonte de dados: o resultado já carregado** na análise corrente (`_current_data`), filtrado pelos tickers selecionados no Listbox. Sem leitor de cache, sem download, sem janela própria e sem job em background.
- A rede **usa a amostragem dos combos globais** (período + amostragem) e é **recalculada automaticamente** quando eles mudam com a sub-aba ativa (pelo fluxo de atualização já existente).
- Premissa esparsa: retornos calculados entre **observações consecutivas** da grade compartilhada de datas (B3), com **diagnóstico de gaps** (mín/mediana/máx em dias úteis, span de calendário).
- **Gates por número de observações**: correlação exige ≥ 30 observações alinhadas; cointegração exige ≥ 40 e é apresentada como **indício exploratório** (o ADF assume espaçamento regular).
- `networkx` adicionado como dependência para layout (`spring_layout`), detecção de comunidades e centralidade.
- Texto de orientação (OrientationPanel) e a mesma barra de ferramentas (`ToolbarBR`) da sub-aba VWAP — Início, Voltar, Avançar, Mover, Ampliar, Salvar e "Copiar Gráfico" — para a nova sub-aba.
- Sem remoção ou alteração de comportamento dos painéis existentes.

## Capabilities

### New Capabilities
- `correlation-network-panel`: Sub-aba "Rede de Correlação" da "Análise Geral" — grafo de correlação/cointegração, codificação visual dupla, uso dos seletores globais e recálculo ao mudá-los, gates por observações, diagnósticos de amostragem, estados vazios e texto de orientação.
- `network-analysis`: Núcleo de cálculo puro (sem I/O e sem Tk) — alinhamento de séries de preço por interseção de datas, retornos entre observações consecutivas, matriz de correlação assinada, cointegração par-a-par (Engle-Granger + ADF em `numpy`), half-life do spread, construção do grafo, comunidades e modularidade.

### Modified Capabilities
- `gui-interface`: A "Análise Geral" passa a ter a sub-aba "Rede de Correlação" no sub-notebook, com texto de orientação próprio, registro no despacho de atualização/cópia e recálculo ao mudar período/amostragem.

## Impact

- **Dependências**: adiciona `networkx` (Python puro) e declara `numpy` explicitamente em `pyproject.toml`; atualiza `flowscope.spec` e `requirements.txt`.
- **Domínio**: novo módulo de análise de rede (`domain/`) — matemática coberta pelo quality gate (cobertura ≥ 85%).
- **Aplicação/Presentação**: módulo de mapeamento `_current_data` → séries alinhadas e novo painel em `presentation/gui/charts/`; alterações em `app_tab_layout.py`, `app_layout.py`, `app_tabs.py`, `app_actions.py`.
- **Sem infraestrutura nova**: nenhum leitor de cache, fallback ou job; a rede consome o resultado em memória.
- **Documentação**: `panels.md` e texto de orientação.
- **Sem breaking changes**: nenhuma sub-aba ou fluxo existente é alterado.
