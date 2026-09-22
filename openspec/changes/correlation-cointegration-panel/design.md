## Context

A RFC-013 propõe um grafo de correlação/cointegração, mas assume séries diárias contíguas e as bibliotecas `networkx` + `statsmodels`. O FlowScope atual: (a) entrega preços por amostragem (Fibonacci = 7 datas com gaps por padrão), (b) usa apenas `numpy`/`matplotlib` — `numpy` sequer é importado em `src/`, e (c) mantém um cache em disco **sem TTL** (`~/.cache/flowscope/*.csv`) e um cache histórico de fundamentos com retenção de 365 dias. Ver `proposal.md` para a motivação. As sub-abas da "Análise Geral" seguem o padrão painel + `*_data.py` + registro em quatro pontos (`app_tab_layout`, `app_layout`, `app_tabs`, `app_actions`).

## Goals / Non-Goals

**Goals:**
- Materializar a RFC-013 como sub-aba da "Análise Geral" com codificação visual dupla (cor = correlação, estilo/espessura = cointegração).
- Calcular correlação e cointegração em `numpy` puro, sem `statsmodels`/`scipy`.
- Usar exclusivamente dados já em cache local, com janela própria do painel.
- Manter a matemática sob o quality gate (cobertura ≥ 85% e mutation testing), fora de `presentation/gui/`.

**Non-Goals:**
- Download de rede ou aquecimento de cache específico para o painel.
- Heatmap + dendrograma complementar (Opção 3 da RFC) — pode vir depois.
- Correção de múltiplos testes (FDR) na primeira versão.
- Interatividade (Plotly/PyVis) ou substituição do ecossistema Matplotlib.
- Alterar a amostragem global ou o comportamento de painéis existentes.

## Decisions

### 1. Fonte de dados: cache da B3, somente leitura, janela própria

A fonte primária é o cache diário da B3, lido em modo cache-only. O painel tem seu **próprio seletor de janela** (90/180/252 pregões), independente do combo global de período/amostragem — porque a amostragem global entrega poucos pontos com gaps, inviabilizando retornos diários.

Para a janela, o leitor lista os arquivos `~/.cache/flowscope/*.csv`, filtra dias úteis e toma os N mais recentes. Isso evita converter "pregões" em `period_days` (calendário) e não depende da máquina de amostragem.

- **Alternativa considerada**: reusar `_current_data["daily_data"]` (amostragem global). Rejeitada: `pct_change` sobre datas com gap não é retorno diário, e n cai para ~7–30.
- **Alternativa considerada**: `SamplingConfig(method="all_days", period_days=…)`. Rejeitada por acoplar a janela ao calendário e reusar a resolução de datas.

### 2. Leitor de histórico com fonte única e fallback

Novo leitor em `infrastructure/` (porta em `application/`) monta `dict[ticker, list[(data, preco)]]`. Fonte primária: último preço (`LastPric`) do CSV da B3. Fallback: `cotacao` do cache histórico de fundamentos, quando a B3 não der densidade. A escolha é **única por execução** — nunca misturar fontes entre tickers, pois `LastPric` e `cotacao` têm semânticas diferentes e enviesariam a correlação.

Adiciona-se `CacheManager.list_dates()` (datas com arquivo diário em cache) para o leitor enumerar a janela sem varrer o disco a cada data.

### 3. Cointegração em `numpy` puro: Engle-Granger com N=2

Como as arestas são par-a-par, o Engle-Granger sempre tem **um regressor + constante**, então só são necessários os valores críticos de MacKinnon para **N=2** — uma tabela pequena e auditável — em vez de uma implementação geral de ADF.

Por par:
1. OLS `y = a + b·x` via `np.linalg.lstsq` → resíduo `e_t` (spread).
2. ADF: regride `Δe_t` sobre `e_{t-1}` (+ constante + defasagens `Δe_{t-i}`); `t-stat` do coeficiente de `e_{t-1}`.
3. Compara com os críticos de MacKinnon N=2 (constante, sem tendência): 1% ≈ −3,90; 5% ≈ −3,34; 10% ≈ −3,04, com correção de amostra finita via superfície de resposta.

Ordem de defasagem por BIC sobre `p` em `0..p_max`, com `p_max = min(4, floor(12·(n/100)^0,25))`. Nível de significância padrão: 5%.

- **Alternativa considerada**: `statsmodels.coint`. Rejeitada pelo custo do binário (puxa `pandas`/`scipy`/`patsy`) e pela preferência por `numpy`.
- **Alternativa considerada**: half-life AR(1) apenas. Mantida como **complemento**, não substituto: é mais robusta em n baixo e vira número interpretável ("reverte em ~N dias").
- **Risco aceito**: ADF tem baixo poder em n≈60. O gate de densidade e o half-life mitigam a leitura equivocada.

### 4. Grafo, layout e comunidades com `networkx`

`networkx` (Python puro, leve) fornece `spring_layout(seed=42)`, detecção de comunidades determinística (`greedy_modularity_communities`), centralidade (`degree`) e `modularity` — cobrindo cor do nó (cluster), tamanho (centralidade) e a métrica de sucesso da RFC sem `scipy`.

- **Alternativa considerada**: reimplementar Fruchterman-Reingold e label propagation em `numpy` (~60 linhas). Rejeitada por reimplementar o que `networkx` já faz e por perder `modularity` pronta.

### 5. Camadas: matemática no domínio, sob o quality gate

`pyproject.toml` exclui `presentation/gui/*` da cobertura (`fail_under=85`) e do mutation testing. Um ADF sutilmente errado ali passaria batido. Por isso a matemática fica em `domain/network_analysis.py` (coberto e mutado); o I/O em `infrastructure/`; a orquestração em `application/`; e o painel/desenho em `presentation/gui/charts/`.

- **Nota**: hoje `domain/` não usa `numpy` (é Python puro/Decimal). Introduzir `numpy` no domínio é um padrão novo, aceito por ser análise reutilizável e por precisar do gate. Alternativa (matemática em `application/`) também é coberta, mas mistura orquestração com cálculo.

### 6. Carga em background, cálculo na thread principal

O gargalo é o **parse dos CSVs** (até 252 arquivos), não a matemática (1.225 `lstsq` pequenos ≈ < 1 s). A leitura do histórico roda em job com fila, no padrão de `documentos_job.py`/`fundamental_job.py`, para não travar o Tk; correlação/cointegração/desenho rodam na thread do Tk após o resultado.

### 7. Gates de densidade e estados

- `MIN_OBS_CORR = 30` (pares de retorno) → abaixo: estado vazio.
- `MIN_OBS_COINT = 60` (níveis alinhados) → abaixo: só correlação + aviso.
- Alinhamento por interseção de datas; `n` efetivo reportado no painel e na orientação.

### 8. Codificação visual e determinismo

Cor da aresta = `|correlação|` com colormap divergente + colorbar; estilo/espessura = cointegração (sólida/grossa vs. tracejada/fina) + legenda; cor do nó = cluster; tamanho = centralidade. Layout com `seed` fixo; limiar de correlação padrão `|corr| > 0,5`, ajustável por constante.

## Risks / Trade-offs

- **Falso positivo por múltiplos testes** (1.225 pares a 5%) → mitigação: documentar na orientação; FDR fica como trabalho futuro; considerar 1% como crítico em redes grandes.
- **ADF com baixo poder em n≈60** → mitigação: gate n ≥ 60 e half-life como leitura complementar.
- **Cache raso/incompleto** → mitigação: fonte única + fallback de fundamentos, reporte explícito de cobertura e estado vazio honesto.
- **Engle-Granger é direcional** (A sobre B ≠ B sobre A) → mitigação: fixar uma direção determinística e documentar.
- **Mistura FII + ação na watchlist** → mitigação: não filtrar, mas sinalizar na orientação que classes distintas podem gerar relações espúrias.
- **`numpy` no domínio quebra o padrão Python puro** → mitigação: isolar em um módulo de análise, com testes de propriedades e valores conhecidos.
- **Determinismo dependente da versão do `networkx`** → mitigação: fixar `seed`, documentar a versão suportada e cobrir com teste de repetibilidade.
- **Empacotamento PyInstaller** → mitigação: adicionar `numpy`/`networkx` às dependências e `networkx` aos `hiddenimports`; validar o build.

## Migration Plan

Mudança puramente aditiva: nova sub-aba e novos módulos; nenhum painel ou fluxo existente é alterado. Deploy = atualizar dependências e reconstruir o binário. Rollback = remover a sub-aba e os módulos novos. Sem migração de dados.

## Open Questions

- Qual o valor final do limiar de correlação padrão (`0,5`) e se deve ser exposto ao usuário ou mantido como constante.
- Se a janela padrão inicial deve ser 180 ou 252 pregões, dado o cache típico.
