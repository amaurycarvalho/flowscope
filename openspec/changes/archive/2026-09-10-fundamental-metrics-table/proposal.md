## Why

As RFC-006 e RFC-007 especificam um pipeline determinístico para extrair métricas fundamentalistas de FIIs (FFO Yield, Dividend Yield, P/FFO, P/VP, FFO Momentum, nº de cotistas e patrimônio) a partir de CVM, preço de mercado e um provedor de FFO. O FlowScope hoje expõe apenas análise de fluxo de ordens (B3) e não possui nenhuma visualização fundamentalista. Esta change adiciona uma sub-aba "Fundamentos" à aba "Análise Geral" com uma tabela consolidando identidade, classificação, dividendos e — para FIIs elegíveis — as métricas das RFCs, de forma ticker-agnóstica.

## What Changes

- Nova sub-aba "Fundamentos" no sub-notebook da aba "Análise Geral", com uma tabela (`ttk.Treeview`) alimentada pela watchlist de tickers.
- Colunas de identidade para todos os tickers: ticker, nome, tipo (ação/FII/ETF/BDR) e sub-tipo (FII: tijolo/papel/híbrido/fiagro/fiinfra; ação: ordinária/preferencial/ETF).
- Classificação de tipo/sub-tipo: tipo e sub-tipo de ação derivados sintaticamente do ticker e cruzados com `code-cvm-resolution`; sub-tipo de FII via taxonomia versionada.
- Colunas de dividendo para todos os tickers: última data-com, último dividendo (somente `Rendimento`; amortização excluída) e tendência do dividendo (último vs. anterior, banda de ±5% configurável, `N/A` sem dividendo anterior).
- Colunas fundamentalistas **apenas para FIIs elegíveis** (tijolo/híbrido): FFO Yield, Dividend Yield 12m, P/FFO, P/VP, FFO Trend, nº de cotistas + classe e patrimônio + classe — conforme RFC-006/007. Ações/ETF/papel/fiagro exibem `N/A` nessas colunas.
- Adapter CVM para NAV, nº de cotas e nº de cotistas; provedor Fundamentus para FFO 12m/3m.
- Reuso do preço de fechamento dos dados B3 já baixados (sem novo adapter de mercado).
- Camada de domínio isolada (funções puras, `decimal.Decimal`, evidência por métrica) conforme RFC-007.

## Capabilities

### New Capabilities

- `fii-classification`: Classificação determinística de tipo (ação/FII/ETF/BDR) e sub-tipo (tijolo/papel/híbrido/fiagro/fiinfra para FIIs; ordinária/preferencial/ETF para ações), combinando derivação sintática do ticker, resolução codeCVM e taxonomia versionada.
- `dividend-metrics`: Métricas de dividendo por ticker — última data-com, último dividendo (Rendimento) e tendência do dividendo (último vs. anterior, banda ±5%).
- `fii-fundamental-metrics`: Motor determinístico de métricas fundamentalistas de FII (FFO Yield, Dividend Yield, P/FFO, P/VP, FFO Momentum, nº de cotistas e patrimônio, com classificação por faixas) conforme RFC-006/007, incluindo evidência por métrica.

### Modified Capabilities

- `gui-interface`: Adiciona a sub-aba "Fundamentos" ao sub-notebook da aba "Análise Geral", exibindo a tabela fundamentalista para os tickers selecionados no Listbox.

## Impact

- **Código afetado**: Novos módulos em `domain/` (classificação, tendência de dividendo, métricas FII), `application/` (use case de análise fundamentalista), `infrastructure/` (adapter CVM e provedor Fundamentus) e `presentation/gui/` (nova sub-aba e painel de tabela).
- **Dependências**: Reusa `Provento`/`Entidade` de `structured-earnings` (change em aberto) e `code-cvm-resolution` de `regulacao-mercado` (change em aberto); reusa `beautifulsoup4` (já adicionado por `structured-earnings`) se necessário para o provedor de FFO.
- **Cache**: Novas chaves em `~/.cache/flowscope/` para dados CVM e FFO.
- **APIs**: CVM (informes mensais/trimestrais) e provedor de FFO (Fundamentus); preço de fechamento via dados B3 já existentes.
- **Escopo faseado**: Fase A entrega identidade + dividendos (FIIs/fundos); Fase B entrega as métricas FFO (FII elegível). Dividendos de ações ficam fora da Fase A (`N/A` nas colunas de dividendo para ações).
