## 1. Estrutura de dois Treeviews

- [x] 1.1 Derivar `_COLUNAS_FIXAS = _COLUNAS[:2]` e `_COLUNAS_ROLANTES = _COLUNAS[2:]` mantendo `_COLUNAS` como canônica; verificar que `montar_csv` continua produzindo as 26 colunas e os testes existentes passam
- [x] 1.2 Substituir o Treeview único por dois Treeviews (congelado com `Ticker`, `Nome`; rolável com as 24 demais) em frames lado a lado; verificar que o painel expõe os dois widgets e que o congelado tem exatamente 2 colunas
- [x] 1.3 Montar o layout em grid: frame congelado com `weight=0` e largura fixada pela soma das colunas, frame rolável com `weight=1`, barra vertical compartilhada e barra horizontal apenas sob o painel rolável, com espaçador de mesma altura sob o congelado; verificar a estrutura via `grid_info` em teste
- [x] 1.4 Atualizar `update()`/`reset()` para inserir as mesmas linhas nos dois Treeviews com `iid=ticker`; verificar que ambos têm os mesmos `iid`s e que a linha dividida em `[:2]`/`[2:]` reconstrói os 26 campos

## 2. Rolagem e seleção sincronizadas

- [x] 2.1 Implementar sincronização vertical (`yscrollcommand` do rolável move o congelado via `yview_moveto`, comando da barra chama `yview` nos dois e roda do mouse encaminhada); verificar que rolar o painel rolável desloca o congelado para a mesma fração
- [x] 2.2 Implementar seleção única espelhada com `selectmode="browse"` e guarda de reentrância em `<<TreeviewSelect>>`; verificar que selecionar em um painel seleciona o mesmo `iid` no outro e que Ctrl/Shift não mantém mais de uma linha

## 3. Larguras e fronteira auto-ajustada

- [x] 3.1 Agregar `get_column_widths()` sobre os dois Treeviews e associar `_on_column_resized` a ambos; verificar que o callback recebe larguras de colunas congeladas e roláveis no mesmo dicionário
- [x] 3.2 Aplicar as larguras persistidas ao Treeview correto de cada coluna; verificar que `ticker`/`nome` são restaurados no painel congelado e as demais no rolável
- [x] 3.3 Dimensionar o frame congelado pela soma das larguras de `Ticker` e `Nome` (com `propagate(False)`) e recalculá-lo em `_on_column_resized`; verificar que redimensionar uma coluna congelada move a fronteira sem gap nem clipping
- [x] 3.4 Impor uma largura mínima ao painel rolável e limitar o painel congelado quando as colunas crescerem além do espaço; verificar que o painel rolável não colapsa

## 4. Cópia CSV

- [x] 4.1 Confirmar que `_build_fundamental_csv` continua usando `_fundamental_data` + `montar_csv` sem ler os widgets; verificar com teste que a cópia contém o cabeçalho e as 26 colunas, incluindo `Ticker` e `Nome`

## 5. Testes e documentação

- [x] 5.1 Atualizar `TestFundamentalTablePanel` para os dois Treeviews, o acessor agregado e os novos índices de coluna; verificar que os testes passam
- [x] 5.2 Adicionar testes de sincronização de rolagem, espelhamento de seleção e fronteira auto-ajustada; verificar que passam
- [x] 5.3 Atualizar `panels.md` descrevendo o congelamento das colunas `Ticker`/`Nome` e a fronteira auto-ajustada; verificar que a seção da sub-aba Fundamentos reflete o novo comportamento
- [x] 5.4 Executar `make lint` e `make test`; verificar que passam com cobertura >= 85%
