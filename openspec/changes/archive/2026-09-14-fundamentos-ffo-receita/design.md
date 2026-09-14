## Context

O pipeline da tabela de Fundamentos é: `parser.py` -> `AtivoFundamental` (já extrai `Receita`, `FFO` e `Rend. Distribuído` em `demonstrativos_12m/3m`) -> `adapter.campos_do_ativo()` (hoje mapeia apenas `FFO_12M/FFO_3M`) -> `FundamentalAnalysisUseCase._resolver_metricas()` (Fundamentus primeiro, motor de FFO depois, parciais por último) -> `AnaliseFundamental.metricas: MetricasFii` -> `fundamental_rows._linha_analise()` (26 colunas).

Os demonstrativos já chegam parseados; falta expô-los e calcular as razões. O Dividend Yield atual vem do Fundamentus (`CAMPO_DIVIDEND_YIELD`) ou do motor de FFO (`dividends_12m / market_value`). Ver `proposal.md - Why`.

## Goals / Non-Goals

**Goals:**
- Expor `Receita` e `Rend. Distribuído` (12m/3m) do Fundamentus na composição de campos.
- Calcular as seis razões sobre a receita de forma determinística (`Decimal`, sem arredondamento intermediário) e apresentá-las como percentual com uma casa.
- Recalcular o Dividend Yield de FII por `(último dividendo × 12) / P`.
- Redefinir o `FFO Trend` pela diferença de margens `FFO/Receita (3m) − (12m)`.
- Manter os fallbacks existentes para `Papel` e para insumos ausentes.

**Non-Goals:**
- Não alterar os cálculos do motor de FFO (`FFO Yield`, `P/FFO`, `P/VP`); eles continuam existindo, apenas deixam de ser exibidos na tabela.
- Não adicionar `Receita`/`FFO` às fontes de fallback B3/CVM; as novas razões são exclusivas do Fundamentus e ficam `N/A` quando ele não fornece os dados.
- Não criar novas faixas de classificação; o `FFO Trend` reutiliza as faixas determinísticas existentes.

## Decisions

### D1. Cálculo das razões em funções puras de domínio, montagem na aplicação

As fórmulas viram funções puras em `domain/fii/metrics.py` (ou módulo irmão), operando em `Decimal` e sem arredondar. Cada função retorna um resultado tipado que distingue valor de motivo de indisponibilidade:

- `ffo_receita(ffo, receita)`, `dividendos_receita(dividendos, receita)`, `dividendos_ffo(dividendos, ffo)` -> `ResultadoMargem(valor: Decimal | None, motivo: MotivoMargem | None)`, com `MotivoMargem` em {`RECEITA_NEGATIVA`, `FFO_NEGATIVO`, `RECEITA_E_FFO_NEGATIVOS`}.
- `tendencia_margem_ffo(margem_12m, margem_3m)` -> `TendenciaFfo | None`, implementada como `classificar_tendencia_ffo(margem_3m - margem_12m)`.

A aplicação (`_analisar_ticker`) calcula as seis razões e a tendência apenas quando `exibicao.tipo` é FII, a partir dos campos do Fundamentus, e as guarda em `AnaliseFundamental` (ex.: `margens: MargensFii | None`). A apresentação só traduz `motivo` -> texto e `valor` -> `formatar_percentual(valor, 1)`.

Alternativa considerada: estender `MetricasFii` com as razões. Rejeitada porque as razões dependem de insumos exclusivos do Fundamentus e não pertencem ao motor determinístico de FFO, e porque o motivo textual é política de exibição, não de domínio. Alternativa considerada: calcular tudo na apresentação (como o atual `_payout`). Rejeitada para manter o cálculo testável no domínio e evitar regras de sinal espalhadas na camada de UI.

### D2. Recálculo do Dividend Yield na aplicação, preservando o valor do Fundamentus

Em `_analisar_ticker`, após resolver `cotacao` e `ultimo_dividendo`, quando `exibicao.tipo == FII`, `ultimo_dividendo.valor` existe, `cotacao` existe e `cotacao != 0`, o `dividend_yield` de `MetricasFii` é substituído por `(ultimo_dividendo.valor * 12) / cotacao` via `dataclasses.replace`. Se `metricas` for `None` ou qualquer insumo faltar, mantém-se o comportamento atual (Fundamentus e fallbacks). Para `Papel`, nada muda.

Alternativa considerada: aplicar no motor de FFO. Rejeitada porque o motor usa dividendos acumulados de 12 meses e não conhece o último dividendo/cotação no formato do snapshot.

### D3. FFO Trend pela diferença de pontos percentuais

`FFO Trend = classificar_tendencia_ffo(margem_3m - margem_12m)`, com as margens como frações. Como as frações já representam percentuais, a diferença é diretamente a diferença em pontos percentuais e os limiares existentes (`±0,05` e `±0,20`) passam a valer `±5 p.p.` e `±20 p.p.`, sem nova configuração. Quando qualquer margem for `None` (ausente ou com texto de negativo), a tendência é `None` (`N/A`).

### D4. Exposição dos campos no provider

Adicionar `CAMPO_RECEITA_12M`, `CAMPO_RECEITA_3M`, `CAMPO_RENDIMENTOS_12M`, `CAMPO_RENDIMENTOS_3M` a `fundamental_ports.py` e a `CAMPOS_FUNDAMENTAIS`. O adapter lê `ativo.demonstrativos_12m/3m`, usando `Receita` e, na ausência, `Receita Líquida`, e `Rend. Distribuído`. `Rend. Distribuído` é a fonte de Dividendos.

### D5. Layout de colunas

Substituir `ffo_yield`, `dividend_payout` e `p_ffo` por `ffo_receita_12m`, `ffo_receita_3m`, `dividendos_receita_12m`, `dividendos_receita_3m`, `dividendos_ffo_12m`, `dividendos_ffo_3m`, mantendo `ffo_trend` logo após `ffo_receita_3m`. Total: 29 colunas (2 fixas + 27 roláveis). As novas colunas entram em `_COLUNAS_DIREITA`; `ffo_trend` permanece à esquerda. O CSV passa a refletir a mesma ordem/cabeçalho.

## Risks / Trade-offs

- [O DY anualizado pelo último dividendo pode divergir do DY do Fundamentus, pois um único pagamento mensal pode ser atípico] -> Comportamento intencional solicitado; documentado no quadro de orientações. O fallback do Fundamentus cobre ausência de insumo.
- [Células com texto (`Receita negativa`) quebram consumidores que esperam número no CSV] -> O texto é exportado igual à tela, de forma consistente; a regra é explícita na spec e nos testes.
- [`Receita` ausente em algumas páginas, com apenas `Receita Líquida`] -> O adapter prioriza `Receita` e cai para `Receita Líquida`.
- [Índices e cabeçalhos de coluna são usados em testes de apresentação] -> Atualizar os testes de CSV/colunas junto com `_COLUNAS`; os testes de cenário da spec cobrem os novos valores.
- [A regra de negativos pode zerar a tendência de FIIs com prejuízo no 12m] -> Esperado: sem margem numérica não há tendência; a célula exibe `N/A`.

## Migration Plan

Sem migração de dados persistidos nem mudança de cache (a versão do parser não muda). Deploy é apenas de código. Rollback: reverter os artefatos de código; nenhuma estrutura externa é criada.

## Open Questions

Nenhuma. As ambiguidades de escopo (negativos, DY anualizado, fórmula do FFO Trend e abrangência por Tipo) foram resolvidas com o usuário antes da proposta.
