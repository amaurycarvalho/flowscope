## Context

Ver `proposal.md` — Why, e o contrato em
`openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md`.
Estado atual relevante:

- `presentation/gui/charts/fundamental_rows.py` define o layout de colunas
  (`_COLUNAS`, `_COLUNAS_FIXAS`, `_COLUNAS_ROLANTES`, `_COLUNAS_DIREITA`) e monta
  as linhas a partir das análises de domínio (`montar_linhas`) e o CSV
  (`montar_csv`), apoiando-se nos formatadores de
  `presentation/gui/charts/fundamental_formatters.py`.
- `presentation/gui/charts/fundamental_evolution_data.py` já é puro (sem I/O):
  amostragem Fibonacci das datas (`selecionar_datas_fibonacci`) e montagem das
  séries de oito campos (`montar_series`), consumindo
  `application.fundamental_ports.ObservacaoFundamental` e
  `domain.fii.AnaliseFundamental`.
- `presentation/gui/charts/fundamental_table.py` e
  `fundamental_evolution_panel.py` apenas desenham (`ttk.Treeview`, matplotlib) e
  reexportam `montar_linhas`/`montar_csv`.
- `presentation/gui/app_csv.py` importa `montar_csv` de
  `presentation/gui/charts/fundamental_table` (que o reexporta de
  `fundamental_rows`).
- `presentation/gui/controller_fundamental.py` importa
  `infrastructure.fii.b3_price.B3MarketPriceFromResult` e o instancia a partir do
  `daily_data` do resultado — única violação de fronteira da fatia (allowlist).
- Testes: `test_fundamental_table.py` (91, 27 referências a `DISPLAY`),
  `test_fundamental_evolution_data.py` (16, puro), `test_fundamental_evolution_panel.py`
  (26, 19 com `DISPLAY`), `test_fundamental_job.py` (22, puro).

## Goals / Non-Goals

**Goals:**

- Colocar a montagem de linhas, o CSV e a formatação de exibição em
  `application/fundamental` como view-models prontos.
- Colocar a amostragem Fibonacci e as séries de evolução em `application`.
- Injetar o adaptador de mercado no controlador pelo composition root, sem
  import de `infrastructure`.
- Remover a entrada de `controller_fundamental` da allowlist.
- Migrar os testes puros para `tests/test_application`.

**Non-Goals:**

- Não alterar a tabela, o congelamento, a rolagem, a seleção espelhada nem o
  painel de evolução (widgets inalterados).
- Não mexer na `FundamentalAnalysisUseCase` nem nos providers de fundamentos.
- Não introduzir framework de injeção; usar o composition root existente.
- Não redesenhar colunas, rótulos ou formatação.

## Decisions

### D1 — View-models de linha e CSV em `application/fundamental`

`montar_linhas`, `montar_csv` e o layout de colunas vão para
`application/fundamental/linhas.py`; os formatadores de exibição vão para
`application/fundamental/formatters.py`. A aplicação devolve as tuplas/valores já
prontos para o `ttk.Treeview`; a apresentação apenas insere e copia. Alternativa:
manter a montagem na apresentação e mover só as funções sem formatação.
Rejeitada por deixar a regra de composição da linha fora de `application` e
exigir Tk nos testes.

### D2 — Evolução em `application/fundamental`

`selecionar_datas_fibonacci`, `CAMPOS_EVOLUCAO` e `montar_series` migram para
`application/fundamental/evolucao.py`; o painel de evolução consome o resultado e
só desenha. Alternativa: manter em `presentation` por já ser puro. Rejeitada por
contrariar a localização de regras e por manter os testes na apresentação.

### D3 — Adaptador de mercado injetado pelo composition root

O controlador deixa de construir `B3MarketPriceFromResult`; o composition root
(`app_wiring.py`) monta o adaptador e o injeta como fábrica/callable
(`mercado_factory(daily) -> MarketPricePort`). O controlador só orquestra a
thread e a fila. Alternativa: mover `B3MarketPriceFromResult` para `application`.
Rejeitada por ser adaptador de infraestrutura.

### D4 — Testes puros migram; painel fica com UI

Os testes de linhas/CSV/formatação e de evolução vão para
`tests/test_application`; ficam na apresentação apenas os que verificam
wiring, estado visual, congelamento/rolagem e seleção espelhada.

## Risks / Trade-offs

- [View-models "sujos" de formatação] → a convenção D2 do chapéu admite valores
  já preparados; manter a formatação junto da montagem evita uma fronteira
  artificial e preserva a paridade observável.
- [Reexportações quebradas] → `fundamental_table` reexporta a API pública para
  não quebrar importadores; `app_csv` passa a importar de `application`.
- [Cobertura/mutation ao mover] → mover (não reescrever) os testes junto do
  código e rodar `make test`/guardrail ao final.
- [Adaptador injetado com assinatura divergente] → definir a fábrica no
  composition root e cobrir com os testes de job/controlador existentes.

## Migration Plan

1. Criar `application/fundamental/` com formatters, linhas/CSV e evolução.
2. Atualizar `fundamental_table`, `fundamental_evolution_panel` e `app_csv` para
   consumir `application`.
3. Injetar o adaptador de mercado no controlador pelo composition root e remover
   o import de `infrastructure`.
4. Remover a entrada de `controller_fundamental` da allowlist; migrar os testes
   puros; rodar `make test` e `make quality-gate`.

Rollback: reverter o change restaura os módulos e a allowlist; comportamento
idêntico.

## Open Questions

- Nome do pacote (`application/fundamental/` vs `application/fundamentals/`) e a
  divisão entre `linhas.py`, `formatters.py` e `evolucao.py`: decidir na
  implementação, sem impacto no contrato.
- Se a fábrica de mercado é um `Callable[[dict], MarketPricePort]` ou o próprio
  adaptador com o `daily` recebido por método: decidir na implementação.
