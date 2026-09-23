## Why

O cursor de espera ("watch"/ampulheta) continua preso sobre o grid rolável (campos Tipo, Sub-Tipo, …) da sub-aba "Fundamentos" depois que a carga de dados e a análise fundamentalista terminam. O defeito é intermitente e depende de o ponteiro estar sobre o separador de uma coluna no instante em que o estado ocupado é iniciado.

## What Changes

- Tornar robusta a captura do cursor de repouso dos widgets no snapshot do estado ocupado, normalizando valores que o Tk devolve como lista Tcl (por exemplo `('sb_h_double_arrow',)`) e filtrando cursores transitórios de separador/sash antes de usá-los como baseline.
- Garantir que a restauração do cursor nunca deixe o widget preso em "watch": se a restauração do baseline falhar, o widget volta ao cursor padrão.
- Adicionar teste de regressão de GUI cobrindo o ponteiro sobre o separador no início da operação.

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `loading-state-management`: adiciona o requisito de que o cursor de repouso usado como baseline do estado ocupado seja imune a cursores transitórios do toolkit (redimensionamento de separador/sash), inclusive quando o Tk os devolva como lista, garantindo que nenhum widget — em especial os dois grids da tabela de Fundamentos — fique preso em "watch".

## Impact

- Código: `src/flowscope/presentation/gui/app_status.py` (captura/restauração do cursor no `StatusMixin`).
- Testes: `tests/test_presentation/test_fundamental_table.py`.
- Sem alteração de API pública, dependências, domínio ou aplicação.
