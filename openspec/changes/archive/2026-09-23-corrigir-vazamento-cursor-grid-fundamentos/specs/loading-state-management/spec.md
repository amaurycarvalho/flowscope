## ADDED Requirements

### Requirement: Baseline do cursor de espera imune a cursores transitórios do toolkit

Ao capturar o cursor de repouso de cada widget para o estado ocupado, o sistema DEVE ignorar os cursores transitórios geridos pelo toolkit para redimensionamento — o cursor de separador de coluna de tabelas e os cursores de sash de painéis divididos — mesmo quando o Tk os devolva como lista Tcl em vez de string. Esses valores NUNCA DEVEM ser usados como baseline da restauração nem reaplicados ao final da operação. Se a restauração do cursor de repouso de um widget falhar, o sistema DEVE aplicar o cursor padrão, de modo que o widget não permaneça com o cursor de espera "watch". Isso vale para os dois grids da tabela de Fundamentos (colunas congeladas e campos roláveis), que DEVEM sempre terminar a operação com o mesmo cursor entre si.

#### Scenario: Ponteiro sobre o separador de coluna ao iniciar a operação

- **WHEN** uma operação entra no estado ocupado com o ponteiro sobre o separador de uma coluna do grid rolável da tabela de Fundamentos
- **THEN** o baseline capturado para esse grid DEVE ser o cursor de repouso (não o cursor transitório de redimensionamento) e, ao final da operação, o cursor DEVE voltar ao cursor original, sem permanecer "watch"

#### Scenario: Baseline em forma de lista do Tk

- **WHEN** o Tk devolve o cursor de repouso de um widget como uma lista (por exemplo `('sb_h_double_arrow',)`)
- **THEN** o sistema DEVE normalizá-la para o nome do cursor e tratar os cursores transitórios como repouso, nunca os usando como baseline

#### Scenario: Falha ao restaurar o cursor de repouso

- **WHEN** a restauração do baseline de um widget falha durante a saída do estado ocupado
- **THEN** o widget DEVE voltar ao cursor padrão, não permanecendo com o cursor "watch"

#### Scenario: Grids da tabela de Fundamentos terminam sincronizados

- **WHEN** a operação termina com o ponteiro sobre um dos grids da tabela de Fundamentos
- **THEN** os dois grids DEVEM apresentar o mesmo cursor entre si, ambos restaurados ao cursor original
