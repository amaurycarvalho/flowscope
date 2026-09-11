## Why

A tabela da sub-aba "Fundamentos" possui 26 colunas e rola horizontalmente; ao rolar para a direita, o usuário perde de vista o Ticker e o Nome, que identificam a linha. Congelar as duas primeiras colunas preserva a identidade do ativo durante toda a leitura da tabela.

## What Changes

- **Congelamento**: as colunas `Ticker` e `Nome` passam a ficar fixas à esquerda da tabela de Fundamentos, enquanto as demais 24 colunas rolam horizontalmente.
- **Dois Treeviews sincronizados**: a tabela passa a ser composta por um Treeview fixo (Ticker, Nome) e um Treeview rolável (demais colunas), lado a lado; a fronteira entre eles é a borda direita da última coluna congelada, reforçada por uma linha divisória vertical fixa (não arrastável), para que permaneça visível durante a rolagem horizontal.
- **Scroll vertical compartilhado**: uma única barra de rolagem vertical controla os dois Treeviews; a roda do mouse sobre qualquer um dos painéis rola ambos.
- **Scroll horizontal**: apenas o Treeview rolável possui rolagem horizontal; o painel congelado não rola.
- **Largura da região congelada**: a largura do painel congelado é a soma das larguras de `Ticker` e `Nome`; redimensionar uma dessas colunas redimensiona a região, sem gap nem clipping. As larguras das colunas continuam sendo persistidas e são a única fonte de verdade da largura da região.
- **Seleção**: a seleção de uma linha em qualquer um dos Treeviews é espelhada no outro. O modo multi-seleção é desabilitado, mantendo-se apenas a seleção de uma linha por vez.
- **CSV inalterado**: o botão "Copiar dados CSV" continua copiando a tabela inteira, com todas as 26 colunas, sem alteração de comportamento.
- **Compatibilidade**: a preferência existente (`fundamental_column_widths`) permanece válida e passa a ser a única fonte de largura; nenhuma preferência nova é introduzida.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities

- `gui-interface`: novo comportamento de congelamento das colunas `Ticker` e `Nome` na sub-aba Fundamentos, com a região congelada dimensionada pelas próprias colunas, scroll sincronizado e seleção de linha espelhada.

## Impact

- **Código**: `presentation/gui/charts/fundamental_table.py` (dois Treeviews, sincronização de scroll e seleção, agregação de larguras e largura da região congelada derivada das colunas). `app.py` e `app_tab_layout.py` não mudam, pois a preferência existente já cobre as larguras.
- **Preferências**: nenhuma chave nova; `fundamental_column_widths` mantém o mesmo formato e passa a definir também a largura da região congelada.
- **CSV**: `presentation/gui/app_csv.py` e `montar_csv` não mudam.
- **Testes**: `tests/test_presentation/test_fundamental_table.py` (painel passa a expor dois Treeviews e a fronteira auto-ajustada).
- **Compatibilidade**: usuários com preferências antigas continuam válidos; as larguras salvas determinam a região congelada desde a primeira execução.
