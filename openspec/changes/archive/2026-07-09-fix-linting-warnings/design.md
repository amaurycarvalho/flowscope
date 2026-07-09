## Context

O linter (ruff/flake8) reporta 75 warnings no CI. Cerca de 60 são triviais (imports não usados, blank lines, indentação, linhas longas) e ~15 requerem extração de métodos para reduzir complexidade ciclomática (C901). Os charts seguem um padrão estrutural sem classe base, mas esta change não criará uma — apenas extrairá métodos para reduzir complexidade local.

## Goals / Non-Goals

**Goals:**
- Reduzir o total de warnings de linting de 75 para 0
- Extrair `_compute_stems` como função compartilhada entre 2 charts
- Extrair `_render_last_day_markers` do `PriceRangePanel._build_main_chart`
- Extrair `_collect_ticker_data` e `_compute_violin_shapes` do `VWAPHistChart.update`
- Extrair `_annotate_tickers` do `QuadrantChart.update`
- Adicionar `# noqa: C901` nos `_generate_summary`
- Remover 19 imports e 4 variáveis não usadas
- Corrigir ~37 warnings cosméticos

**Non-Goals:**
- Não criar `ChartBase` ou qualquer classe base compartilhada
- Não alterar comportamento ou output visual dos charts
- Não adicionar testes novos (apenas garantir que existentes passam)

## Decisions

1. **`_compute_stems` como função livre no módulo**, não método de classe, porque opera em dados puros (listas de floats) sem depender de estado do chart.

2. **Extrações de métodos como `_render_last_day_markers` e `_annotate_tickers`** como métodos de instância (não estáticos), porque acessam `self._hover_data`, `self._axes`, etc.

3. **`# noqa: C901` nos `_generate_summary`** em vez de refatorar árvores de if/elif, porque a complexidade é inerente à geração de texto narrativo condicional e qualquer refatoração só trocaria ifs por um dikt/padrão que não reduziria McCabe significativamente.

4. **E501 (linhas longas):** quebrar apenas as que podem ser quebradas com strings adjacentes implícitas ou parênteses. As que estão dentro de strings de texto longo demais para quebrar sem perder contexto usam `# noqa: E501`.

5. **Remoção de imports não usados (F401) e variáveis (F841)** em lote — trivial, sem risco.

## Risks / Trade-offs

- [Risco] Extrair `_compute_stems` como função pura pode mudar ligeiramente o comportamento se
  a função receber os parâmetros errados. → Mitigação: assinatura tipada e testes existentes
  validam output visual.
- [Trade-off] Não criar `ChartBase` agora significa que futuras correções de duplicação
  precisarão de outra change. → Decisão consciente para manter o escopo focado.
- [Risco] Quebrar linhas longas em strings de texto pode introduzir espaços extras ou
  quebras de linha indesejadas. → Mitigação: revisão visual pós-mudança.