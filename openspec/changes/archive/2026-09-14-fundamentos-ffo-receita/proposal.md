## Why

A sub-aba "Fundamentos" exibe hoje FFO Yield, P/FFO e Dividend Payout (DY/FFOY), que não mostram a relação entre FFO, dividendos e a receita do fundo. Além disso, o Dividend Yield usa o acumulado de 12 meses, sem refletir o dividendo corrente sobre a cotação atual de um FII. Substituir essas colunas por razões sobre a receita e redefinir a tendência do FFO dá ao usuário uma leitura direta de quanto da receita vira caixa operacional e quanto é distribuído.

## What Changes

- Recalcula o Dividend Yield de FIIs como `(último dividendo × 12) / P (Cotação)` quando o último dividendo e a cotação existirem; caso contrário mantém o Dividend Yield do Fundamentus. Para Tipo `Papel` o recálculo não se aplica e os fallbacks existentes são preservados.
- Remove as colunas `FFO Yield`, `P/FFO` e `Dividend Payout (DY/FFOY)`.
- Adiciona as colunas `FFO/Receita (12m)`, `FFO/Receita (3m)`, `Dividendos/Receita (12m)`, `Dividendos/Receita (3m)`, `Dividendos/FFO (12m)` e `Dividendos/FFO (3m)`, em notação percentual com uma casa decimal, calculadas apenas para Tipo `FII` (Tipo `Papel` exibe `N/A`).
- Trata insumos negativos com texto na célula: `Receita negativa`, `FFO negativo` ou `Receita e FFO negativos`; exibe `N/A` para divisão por zero e para dado ausente.
- Redefine o `FFO Trend` como a diferença em pontos percentuais entre `FFO/Receita (3m)` e `FFO/Receita (12m)`, classificada nas cinco faixas existentes (Forte Alta, Leve Alta, Estável, Leve Queda, Forte Queda), posicionada após `FFO/Receita (3m)`.
- Expõe `Receita` e `Rend. Distribuído` (12m e 3m) do Fundamentus na composição de campos fundamentalistas, tratando `Rend. Distribuído` como Dividendos.
- Atualiza o quadro de orientações da sub-aba "Fundamentos" para as novas colunas e sua leitura.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `fundamentus-fundamental-provider`: expor os demonstrativos `Receita` e `Rend. Distribuído` (12m e 3m) na composição de campos fundamentalistas.
- `fii-fundamental-metrics`: novas razões `FFO/Receita`, `Dividendos/Receita` e `Dividendos/FFO` (12m/3m) com tratamento de negativos; recálculo do Dividend Yield de FII pelo último dividendo; tendência do FFO pela diferença de margens.
- `gui-interface`: nova lista e ordem de colunas da tabela fundamentalista, formatação percentual com uma casa decimal, alinhamento das colunas numéricas e quadro de orientações.

## Impact

- Código: parser/adapter do Fundamentus; domínio de métricas de FII; caso de uso da análise fundamentalista; tabela fundamentalista (linhas, formatadores, CSV); textos de orientação; documentação (`panels.md`).
- Colunas da tabela: 26 -> 29 (2 fixas + 27 roláveis).
- Sem novas dependências externas.
