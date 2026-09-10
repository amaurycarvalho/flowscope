## Context

As métricas `FFO Yield`, `P/FFO` e `FFO Trend` têm o Fundamentus como fonte primária (change `fundamentus-fundamental-provider`), que faz scraping da página do Fundamentus e retorna os valores reportados. A RFC-010 define um motor determinístico que calcula o FFO a partir de componentes estruturados da CVM, usado como fallback quando o Fundamentus falha ou não traz o dado. O domínio já possui `domain/fii/metrics.py`, que calcula `ffo_yield`, `p_ffo` e `ffo_momentum` a partir de um `FiiSnapshot` com `ffo_12m`/`ffo_3m`. Ver `proposal.md` para motivação.

Depende de `b3-fii-identity-and-dividends` (identidade/CNPJ) e `cvm-monthly-fund-data` (pipeline CVM e cotas/patrimônio).

## Goals / Non-Goals

**Goals:**
- Calcular FFO de forma determinística e auditável a partir de componentes CVM.
- Preencher `FFO Yield`, `P/FFO` e `FFO Trend` com uma única fonte de verdade.
- Fornecer o FFO calculado como fallback do Fundamentus.
- Manter o domínio puro (sem HTTP/CSV) e versionado.

**Non-Goals:**
- Usar FFO divulgado por gestor/administrador.
- Classificação por LLM em produção.
- Dados intraday ou estimativas não reportadas.

## Decisions

### 1. Classificador puro com tabela de regras versionada

O classificador é uma função pura `componente → tipo`, orientada por uma tabela de regras versionada (`FFO_RULES_VERSION`), independente de ticker. `UNKNOWN` é o default conservador e nunca entra no FFO. **Alternativa:** classificação por similaridade/LLM — rejeitada pela RFC-010 §36.

### 2. Motor de FFO no domínio, aquisição na infraestrutura

`domain/ffo/` contém componentes, classificador e o motor (soma dos recorrentes, agregação mensal/12m, FFO por cota, Yield/P/FFO). A infraestrutura apenas fornece componentes normalizados. **Alternativa:** calcular na camada de aplicação — misturaria I/O com regra financeira.

### 3. Média ponderada de cotas

`weighted_average_shares` é derivado das observações mensais de `QT_COTA` da CVM (change 2) ponderadas pelo tempo; quando indisponível, o FFO por cota fica indisponível em vez de usar uma cota pontual silenciosamente.

### 4. Fonte única de verdade para métricas de FFO

O motor emite `ffo_12m`, `ffo_3m` (soma dos 3 últimos meses), `ffo_per_share`, `ffo_yield` e `p_ffo`. O `analisar_snapshot` passa a consumir `ffo_12m`/`ffo_3m` do motor para as colunas de FFO, evitando cálculo duplicado. `FFO Trend` mantém a semântica atual `(ffo_3m × 4) / ffo_12m − 1`, agora com `ffo_3m` derivado dos meses. **Alternativa:** manter dois cálculos — rejeitada por gerar divergência entre colunas.

### 5. Motor de FFO como fallback do Fundamentus

O `FundamentusProvider` permanece como fonte primária de FFO; o motor determinístico entra na composição por campo como fallback, usado quando o Fundamentus falha ou não traz o FFO. O contrato `FfoProvider` é preservado e satisfeito tanto pelo provider do Fundamentus quanto pelo motor.

**Alternativa:** remover o Fundamentus — rejeitada pelo usuário, que o define como fonte principal.

### 6. Reconciliação e qualidade configuráveis

Limites de materialidade (`1%`/`5%`) e de reconciliação (`1%`) são configuráveis e versionados; divergências geram warning, não descarte. **Alternativa:** falhar o cálculo — rejeitada por esconder informação útil.

## Risks / Trade-offs

- **[Risco] Cobertura das regras de classificação** → `UNKNOWN` conservador, qualidade `MEDIUM`/`LOW` e proveniência para revisão; regras versionadas.
- **[Risco] Layout do Informe Trimestral/DFIN mudar** → schema versionado e erro explícito.
- **[Risco] Acumulado vs. mensal no Informe Trimestral** → derivar meses apenas com a mesma base contábil e sinalizar base insuficiente.
- **[Trade-off] Refatorar `analisar_snapshot`** → risco de regressão nas métricas existentes; coberto por testes atuais e novos.
- **[Trade-off] Dois cálculos de FFO** (reportado pelo Fundamentus e calculado pela CVM) → precedência explícita por campo, com proveniência, e o calculado como fallback; mitigado pela reconciliação com DFIN.

## Migration Plan

1. Implementar `domain/ffo/` (componentes, classificador, motor) com testes puros.
2. Implementar a aquisição CVM trimestral/DFIN e normalização de componentes.
3. Integrar o FFO ao `analisar_snapshot` e ao wiring da análise.
4. Integrar o motor como fallback de FFO na composição de fontes e ajustar testes/imports.
5. Rollback: manter o provider atrás de uma flag temporária enquanto o motor não estiver validado; removê-lo ao final.
