## Context

A RFC-013 propõe um grafo de correlação/cointegração, mas assume séries diárias contíguas e as bibliotecas `networkx` + `statsmodels`. O FlowScope atual: (a) entrega preços por **amostragem** (Fibonacci = ~7 datas com gaps por padrão), (b) usa apenas `numpy`/`matplotlib` — `numpy` sequer é importado em `src/` — e (c) já expõe, por ticker, os dados diários carregados em `_current_data[ticker]["daily_data"]` (`date`, `last_price`, …). Ver `proposal.md` para a motivação.

Consequência central: **não existe grade diária contígua**. Os combos globais de período e amostragem definem as datas disponíveis. Como o cache da B3 é uma grade compartilhada por todo o mercado (um arquivo por data contém todos os tickers), todos os papéis compartilham as mesmas observações; retornos entre observações consecutivas têm intervalos idênticos para todos os tickers, o que torna as correlações comparáveis. A cointegração, por sua vez, é um **indício** sob espaçamento irregular.

As sub-abas da "Análise Geral" seguem o padrão painel + `*_data.py` + registro em quatro pontos (`app_tab_layout`, `app_layout`, `app_tabs`, `app_actions`).

## Goals / Non-Goals

**Goals:**
- Materializar a RFC-013 como sub-aba da "Análise Geral" com codificação visual dupla (cor = correlação assinada, estilo/espessura = cointegração).
- Calcular correlação e cointegração em `numpy` puro, sem `statsmodels`/`scipy`.
- Consumir os dados **já carregados** pelos combos globais (período + amostragem), filtrados pelo Listbox, com recálculo ao mudá-los.
- Manter a matemática sob o quality gate (cobertura ≥ 85%), fora de `presentation/gui/`.

**Non-Goals:**
- Janela/seletor próprio do painel, leitor de cache próprio, download ou job em background.
- Fallback para o cache histórico de fundamentos (grade por ticker destrói a comparabilidade).
- Heatmap + dendrograma complementar (Opção 3 da RFC) — trabalho futuro.
- Correção de múltiplos testes (FDR) na primeira versão.
- Interatividade (Plotly/PyVis) ou substituição do ecossistema Matplotlib.
- Alterar a amostragem global, os combos ou o comportamento de painéis existentes.

## Decisions

### 1. Fonte de dados: o resultado já carregado pelos combos globais

A rede lê `_current_data` (o `result` de `AnalyzeTickersUseCase.execute`, aplicado por `set_current_data`), restringindo-se aos tickers selecionados no Listbox. O mapeamento extrai `[(date, last_price)]` de `daily_data` e o painel calcula a rede a partir daí.

- **Elimina** `CacheManager.list_dates()`, o leitor de histórico em `infrastructure/`, o fallback de fundamentos e o job em background — antes previstos por assumir uma janela própria.
- **Recálculo**: mudar período/amostragem já dispara `on_load_data` → `presenter.on_result` → `set_current_data` + `on_tab_changed` → `_do_update` no painel ativo. Basta a rede estar registrada e tratada no `_do_update`.
- **Alternativa considerada**: manter uma janela própria (90/180/252 pregões) lendo o cache. Rejeitada: ignora os combos escolhidos pelo usuário, duplica leitura/estado e não resolve a esparsidade (o cache também tem gaps).

### 2. Alinhamento global por interseção de datas

As séries são alinhadas por **interseção de datas** entre os tickers considerados. Como a grade é compartilhada, isso preserva **intervalos idênticos para todos os pares**, tornando as correlações comparáveis entre si.

- **Alternativa considerada**: alinhamento par-a-par (pairwise). Dá mais cobertura, mas cada par passaria a usar intervalos diferentes, quebrando a comparabilidade — justamente o que um painel de rede precisa.

### 3. Cointegração em `numpy` puro: Engle-Granger com 2 variáveis

Como as arestas são par-a-par, o Engle-Granger sempre tem **um regressor + constante**, então só são necessários os valores críticos de MacKinnon para **2 variáveis** (aqui `T` é o número de observações da superfície de resposta, e `2` é o número de variáveis) — uma tabela pequena e auditável, em vez de uma implementação geral de ADF.

Por par:
1. OLS `y = a + b·x` via `np.linalg.lstsq` → resíduo `e_t` (spread).
2. ADF: regride `Δe_t` sobre `e_{t-1}` (+ constante + defasagens `Δe_{t-i}`); usa o `t-stat` do coeficiente de `e_{t-1}`.
3. Compara com os críticos de MacKinnon (constante, sem tendência; 2 variáveis): 1% ≈ −3,90; 5% ≈ −3,34; 10% ≈ −3,04, com correção de amostra finita pela superfície de resposta de MacKinnon. Sob espaçamento irregular, o resultado é tratado como **indício**.

Ordem de defasagem por BIC sobre `p` em `0..p_max`, com `p_max = min(4, floor(12·(T/100)^0,25))`. Nível de significância padrão: 5%.

- **Alternativa considerada**: `statsmodels.coint`. Rejeitada pelo custo do binário (puxa `pandas`/`scipy`/`patsy`) e pela preferência por `numpy`.
- **Alternativa considerada**: half-life AR(1) apenas. Mantida como **complemento**, não substituto: é mais robusta em `T` baixo e vira número interpretável.
- **Risco aceito**: ADF tem baixo poder em `T`≈40–60 e assume espaçamento regular. Os gates e o half-life mitigam a leitura equivocada; a orientação rotula "indício".

### 4. Grafo, layout e comunidades com `networkx`

`networkx` (Python puro, leve) fornece `spring_layout(seed=42)`, detecção de comunidades determinística (`greedy_modularity_communities`), centralidade (`degree`) e `modularity` — cobrindo cor do nó (comunidade), tamanho (centralidade) e a métrica de sucesso da RFC sem `scipy`.

- **Alternativa considerada**: reimplementar Fruchterman-Reingold e label propagation em `numpy` (~60 linhas). Rejeitada por reimplementar o que `networkx` já faz e por perder `modularity` pronta.

### 5. Camadas: matemática no domínio, sob o quality gate

`pyproject.toml` exclui `presentation/gui/*` da cobertura (`fail_under=85`). Um ADF sutilmente errado ali passaria batido. Por isso a matemática fica em `domain/network_analysis.py` (coberto por testes); o mapeamento `_current_data` → séries alinhadas fica no módulo de dados do painel (`presentation/gui/charts/`); e o painel/desenho em `presentation/gui/charts/`.

- **Nota**: hoje `domain/` não usa `numpy` (é Python puro/Decimal). Introduzir `numpy` no domínio é um padrão novo, aceito por ser análise reutilizável e por precisar do gate.

### 6. Cálculo na thread do Tk

A carga dos CSVs (download/parse) já ocorreu no fluxo normal da análise. A rede apenas mapeia `_current_data` e roda a matemática (1.225 `lstsq` pequenos) e o desenho — custo baixo, na thread do Tk. **Não há job em background.**

### 7. Gates por número de observações e diagnósticos de amostragem

- `MIN_OBS_CORR = 30` (observações alinhadas) → abaixo: estado vazio.
- `MIN_OBS_COINT = 40` (observações alinhadas) → abaixo: só correlação + aviso de que a cointegração requer mínimo de 40 observações.
- O resultado reporta `T` (observações), span de calendário e gaps (mín/mediana/máx em dias úteis), exibidos no painel/orientação.

### 8. Codificação visual e determinismo

Cor da aresta = **correlação assinada** em colormap divergente com `Normalize(vmin=-1, vmax=1)` + colorbar; estilo/espessura = cointegração (sólida/grossa vs. tracejada/fina) + legenda; cor do nó = comunidade; tamanho = centralidade. Layout com `seed` fixo; limiar de correlação padrão `|corr| > 0,5`, ajustável por constante.

### 9. Estado vazio legível: quebra de linha automática

As mensagens de estado vazio (em especial "Poucas observações alinhadas…", com ~121 caracteres) transbordam a figura de 700 px quando desenhadas em uma única linha. O rótulo de estado vazio do painel habilita `wrap=True`, de modo que a mensagem é quebrada em múltiplas linhas e permanece inteiramente visível dentro da janela, preservando o texto completo (sem depender da barra de status). O texto passa a ser, na prática, multilinha, e o ajuste acompanha a largura da figura quando a janela é redimensionada.

### 10. Toolbar compartilhada com o VWAP

O painel reutiliza a mesma `ToolbarBR` da sub-aba VWAP (instanciada com `copy_chart_callback`), sem criar controles próprios. Isso garante paridade de estilo e de funcionalidades — Início, Voltar, Avançar, Mover, Ampliar, Salvar e "Copiar Gráfico" — além das regras de exclusividade entre Mover/Ampliar e do desmarcar ambos pelo Início, já encapsuladas na classe. A decisão evita duplicar comportamento e mantém uma única fonte de verdade da barra de ferramentas. Um teste de paridade trava a igualdade de `toolitems`/botões em relação ao VWAP.

**Ordem de empacotamento:** o canvas era empacotado antes da toolbar e a figura da rede é retrato (aspecto 7:6), mais alta que a do VWAP (5:3). Em janelas baixas, o canvas (`fill="both", expand=True`) reivindicava toda a altura do frame e a toolbar ficava espremida a ~1 px — invisível no app real, embora presente no widget tree. A correção empacota a toolbar (`side=BOTTOM`) **antes** do canvas, reservando a altura da barra e deixando o restante para a figura, independentemente da proporção da figura e da altura da janela. Um teste de regressão usa janela baixa e verifica que a toolbar permanece mapeada e com altura útil.

## Risks / Trade-offs

- **Não é correlação diária; amostragem esparsa/irregular** → mitigação: docs/orientação explícitas; retornos entre observações; gates por observações.
- **ADF com baixo poder e espaçamento irregular** → mitigação: rotular como indício; gate ≥ 40; half-life complementar; orientar "Todos os dias" para densificar o cache via o fluxo de carga existente.
- **Fibonacci enviesa para o presente** → mitigação: documentar que a leitura é majoritariamente de curto prazo.
- **Falso positivo por múltiplos testes** (1.225 pares a 5%) → mitigação: documentar na orientação; FDR fica como trabalho futuro; considerar 1% em redes grandes.
- **Engle-Granger é direcional** (A sobre B ≠ B sobre A) → mitigação: fixar uma direção determinística (ex.: ordem alfabética dos tickers) e documentar.
- **Mistura FII + ação na watchlist** → mitigação: não filtrar, mas sinalizar na orientação que classes distintas podem gerar relações espúrias.
- **`numpy` no domínio quebra o padrão Python puro** → mitigação: isolar em um módulo de análise, com testes de propriedades e valores conhecidos.
- **Determinismo dependente da versão do `networkx`** → mitigação: fixar `seed`, fixar a versão suportada (`networkx>=3,<4`) e cobrir com teste de repetibilidade.
- **Empacotamento PyInstaller** → mitigação: adicionar `numpy`/`networkx` às dependências e `networkx` aos `hiddenimports`; validar o build.

## Migration Plan

Mudança puramente aditiva: nova sub-aba e novos módulos; nenhum painel ou fluxo existente é alterado. Deploy = atualizar dependências e reconstruir o binário. Rollback = remover a sub-aba e os módulos novos. Sem migração de dados.

## Open Questions

- Qual o valor final do limiar de correlação padrão (`0,5`) e se deve ser exposto ao usuário ou mantido como constante.
- Se o gate de cointegração (`40`) deve subir para `60`, aceitando que exija "Últimos 90 dias + Todos os dias".
