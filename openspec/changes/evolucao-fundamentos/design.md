## Context

Ver `proposal.md` — Why e `specs/` para os requisitos. Restrições relevantes:

- A porta `FundamentalHistoryStore` já expõe `datas(ticker)` (ascendente, dentro da retenção de 365 dias) e `historico(ticker, inicio, fim)` (observações datadas, tolerantes a versões antigas), com implementação `JsonFundamentalHistoryStore`.
- A sub-aba "Fundamentos" é a `FundamentalTablePanel` (`charts/fundamental_table.py`), com dois `ttk.Treeview` sincronizados (fixo e rolável) que compartilham o `iid` do ticker.
- As sub-abas de "Análise do Ticker" são criadas por `TAB_CONFIGS`/`ENABLED_TABS` (`app_tabs.py`) e construídas em `_build_ticker_tabs` (`app_tab_layout.py`); os painéis gráficos usam `FigureCanvasTkAgg`, `ToolbarBR` e `empty_state`.
- O `_on_tab_changed` (`app_tab_actions.py`) resolve o painel por `(main_tab, sub_tab)` e chama `_do_update`, hoje só quando `self._current_data` é verdadeiro.
- O store é criado em `_wire_controller` (`app.py`) e entregue ao controller; a apresentação ainda não tem referência a ele.
- O `FundamentusProvider` ignora `reference_date`: a data-chave é a data de carga, então as séries refletem os dias em que o usuário carregou, não o histórico de mercado.

## Goals / Non-Goals

**Goals:**

- Painel de small multiples alimentado só pelo cache histórico, preenchido de forma preguiçosa.
- Amostragem Fibonacci acumulada, determinística e testável, isolada do código de desenho.
- Duplo clique na tabela de Fundamentos ativando a nova sub-aba com o ticker correto.
- Funcionar sem carga B3 corrente e com estado vazio explícito.

**Non-Goals:**

- Qualquer aquisição de rede ou enriquecimento com outros caches (preço B3, dividendos, CVM).
- Alterar a retenção, o schema ou a política de escrita do cache histórico.
- Novos controles de período/amostragem para a evolução; a amostragem é fixa em Fibonacci acumulado.
- Exportar a evolução em CSV.

## Decisions

### 1. Amostragem Fibonacci acumulada com aproximação para a data mais próxima

A partir de `datas = store.datas(ticker)` (ascendente), inclui-se sempre `datas[0]` e `datas[-1]`. Caminha-se para trás a partir de `datas[-1]`, com gaps sucessivos `1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377`; cada alvo `atual - gap` é aproximado para a data de cache mais próxima ainda não usada; o processo para quando o alvo alcança ou ultrapassa `datas[0]`. Datas duplicadas são descartadas e o resultado é ordenado de forma crescente.

Alternativas descartadas: offsets absolutos a partir do mais recente (colapsa em poucos pontos quando o cache é esparso) e reutilizar o sampler de B3 (`infrastructure/b3/generators.py`), que trabalha sobre uma data de referência fixa e um período, não sobre as datas existentes no cache.

### 2. Small multiples em vez de eixo único ou índice base 100

Sete campos com unidades incompatíveis (R$, razão, %, contagem) são exibidos em sete mini-gráficos de linha, com eixo de datas compartilhado e escala vertical própria. É a opção que preserva o valor absoluto e evita a leitura enganosa de sobrepor unidades.

Alternativas descartadas: eixo único com escalas misturadas (enganoso) e índice normalizado base 100 (compara formas, mas esconde o valor real — ruim para leigo).

### 3. Eixo X temporal real

As datas amostradas são posicionadas em um eixo de datas real (matplotlib), de modo que os intervalos Fibonacci crescentes apareçam visualmente. Alternativa descartada: posições categóricas equidistantes, que escondem a intenção da amostragem.

### 4. Separar cálculo de dados do painel de desenho

`charts/fundamental_evolution_data.py` concentra funções puras — seleção Fibonacci das datas e montagem das séries por campo (com lacunas para valores ausentes) — e `charts/fundamental_evolution_panel.py` cuida apenas da figura, do estado vazio e da formatação. Motivo: a amostragem é a parte com regra de negócio e precisa de teste unitário sem Tk/matplotlib.

### 5. Painel passivo; a GUI resolve a fonte

O painel expõe `update(series)` e recebe dados já preparados. Em `_wire_controller`, o GUI guarda `self._fundamental_history_store`; `_do_update` ganha um caso para o painel de evolução que lê `datas`/`historico` e chama o montador. Motivo: o painel é construído antes do store existir (`_build_main_area` antecede `_wire_controller`) e o desenho fica desacoplado da infraestrutura.

### 6. Duplo clique via callback na tabela

`FundamentalTablePanel` ganha o callback opcional `on_row_activated(ticker)`, associado a `<Double-1>` nos dois `Treeview` (o `iid` é o ticker em ambos). O handler na GUI fixa `self._evolution_ticker`, seleciona a aba "Análise do Ticker" e a sub-aba "Evolução dos Fundamentos"; a troca dispara `<<NotebookTabChanged>>` e o preenchimento preguiçoso.

Alternativa descartada: sincronizar programaticamente a seleção da `TickerList`, que dispararia `on_ticker_edit` e efeitos colaterais de recarga.

### 7. Ticker fixado pelo duplo clique, com fallback para a seleção

O painel usa `self._evolution_ticker` quando definido; caso contrário, usa o ticker selecionado na `TickerList` (mesma regra das demais sub-abas). Ao usuário alterar a seleção na `TickerList`, `on_ticker_edit` limpa `_evolution_ticker` para o painel voltar a seguir a lista. O pin evita que o duplo clique seja sobrescrito pela seleção corrente no momento da troca de aba.

### 8. Escapar do gate de `_current_data`

Em `_on_tab_changed`, o painel de evolução é atualizado mesmo com `_current_data` vazio; os demais gráficos mantêm o gate. Motivo: o requisito é funcionar só com o cache. Alternativa descartada: remover o gate global, que arriscaria os painéis dependentes de B3.

### 9. Campos e origem

Cotação → `analise.cotacao`; VP → `analise.vp_cota`; P/VP → `analise.metricas.p_vp`; Dividend Yield → `analise.metricas.dividend_yield`; Último dividendo → `analise.ultimo_dividendo.valor`; Nº de cotistas → `analise.cotistas`; Nº de cotas → `analise.cotas`. Valores ausentes viram lacunas; campo sem nenhum valor exibe "sem dado" no seu painel. Formatação reaproveita `fundamental_formatters` (reais, percentual, quantidade/inteiro).

### 10. Texto orientativo e documentação

Nova entrada em `TAB_CONTENT` (`app_tabs.py`) com objetivo, pergunta, indicadores e como interpretar, no padrão existente; `panels.md` ganha a descrição da sub-aba.

### 11. Respiro entre o título e a primeira fileira de painéis

O título geral da figura é posicionado de forma a deixar o equivalente a uma linha de texto (altura dos caracteres do título, 11 pt) de espaço em branco até os dois primeiros gráficos. Na prática, o `top` do layout é reduzido para criar essa folga. Motivo: o título encostava na primeira fileira e prejudicava a leitura dos painéis superiores. Alternativa descartada: reduzir a fonte do título, que pioraria a legibilidade.

## Risks / Trade-offs

- [Cache esparso e vários campos quase constantes, já que a chave é a data de carga] → estado vazio quando não há histórico, contagem de datas exibida no título e texto orientativo explicando que a série reflete as observações carregadas.
- [Observações de schema antigo com campos ausentes] → leitura tolerante do store já devolve o que existe; campos ausentes viram lacunas, sem quebrar o painel.
- [Amostra degenerar em poucas datas quando o cache tem poucos pontos] → a Leitura A prioriza os extremos e não repete datas; o painel funciona com 1 ou 2 pontos.
- [Duplo clique apenas em um dos `Treeview`] → bind nos dois, com o mesmo `iid` do ticker.
- [Leitura de disco na thread do Tk ao trocar de sub-aba] → arquivos pequenos (até 365 observações) e leitura única por seleção; aceitável.
- [Painel de evolução e demais gráficos no mesmo `_do_update`] → caso explícito no despacho, mantendo o gate de `_current_data` para os demais.

## Migration Plan

Nenhuma migração: mudança aditiva, só leitura do cache existente. Rollback = reverter os arquivos e remover a sub-aba do registro; nenhum dado é criado ou alterado.

## Open Questions

- Formato e quantidade dos rótulos de data no eixo (dd/mm vs mm/aaaa) e limite de rótulos para evitar poluição — puramente cosmético, ajustável na implementação sem mudar specs ou abordagem.
