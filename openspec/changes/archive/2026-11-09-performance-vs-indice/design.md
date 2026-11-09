# Design

## Context

Ver `proposal.md` para a motivação. O estado atual que molda a solução:

- `AnalyzeTickersUseCase` baixa `TradeInformationConsolidated` nas datas amostradas e devolve, por ticker, `daily_data` (com `date`, `last_price`, `min_price`, `max_price`, etc.) e `_sampling_dates`.
- Os botões IBOV/IDIV/IFIX baixam apenas a **carteira** (constituintes) via `GetDownloadPortfolioDay`; não existe série de fechamento do índice no app.
- A análise fundamentalista roda em job separado e produz `_fundamental_data` (classificação e dados de proventos), mas não guarda o histórico completo de proventos.
- Os painéis seguem o padrão Tk + `Figure` + `ToolbarBR`, com a lógica pura em `application/` (ex.: `vwap/dados.py`, `network/dados.py`).
- Caches existentes: `CacheManager` (JSON com TTL), `JsonFundamentalHistoryStore` (JSON por ticker com retenção) e `ConditionalCache` (revalidação condicional).
- Restrição: sem novas fontes de terceiros; apenas novas URLs/endpoints dos datasources já usados (B3).

## Goals / Non-Goals

**Goals:**

- Sub-aba "Performance" com barras de excesso de retorno acumulado em p.p.
- Ingestão automática da série diária de fechamento de IBOV, IDIV e IFIX na pipeline de atualização, com cache por índice e ano.
- Cálculo de retorno de preço (IBOV) e total (IFIX/IDIV) com datas alinhadas, respeitando período e amostragem globais.
- Cache pré-calculado dos resultados para evitar recálculo.
- Aviso heurístico de evento societário suspeito, sem correção do valor.
- Limitação documentada na orientação, specs e docs.

**Non-Goals:**

- IDIV Price Return (só existe em planilha "Índices On Demand" da B3).
- Ajuste preciso de split/grupamento/bonificação (COTAHIST/FATCOT fica para evolução futura).
- Reconstruir o índice a partir dos constituintes.
- Dados intradiários ou janelas móveis de 3/6/12/24 meses.
- Alterar o comportamento dos painéis existentes.

## Decisions

### D1 — Fonte da série do índice: endpoint oficial de evolução diária

Usar o mesmo host B3 já consumido pelo app:

```text
GET https://sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/
    GetPortfolioDay/{BASE64}

payload: {"index":"<IBOV|IDIV|IFIX>","language":"pt-br","year":"<YYYY>"}
```

Resposta JSON com `results` em grade dia × mês (`rateValue1..12`), fechamentos em formato decimal brasileiro, `null` para dia sem pregão. Uma requisição cobre o ano inteiro (~250 pregões).

Alternativas descartadas:
- `bvmf.bmfbovespa.com.br/indices/ResumoEvolucaoDiaria.aspx`: só tem anos até 2020 e depende de postback ASP.NET.
- Variante CSV `GetDownloadPortfolioDay`: funciona (Base64), mas o JSON evita decodificação e já traz a estrutura pronta.
- Reconstruir dos constituintes: pesos só do dia corrente, exigiria proventos e histórico de todos os constituintes; não reprodutível.

`IBOV` e `IBOVESPA` retornam a mesma série; o app usa `IBOV` e mantém o mapeamento explícito se necessário. Índice inexistente retorna `results: []`.

### D2 — Contrato de dados: porta dedicada, sem inchar `DataRepository`

Criar uma porta `IndexHistoryRepository` em `application/ports.py` (Protocol) com `get_index_history(index, start, end)` ou `get_index_year(index, year)`, e implementá-la em `B3DataRepository` (que já encapsula `B3Client` e cache). A composição injeta a mesma instância no novo caso de uso.

Motivo: `DataRepository` é um Protocol usado por fakes de teste; adicionar um método obrigatório ali forçaria atualizar todos os fakes sem necessidade. A porta dedicada mantém o contrato de trades estável e testável.

`B3Client` ganha `fetch_index_daily_history(index, year)` e um parser JSON em `infrastructure/b3/parser.py`, devolvendo `list[IndexClose(date, close)]` (value object simples, `Decimal` ou `float`).

### D3 — Cache em duas camadas

1. **Série bruta do índice** (`CacheManager`):
   - chave `index_history_{index}_{year}`;
   - ano corrente: TTL 1 dia;
   - anos anteriores: imutáveis (TTL longo/sem expiração efetiva);
   - schema/versão do parser no payload para invalidar em mudança de formato;
   - cache miss no ano corrente baixa o ano inteiro; anos anteriores raramente mudam.

2. **Resultado pré-calculado** (`JsonPerformanceCache`, padrão análogo ao `JsonFundamentalHistoryStore`):
   - diretório `~/.cache/flowscope/performance/`;
   - chave lógica `(schema_version, index, ref_date, period_days, sampling_method, tickers_ordenados, return_basis)`;
   - arquivo JSON por chave (ou índice por data), escrita atômica e tolerância a corrupção;
   - leitura read-through antes de calcular; invalidação por schema e por qualquer componente da chave.

Motivo: separar dado imutável (série do índice) de resultado dependente da seleção; evita recalcular ao trocar de sub-aba e reaproveita entre recargas com os mesmos parâmetros.

### D4 — Cálculo do retorno e alinhamento de datas

- Interseção entre as datas amostradas do ticker e as datas com fechamento do índice; mesmo início e fim para os dois; mínimo de 2 observações comuns.
- Retorno do índice: `I_final / I_inicial − 1` (fechamentos oficiais na base correta: IBOV preço; IFIX/IDIV total).
- Retorno de preço (IBOV): `P_final / P_inicial − 1`.
- Retorno total (IFIX/IDIV): acumular `R_t = (P_t + D_t) / P_{t−1} − 1`, onde `D_t` é a soma dos proventos com data ex no intervalo `(t−1, t]`.
- Proventos: reutilizar o `DividendHistoryProvider` já injetado (Fundamentus/B3/CVM). `data_base` é tratada como data-com; a data ex é o próximo dia útil (calendário existente). O provento é incorporado na primeira observação alinhada igual ou posterior à data ex, reinvestido ao fechamento dessa observação. Quando a data ex coincide com uma data amostrada, usa-se o fechamento dela.
- Excesso = `R_ticker − R_benchmark`, em pontos percentuais.

Alternativas:
- Buscar o fechamento exato da data ex fora da amostragem: mais preciso, mas exige requisições extras e um novo conjunto de datas; fica para uma evolução. A aproximação é documentada.
- Usar apenas o primeiro/último preço da série completa (ignorando a amostragem): viola o requisito de respeitar a amostragem.

### D5 — Orquestração na pipeline de atualização

Criar `AnalyzePerformanceUseCase` (aplicação pura) e executá-lo em **job de background próprio**, disparado ao final da carga principal e reexecutado quando `_fundamental_data` é atualizado. O job:

1. lê `_current_data` (trades) e `_sampling_dates`;
2. busca a série do índice para os anos necessários (cache);
3. busca proventos dos tickers elegíveis (cache do provider);
4. classifica os tickers (D6);
5. calcula e grava o resultado em `_performance_data` e no cache;
6. notifica a view para redesenhar a sub-aba, se ativa.

O painel apenas lê `_performance_data`; trocar o combobox não recalcula se o resultado já está em cache.

Motivo: mantém a carga principal leve, não bloqueia a UI e separa a dependência de proventos/tipos (que chegam pela análise fundamentalista). A série do índice continua sendo baixada automaticamente na atualização, não ao abrir a aba.

**Importante:** não colocar a série do índice dentro de `_current_data`, que é iterado como `ticker → dict` por vários painéis. Usar estado próprio (`_index_history`/`_performance_data`).

### D6 — Classificação FII × Ação

Ordem de precedência:
1. `AnaliseFundamental.classificacao` em `_fundamental_data`, quando a classificação determinística já resolve `FII` ou `ACAO`;
2. `AnaliseFundamental.classificacao_exibicao` (discriminador `FII`/`Papel` do Fundamentus) quando a determinística é `DESCONHECIDO`; `Papel` com sub-tipo `BDR` ou `ETF` continua fora;
3. `classificar_ticker` (sintaxe + taxonomia + code CVM + FIAGRO) como fallback;
4. sem classificação confiável, o ticker fica fora.

**Ponto encontrado no teste manual:** o `TVRI11`, FII fora da taxonomia determinística, era classificado como `DESCONHECIDO` em `classificacao` e por isso sumia da Performance, embora `classificacao_exibicao` o identificasse como `FII`. A implementação passou a consultar `classificacao_exibicao` antes de descartar o ticker, mantendo `ETF` e `BDR` inelegíveis.

Apenas `FII` entra no IFIX; apenas `ACAO` entra no IBOV/IDIV. `ETF`, `BDR` e `DESCONHECIDO` são excluídos.

Default do combobox: primeiro ticker selecionado FII → IFIX; primeiro ação → IBOV; caso contrário, a primeira opção disponível (IFIX se houver FII, senão IBOV/IDIV se houver ação).

Alternativas: usar a carteira do índice para inferir o tipo (exigiria baixar as três carteiras e não cobre tickers fora do índice); heurística apenas por sufixo (frágil para o sufixo `11`).

### D7 — Painel, combobox e toolbar

- `PerformancePanel` (casca Tk) + `PerformanceFigure` (figura pura, testável sem `DISPLAY`), seguindo o padrão do `correlation_network_panel`.
- Barras a partir de zero, rótulos de ticker rotacionados, eixo Y "Excesso vs <índice> (p.p.)", linha zero destacada, anotação de hover com `retorno do ticker`, `retorno do índice`, `excesso` e aviso (D8).
- `ToolbarBR` idêntica à do VWAP.
- Combobox no topo do próprio painel, `readonly`, opções filtradas por tipo; ao mudar, usa o cache do resultado ou solicita o cálculo.
- Registro em `_build_general_tabs` (após "Dominância do Pregão"), no dicionário `_GENERAL` e em `TAB_CONTENT` (orientação).
- Estado vazio para seleção sem tickers elegíveis, dados ausentes, menos de 2 observações comuns ou série do índice indisponível.

### D8 — Aviso de evento societário suspeito

Heurística sobre os dados já carregados, sem download extra:

```text
salto_excesso = (P_t / P_{t−1}) / (I_t / I_{t−1})
```

Sinalizar quando `salto_excesso` estiver próximo de `1/f` (split/bonificação) ou de `f` (grupamento) para `f` em fatores usuais (2, 3, 4, 5, 10, 20...) e o desvio for grande. O aviso aparece no hover/rótulo do ticker e na orientação, sem alterar o retorno.

Alternativas:
- `COTAHIST` diário com `FATCOT` (posições 211–217, linha de 245 caracteres, ~470 KB/dia): detecção exata, porém baixa um arquivo por data amostrada; fica para evolução futura.
- Fundamentus: não lista split/grupamento/bonificação; descartado.

Riscos da heurística: falso positivo/negativo; amostragem esparsa dificulta separar evento de movimento de mercado; bonificações pequenas não são detectáveis. Tudo documentado.

### D9 — Release e verificação

- Atualizar a versão para **1.8.0** (skill release-version) e o CHANGELOG.
- Verificação por change: `make lint`, `make complexity` e testes relacionados/impactados.
- Suíte completa/quality gate apenas se houver autorização explícita (convenção do projeto).

### D10 — Logging e cancelamento do job de performance

O job de performance é **auxiliar**: não deve transformar cancelamento ou substituição em erro visível ao usuário, mas todos os problemas recuperáveis devem ficar registrados no log.

- **Cancelamento/substituição:** jobs substituídos por uma submissão mais nova (`LATEST_WINS`) são marcados como `substituido` e não repassam `Outcome.CANCELADO` ao presenter; a substituição é rotineira e não deve exibir "Processamento interrompido". No worker, `executar_performance` também captura `OperacaoCancelada`, registra em `INFO` e descarta o resultado. O gerenciador de background registra substituições e cancelamentos com grupo/id, e o presenter registra o pedido explícito de interrupção do usuário.
- **Níveis de log:** `INFO` para ciclo de vida, decisões de cache, benchmarks calculados e exclusões esperadas por tipo; `WARNING` para problemas de dados ou falhas recuperáveis, sempre com contexto (índice, ano, benchmark ou ticker).
- **Edge cases cobertos:**
  - classificação: tickers excluídos por tipo não elegível (`ETF`, `BDR`, desconhecido);
  - cache: reutilização/cálculo, payload inválido (recalcula), falha de escrita (não derruba o job) e invalidação por schema;
  - B3/índice: resposta vazia, JSON inválido, nenhum fechamento válido, dia/valor/data inválidos no parser e série vazia;
  - cálculo: ticker sem preço, menos de 2 observações alinhadas, índice indisponível, exceção da série do índice isolada por benchmark e falha ao obter proventos;
  - painel: excesso/entrada inválida vira estado vazio ou zero com aviso, sem quebrar a thread do Tk.
- Células `null` da grade dia × mês são ausência esperada de pregão e **não** geram log; apenas valores não nulos inválidos são registrados.

## Risks / Trade-offs

- **Endpoint B3 não documentado pode mudar** → isolar no `B3Client`/parser, cobrir com testes, tratar resposta vazia/malformada como ausência de série e manter a variante CSV como fallback futuro.
- **Proventos ausentes ou atrasados no Fundamentus** → retorno total subestimado; documentar a fonte e o efeito, e manter o cálculo de preço disponível via IBOV.
- **Aproximação da data ex** → pequena diferença no reinvestimento; documentar e usar o calendário real para o próximo dia útil.
- **Classificação incerta de tickers `11`** → usar `_fundamental_data` quando disponível e recalcular após a análise fundamentalista; tickers sem classificação ficam fora.
- **Falso positivo/negativo no aviso de evento** → limiar conservador, aviso explícito de "possível" e nenhuma correção automática.
- **TTL de 1 dia no ano corrente** pode servir dado de fechamento anterior durante o dia; aceitável para análise diária; a recarga após a atualização renova o cache.
- **Custo de rede** → 1 requisição por índice/ano (até 3) + proventos já cacheados; resultado cacheado evita recálculo.

## Migration Plan

- Nenhuma migração de dados. O novo diretório de cache é descartável e pode ser removido sem perda.
- O comportamento atual das demais abas permanece inalterado.
- Rollback: remover a sub-aba e o job de performance; os caches novos ficam órfãos e seguros de apagar.

## Open Questions

Nenhuma pendente que altere abordagem, specs ou quebra de tarefas. A estabilidade do endpoint da B3 e o IDIV Price Return ficam registrados como riscos/evolução, respectivamente.
