## Context

O FlowScope calcula indicadores financeiros a partir dos dados consolidados diários da B3. Atualmente os indicadores são funções isoladas em `domain/indicators.py` (VWAP, CVD, Volume Profile, Top Tickers), chamadas manualmente por `AnalyzeTickersUseCase`. A especificação FS001–FS403 define ~20 indicadores com uma cadeia de dependências natural (Range alimenta 7 indicadores, CLV alimenta MFV, etc.).

A implementação atual tem limitações:
- Cada novo indicador exige alteração no use case e nova iteração manual sobre `list[TradeDay]`
- Cálculos como Range são repetidos em múltiplos indicadores
- CVD usa lógica binária (±fin_vol) que a especificação substitui por CLV contínuo

## Goals / Non-Goals

**Goals:**
- Implementar todos os indicadores FS001–FS403 (exceto CVD, removido)
- Criar um motor de cálculo DAG que resolva automaticamente a ordem de execução
- Cada indicador é uma Strategy independente que declara suas próprias dependências
- Zero recomputação: resultados intermediários são cacheados e reusados
- Fácil adicionar novos indicadores sem modificar código existente (Open/Closed)
- Preço Referência = avg_price em todos os indicadores que o utilizam
- Manter compatibilidade com a interface `AnalyzeTickersUseCase` (output pode mudar, input não)

**Non-Goals:**
- Não alterar a pipeline de ingestão de dados (B3Client, parser, cache)
- Não alterar a CLI
- Não introduzir dependências externas (sem numpy, pandas, etc.)
- Não implementar visualizações GUI completas para todos os indicadores (apenas preparar dados)

## Decisions

### D1: Arquitetura do Indicador como Strategy

Cada indicador é uma classe concreta que herda de `IndicatorStrategy`:

```
                  ┌──────────────────┐
                  │  IndicatorStrategy │  (ABC)
                  ├──────────────────┤
                  │  id: ClassVar      │
                  │  deps: ClassVar    │
                  ├──────────────────┤
                  │ +compute(trades,   │
                  │   dep_results): Any│
                  └──────────────────┘
                        ▲
         ┌──────────────┼──────────────┐
         │              │              │
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │  Range   │  │   CLV    │  │  VWAP    │
   └──────────┘  └──────────┘  └──────────┘
```

```python
class IndicatorStrategy(ABC):
    id: ClassVar[str]
    dependencies: ClassVar[list[str]] = []

    @abstractmethod
    def compute(
        self,
        trades: list[TradeDay],
        dep_results: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        ...
```

**Rationale**: Classes (vs funções) permitem declarar metadados (`id`, `dependencies`) estaticamente, essenciais para a resolução do DAG. Cada strategy é testável isoladamente e registrável no engine sem fricção.

### D2: Motor de Cálculo DAG

```
IndicatorEngine
│
├── register(IndicatorStrategy)   # auto-descobre id + deps
├── execute(trades) → resultados
│
│   Algoritmo:
│   1. Montar grafo G = (V, E) onde V = indicadores, E = dependências
│   2. Validar aciclicidade (DFS)
│   3. Ordenação topológica (Kahn)
│   4. Para cada indicador na ordem:
│      a. Buscar dependências no cache
│      b. Executar compute(trades, dep_results)
│      c. Armazenar resultado no cache
│   5. Retornar cache completo
```

```python
class IndicatorEngine:
    def __init__(self):
        self._registry: dict[str, IndicatorStrategy] = {}

    def register(self, *strategies: IndicatorStrategy) -> None: ...

    def execute(
        self, trades: list[TradeDay]
    ) -> dict[str, dict[str, Any]]:
        # 1. Build graph
        # 2. Topological sort (Kahn)
        # 3. Execute in order, cache results
        # 4. Return all results
```

**Rationale**: DAG garante ordem de execução correta sem que o use case ou os indicadores precisem saber uns dos outros. Kahn é O(V+E), simples de implementar sem dependências.

### D3: Estrutura de Resultados e Cache

O cache do engine é um `dict[str, dict[str, Any]]` onde:
- Chave nível 1: `indicator_id` (ex: "range", "vwap")
- Chave nível 2: `ticker` (ex: "PETR4", "VALE3")
- Valor: o resultado específico do indicador para aquele ticker

```python
cache = {
    "range": {
        "PETR4": {date(1): Decimal("0.97"), date(2): Decimal("1.20")},
        "VALE3": {date(1): Decimal("1.50")},
    },
    "vwap": {
        "PETR4": Decimal("78.40"),
        "VALE3": Decimal("65.20"),
    },
    "clv": {
        "PETR4": {date(1): Decimal("0.30"), date(2): Decimal("-0.15")},
    },
    "money_flow_volume": {
        "PETR4": Decimal("1500000.00"),
    },
}
```

**Rationale**: Estrutura uniforme simplifica o engine e permite que indicadores consumers (GUI, CLI) acessem qualquer resultado pelo mesmo padrão.

### D4: Dois níveis de indicadores — Per-Trade e Agregados

| Tipo | Descrição | Exemplo | Resultado |
|------|-----------|---------|-----------|
| **ScalarIndicator** | Opera por TradeDay, produz série temporal por ticker | Range, CLV, TypicalPrice | `{ticker: {date: value}}` |
| **AggregateIndicator** | Agrega todos os trades do período por ticker | VWAP, MFV acumulado | `{ticker: value}` |

A diferença é meramente conceitual — ambos usam a mesma classe base `IndicatorStrategy`. A distinção fica documentada e guia os consumers.

### D5: Catálogo de Indicadores e Dependências

```
indicator                    deps                          input fields
─────────────────────────────────────────────────────────────────────────
vwap                         —                 avg_price, fin_instr_qty
volume_profile               —                 min_price, max_price, fin_vol
top_tickers                  —                 fin_vol

range                        —                 max_price, min_price
typical_price                —                 max_price, min_price, last_price
median_price                 —                 max_price, min_price
weighted_close               —                 max_price, min_price, last_price

clv                          —                 max_price, min_price, last_price
money_flow_multiplier        clv               (alias, delega ao CLV)

buying_pressure              range             last_price, min_price
selling_pressure             range             max_price, last_price

range_percentual             range             avg_price (Preço Referência)
daily_efficiency             range             last_price, avg_price (Preço Referência)

money_flow_volume            money_flow_multiplier  fin_vol
average_trade_size           —                 fin_instr_qty, trades_qty
average_financial_ticket     —                 fin_vol, trades_qty

financial_density            range             fin_vol
trade_density                range             trades_qty
volume_density               range             fin_instr_qty
```

### D6: Integração com AnalyzeTickersUseCase

O use case existente é refatorado para usar o engine:

```python
class AnalyzeTickersUseCase:
    def __init__(self, repository: DataRepository, engine: IndicatorEngine):
        self._repository = repository
        self._engine = engine

    def execute(self, ref_date: date, tickers: list[str] | None = None) -> dict:
        dates = self._repository.get_available_dates(ref_date)
        trades = self._repository.fetch_trades(dates, tickers)

        if not tickers:
            top = self._engine.execute(trades)
            tickers = top["top_tickers"]["_all"]

        filtered = [t for t in trades if t.ticker.value in tickers]
        results = self._engine.execute(filtered)
        return results
```

A DI do engine permite testar o use case com strategies mockadas.

**Rationale**: O use case não precisa mais conhecer indicadores individualmente. O engine é a única orquestração.

### D7: Remoção do CVD

CVD é substituído por Money Flow Volume, que usa CLV contínuo (range [-1, +1]) em vez de sinal binário (±1). A lógica do MFV captura nuance que o CVD ignora: um fechamento próximo ao centro do range Produz MFV pequeno, enquanto o CVD jogaria ±fin_vol integral.

### D8: Preço Referência = avg_price

Tanto FS003 (Range%) quanto FS301 (Daily Efficiency) usam "Preço Referência". Definimos como `avg_price` (TradAvrgPric) — o preço médio ponderado do pregão já calculado pela B3. É uma escolha consistente porque:
- avg_price já é o preço de referência usado em outros contextos (VWAP diário)
- Está disponível em todos os TradeDay sem exceção
- Não depende de dados que não temos (abertura, fechamento do dia anterior)

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| **Performance**: 18 indicadores iterando sobre list[TradeDay] pode ser lento para janelas grandes (21 dias) | O DAG elimina iterações redundantes. Resultados intermediários são cacheados. Se necessário, batch processing com group-by único. |
| **Acoplamento entre indicadores**: Dependências criam acoplamento indireto — mudar Range afeta 7 consumidores | Testes unitários por strategy + testes de integração do engine detectam regressões. O DAG valida aciclicidade em runtime. |
| **Volume de dados**: 18 indicadores × N tickers × M datas produz muitos resultados na memória | TradeDay é ~200 bytes, 1000 trades ≈ 200KB. Resultados são dicts de Decimais — ordem de grandeza similar. Aceitável para uso desktop. |
| **Mudança na B3**: Se a B3 alterar o formato do CSV, todo o sistema pode quebrar | A responsabilidade é do parser, não dos indicadores. Desde que `TradeDay` seja populado corretamente, os indicadores funcionam. |
| **Complexidade acidental**: DAG engine pode ser overengineering para 18 indicadores | O padrão Strategy + DAG é simples (~150 linhas de engine) e o benefício de extensibilidade supera o custo. Sem engine, cada novo indicador exigiria alterar o use case. |
