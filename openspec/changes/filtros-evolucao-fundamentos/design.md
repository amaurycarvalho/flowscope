## Context

Ver `proposal.md - Why`. O estado atual e as restrições que moldam a solução:

- O painel lê `JsonFundamentalHistoryStore` e o cache guarda **uma observação por `(ticker, data_de_referência)`**, registrada apenas nos dias em que o usuário carregou dados. Não é o dataset amostrado da B3.
- `application/fundamental/evolucao.py` hoje concentra as funções puras e aplica `selecionar_datas_fibonacci` dentro de `montar_series`, sem conhecer período nem método.
- `presentation/gui/evolucao_job.py:preparar_series` lê `datas[0]..datas[-1]` (todo o retido) e não recebe configuração.
- `presentation/gui/app_actions.py` submete o job com `chave=ticker` e política `LATEST_WINS`; o scheduler **descarta** uma submissão com a mesma `chave` do job ativo (`scheduler.py:39`), logo a configuração precisa entrar na chave para uma troca de filtro substituir a leitura anterior.
- `_deve_atualizar` já trata o painel como "atualizável sem dados B3" (`app_tab_actions.py:121`); o `SamplingConfig` dos comboboxes já existe e é mapeado em `get_sampling_config` (`app_actions.py:50`).

```
  comboboxes --> get_sampling_config() --> (period_days, method)
                                              |
  _data_referencia() -------------------------+--> preparar_series(store, ticker, periodo, metodo, ancora)
                                              |         |
                                              |         v
                                              |   selecionar_datas(disponiveis_na_janela, metodo)
                                              |         |
                                              |         v
                                              |   montar_series(observacoes_selecionadas)
                                              v
                       painel.update(series, ticker)
```

## Goals / Non-Goals

**Goals:**
- Período (30/60/90) e método (Fibonacci e variantes, Monte Carlo e duplo, Todos os dias) passam a compor os pontos exibidos.
- Preservar o contrato atual do Fibonacci: extremos sempre presentes, `≤2` observações devolvem todas, sem datas inventadas, ordem crescente, sem duplicatas.
- Manter a origem cache-only e a leitura fora da thread do Tk.
- Eliminar o "pulo" visual do Monte Carlo entre renders.

**Non-Goals:**
- Não alterar a aquisição B3 nem o `SamplingConfig` dos comboboxes; não registrar observações fundamentais em datas amostradas (o cache continua sendo 1 observação por dia usado).
- Não mudar as opções nem os textos dos comboboxes.
- Não introduzir um novo método de amostragem ou nova fonte de dados.

## Decisions

### 1. Selecionar a partir das observações do cache, não das datas-alvo da B3

Como o cache só tem observações nos dias efetivamente carregados, reproduzir as datas-alvo de `infrastructure/b3/generators.py` produziria gráficos quase vazios. A amostragem passa a operar sobre o conjunto de datas presentes no cache dentro da janela.

Alternativa descartada: gerar datas-alvo e aproximar para o cache mais próximo — instável e tende a pular pontos.

### 2. Âncora da janela

`ancora = data_de_referencia`; `janela = [ancora - periodo_dias, ancora]` (inclusivo). Se a janela não contiver observações, `ancora` recua para a maior data disponível no cache e a janela é recalculada com a mesma largura. Alternativa descartada: ancorar sempre na observação mais recente — ignoraria a data de referência que governa o resto do app.

### 3. Regras por método (sobre `disponiveis` ordenado na janela)

- **Fibonacci**: mantém `selecionar_datas_fibonacci` (caminha do recente ao antigo com gaps 1,2,3,5,... e aproxima).
- **Fibonacci reverso**: espelho — caminha do antigo ao recente com os mesmos gaps.
- **Fibonacci duplo**: união dos 3 primeiros alvos do caminho recente + 3 do caminho antigo + a observação mais próxima do centro da janela, deduplicada.
- **Monte Carlo**: extremos + 5 observações intermediárias aleatórias.
- **Monte Carlo duplo**: extremos + 12 observações intermediárias aleatórias.
- **Todos os dias**: todas as observações da janela.

Todas as variantes incluem os extremos, tratam `≤2` observações devolvendo todas e nunca criam datas.

### 4. Monte Carlo determinístico

As intermediárias são sorteadas com `random.Random(semente)` onde `semente = f"{ticker}|{inicio}|{fim}|{metodo}|{n}"`. Assim a amostra é estável entre renders e só muda quando ticker, janela ou conjunto de observações mudam. Alternativa descartada: `random.sample` global (o gráfico pularia a cada refresh).

### 5. Separação de responsabilidades

- `evolucao.py` ganha funções puras: `selecionar_datas(disponiveis, metodo, *, semente=None)` (dispatcher) e as variantes. `montar_series` deixa de amostrar e apenas mapeia as observações recebidas para as séries; a assinatura permanece `montar_series(observacoes)`.
- `evolucao_job.preparar_series(store, ticker, *, periodo_dias, metodo, ancora)` calcula a janela/âncora, filtra as observações pela seleção e chama `montar_series`.
- `app_actions._update_fundamental_evolution` lê `get_sampling_config()` e `_data_referencia()`, inclui a config na `chave` do job (`(ticker, periodo, metodo)`) e no guard de `_aplicar_evolucao`.
- O painel permanece "burro": continua recebendo apenas `series` e `ticker`.

### 6. Re-render ao mudar os filtros

`_on_period_combo_changed` e `_on_sampling_combo_changed` passam a chamar um helper que, se a sub-aba "Evolução dos Fundamentos" estiver visível, dispara `_update_fundamental_evolution()`, independentemente de `_current_data`. A política `LATEST_WINS` com a nova `chave` (item 5) substitui a leitura anterior em voo, evitando renders obsoletos. Título passa a informar as datas exibidas em relação ao total do período.

## Risks / Trade-offs

- [Janela de 30 dias pode ter pouquíssimas observações] → o comportamento de `≤2` e extremos sempre presentes mantém o gráfico legível; o título informa a contagem.
- [Trocar filtro dispara remontagem enquanto uma carga B3 também roda] → `LATEST_WINS` + `chave` com a config coalescem as submissões; o guard de ticker+config descarta resultados antigos.
- [Monte Carlo "fixo" pode surpreender ao usuário que espera re-sorteio] → aceitável; estabilidade visual é preferível, e recarregar dados ou mudar filtro renova a amostra.
- [Mudança de comportamento spec-level] → o delta remove o requisito de Fibonacci fixo e adiciona cenários por método, documentando a migração.

## Migration Plan

1. Adicionar as funções puras de seleção e o dispatcher em `evolucao.py`; simplificar `montar_series`.
2. Propagar `periodo_dias`, `metodo` e `ancora` por `preparar_series` e `app_actions`.
3. Ajustar gatilhos de combobox e título do painel.
4. Atualizar testes de aplicação e de apresentação.
5. Sem migração de dados: nenhuma mudança no formato do cache ou da configuração persistida.
