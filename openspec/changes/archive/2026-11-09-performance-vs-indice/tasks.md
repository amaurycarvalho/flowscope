# Tasks

## 1. Ingestão da série do índice na B3

- [x] 1.1 Adicionar `fetch_index_daily_history(index, year)` em `infrastructure/b3/client.py`, montando o token base64 de `{"index","language","year"}` e chamando `indexStatisticsProxy/IndexCall/GetPortfolioDay`; verificar com teste de cliente que a URL/payload são montados e que resposta vazia vira ausência de série.
- [x] 1.2 Implementar parser JSON da grade dia × mês (`results`/`rateValue1..12`) em `infrastructure/b3/parser.py`, convertendo decimal brasileiro e ignorando `null`; verificar com testes de parsing (ano completo, mês parcial, valores nulos, valor inválido).
- [x] 1.3 Criar a porta `IndexHistoryRepository` em `application/ports.py` e implementá-la em `infrastructure/b3/repository.py` (reaproveitando o cliente), sem alterar o Protocol `DataRepository`; verificar com teste de repositório e com os fakes existentes.
- [x] 1.4 Implementar cache da série por `(index, year)` com `CacheManager`: TTL de 1 dia no ano corrente, imutável para anos anteriores e invalidação por versão de schema; verificar com testes de cache hit/miss/TTL/versão.
- [x] 1.5 Documentar o endpoint, payload, formato de resposta e cache em `docs/misc/datasources.md`; verificar que o texto contém a URL, o payload e as regras de TTL.

## 2. Cálculo do excesso de retorno

- [x] 2.1 Criar `application/performance/` com o cálculo puro do retorno de preço, retorno total, retorno do índice e excesso em p.p., exigindo no mínimo 2 datas comuns alinhadas; verificar com testes unitários de preço, total, alinhamento e observações insuficientes.
- [x] 2.2 Implementar a derivação da data ex (próximo dia útil após a data-com) e a incorporação do provento na primeira observação alinhada igual ou posterior à data ex, usando o `DividendHistoryProvider` injetado; verificar com testes de provento dentro/fora do período e múltiplos proventos.
- [x] 2.3 Implementar `AnalyzePerformanceUseCase` recebendo dados de trades, série do índice, proventos e classificação, produzindo o resultado por ticker e por benchmark; verificar com testes de caso de uso usando fakes.
- [x] 2.4 Implementar cache read-through dos resultados em `infrastructure/performance/` com chave `(schema, index, ref_date, period_days, sampling_method, tickers_ordenados, return_basis)`, escrita atômica e tolerância a corrupção; verificar com testes de reutilização e invalidação por schema/parâmetro.
- [x] 2.5 Implementar a heurística de evento societário suspeito (`salto_excesso` próximo de `1/f` ou `f` para fatores usuais, com desvio grande) sem alterar o retorno; verificar com testes de split, grupamento, bonificação e movimento normal.

## 3. Classificação e orquestração na carga

- [x] 3.1 Implementar a precedência de classificação FII × Ação (`_fundamental_data` → `classificar_ticker`), excluindo ETF, BDR e desconhecido; verificar com testes de cada tipo e de fallback.
- [x] 3.2 Implementar o job de performance em `presentation/gui/controller_performance.py`, disparado após a carga principal e reexecutado quando `_fundamental_data` mudar, gravando `_performance_data` sem tocar em `_current_data`; verificar com testes de controlador (disparo, resultado e preservação de `_current_data`).
- [x] 3.3 Montar as dependências no `Nucleo`/`composicao.py` (porta de índice, caso de uso e provider de dividendos) e injetar no controlador; verificar com teste de wiring que o grafo é montado.
- [x] 3.4 Garantir que os testes existentes de carga e de painéis continuam passando com o novo job desligado/ausente; verificar executando os testes de apresentação e aplicação impactados.

## 4. Painel Performance

- [x] 4.1 Criar `presentation/gui/charts/performance_panel.py` com a figura pura (barras a partir de zero, rótulos, eixo Y em p.p., anotação de hover e estado vazio) separada da casca Tk, testável sem `DISPLAY`; verificar com testes de figura.
- [x] 4.2 Implementar a casca Tk com `ToolbarBR`, combobox `readonly` filtrado por tipo, default FII→IFIX/ação→IBOV e atualização a partir de `_performance_data`; verificar com testes de widget (controles, opções e default).
- [x] 4.3 Registrar a sub-aba "Performance" entre "Dominância do Pregão" e "Rede de Correlação" em `app_tab_layout.py`, adicionar o painel ao dicionário `_GENERAL` em `app_layout.py`; verificar com teste de ordem das sub-abas e de resolução do painel.
- [x] 4.4 Adicionar o texto de orientação em `app_tabs.py` (objetivo, pergunta, indicadores, como interpretar e limitação de eventos societários); verificar com teste de conteúdo do `TAB_CONTENT`.
- [x] 4.5 Verificar que o botão "Copiar Dados" e os demais comportamentos das abas gerais permanecem inalterados e que "Copiar Gráfico" copia a figura; verificar com os testes de cópia existentes e um teste do novo painel.
- [x] 4.6 Documentar a sub-aba, os benchmarks e a limitação em `docs/misc/panels.md`; verificar que o texto descreve o gráfico, o combobox, as bases de retorno e o aviso.

## 5. Integração e release

- [x] 5.1 Executar `make lint`, `make complexity` e os testes relacionados/impactados (infraestrutura, aplicação e apresentação) e corrigir os problemas encontrados.
- [x] 5.2 Cobrir a integração carga → job de performance → painel com um teste que valide barras, combobox e aviso de evento suspeito a partir de dados simulados.
- [x] 5.3 Atualizar o CHANGELOG e a versão para 1.8.0 usando a skill `release-version`; verificar que a versão em `pyproject.toml` e no `CHANGELOG.md` está correta.
- [x] 5.4 Verificação manual no app: carregar uma watchlist mista, conferir os índices oferecidos no combobox, o default, as barras positivas/negativas, o hover, o aviso de evento e o reaproveitamento do cache ao reabrir a sub-aba.

## Pontos encontrados na implementação

- **`TVRI11` fora da Performance (teste manual da task 5.4):** por ser um FII ausente da taxonomia determinística, a classificação retornava `DESCONHECIDO` e o ticker era excluído da sub-aba. O Fundamentus, porém, já o identificava como FII em `_fundamental_data.classificacao_exibicao`.
  - Correção: `application/performance/classificacao.py` passa a usar `classificacao_exibicao` quando a classificação determinística não resolve `FII`/`ACAO`; `Papel` vira `ACAO`, mas sub-tipos `BDR` e `ETF` continuam excluídos.
  - Cobertura: testes de regressão em `tests/test_application/test_performance_classificacao.py` e `tests/test_presentation/test_performance_integration.py`.
  - Efeito: o conjunto de tickers elegíveis muda, gerando nova chave de cache e recálculo do benchmark ao recarregar os dados/abrir a sub-aba.
- **Mensagem "Processamento interrompido" (investigação no log):** a mensagem é emitida quando algum job termina com `Outcome.CANCELADO`. O log não registrava o motivo do cancelamento e o job de performance não registrava seu ciclo, então não era possível identificar a origem.
  - Correção: adicionados logs de agendamento, cache, benchmarks calculados, tickers sem preço, observações insuficientes, índice indisponível e falha de proventos; o gerenciador de background agora registra cancelamentos com grupo/id e o presenter registra o pedido de interrupção do usuário.
  - Efeito: cancelamentos do job auxiliar de performance são registrados e descartados sem exibir "Processamento interrompido"; a mensagem permanece para jobs principais cancelados pelo usuário.
- **Logging de edge cases da Performance (decisão D10):** adotada cobertura explícita para problemas ao carregar e processar a sub-aba.
  - `INFO`: ciclo do job, reutilização/cálculo por benchmark, exclusões por tipo não elegível e descarte por cancelamento.
  - `WARNING`: cache inválido ou falha de escrita, resposta vazia/JSON inválido/série vazia do índice, dia/valor/data inválido no parser, ticker sem preço, menos de 2 observações alinhadas, índice indisponível, falha de proventos, exceção isolada por benchmark e excesso inválido no painel.
  - Células `null` da grade B3 não geram log por serem ausência esperada de pregão.
- **Mensagem "Processamento interrompido" reincidente (causa raiz):** no novo teste, duas submissões do job de performance ocorreram em sequência — uma ao fim da carga e outra após `_fundamental_data` mudar. A segunda substituiu a primeira pelo `LATEST_WINS`, finalizando o job antigo como `CANCELADO`; o presenter interpretou isso como interrupção do usuário.
  - Evidência no log: `Performance: agendando cálculo` duas vezes em `12:34:43` e `Job 3 do grupo performance cancelado.` imediatamente após a segunda submissão.
  - Correção: `JobHandle.substituido` marca jobs substituídos; `app_wiring` não repassa o desfecho de cancelamento desses jobs ao presenter, e o gerenciador registra a substituição com os ids dos jobs.
  - Efeito: substituições rotineiras não exibem "Processamento interrompido"; cancelamentos explícitos do usuário continuam exibindo a mensagem.

## Workflow follow-up

- Manual do usuário: executar a suíte completa (`make test`) e o quality gate (`make quality-gate`) se desejar a verificação ampla; o agente não os executa sem autorização explícita.
- Arquivar a change após a implementação e a revisão do projeto.
