## ADDED Requirements

### Requirement: Congelamento das colunas Ticker e Nome na tabela de Fundamentos

A sub-aba "Fundamentos" DEVE manter as colunas `Ticker` e `Nome` fixas à esquerda enquanto as demais colunas rolam horizontalmente. A tabela DEVE ser composta por dois Treeviews sincronizados, lado a lado, com a fronteira definida pela borda direita da última coluna congelada: o Treeview congelado exibe apenas `Ticker` e `Nome` e NÃO possui rolagem horizontal; o Treeview rolável exibe as demais colunas e mantém a rolagem horizontal. Os dois Treeviews DEVEM compartilhar a mesma barra de rolagem vertical, de modo que uma única rolagem mantenha as linhas alinhadas.

#### Scenario: Colunas congeladas permanecem visíveis
- **WHEN** o usuário rola a tabela horizontalmente para a direita
- **THEN** as colunas Ticker e Nome DEVEM permanecer visíveis à esquerda, sem rolar

#### Scenario: Rolagem vertical sincronizada
- **WHEN** o usuário rola a tabela verticalmente por qualquer um dos Treeviews ou pela barra de rolagem vertical
- **THEN** as mesmas linhas DEVEM permanecer alinhadas nos dois Treeviews

#### Scenario: Rolagem horizontal apenas nas colunas roláveis
- **WHEN** o usuário rola a tabela horizontalmente
- **THEN** apenas o Treeview rolável DEVE se deslocar, mantendo o painel congelado imóvel

### Requirement: Largura do painel congelado definida pelas colunas

A largura do painel congelado DEVE ser a soma das larguras das colunas `Ticker` e `Nome`, de modo que a fronteira entre os painéis seja a borda direita de `Nome`, reforçada por uma linha divisória vertical fixa e não arrastável. Redimensionar uma coluna congelada DEVE redimensionar o painel congelado, sem deixar espaço vazio (gap) nem cortar o conteúdo (clipping). As larguras persistidas das colunas DEVEM determinar a largura inicial do painel congelado. O painel rolável DEVE manter uma largura mínima, limitando o painel congelado quando as colunas congeladas crescerem além do espaço disponível.

#### Scenario: Redimensionar coluna congelada redimensiona o painel
- **WHEN** o usuário redimensiona a coluna `Ticker` ou `Nome`
- **THEN** a largura do painel congelado DEVE acompanhar a soma das duas colunas, sem gap nem clipping, e o painel rolável DEVE ocupar o restante do espaço

#### Scenario: Largura inicial derivada das colunas
- **WHEN** a tabela é montada com larguras persistidas para `Ticker` e `Nome`
- **THEN** o painel congelado DEVE iniciar com a soma dessas larguras

#### Scenario: Limite do painel rolável
- **WHEN** a soma das larguras das colunas congeladas excede o espaço disponível menos a largura mínima do painel rolável
- **THEN** o painel congelado DEVE ser limitado para preservar a largura mínima do painel rolável

### Requirement: Seleção de linha espelhada e única na tabela de Fundamentos

A seleção DEVE ser de uma única linha por vez e DEVE ser espelhada entre os dois Treeviews: ao selecionar uma linha em qualquer um dos painéis, a mesma linha DEVE ser selecionada no outro.

#### Scenario: Seleção espelhada
- **WHEN** o usuário seleciona uma linha no painel congelado ou no painel rolável
- **THEN** a linha correspondente DEVE ser marcada como selecionada no outro painel

#### Scenario: Seleção única
- **WHEN** o usuário tenta selecionar mais de uma linha com Ctrl ou Shift
- **THEN** apenas uma linha DEVE permanecer selecionada

### Requirement: Cópia CSV da tabela completa independente do congelamento

O comando "Copiar dados CSV" da sub-aba Fundamentos DEVE continuar copiando todas as colunas da tabela fundamentalista, na mesma ordem e com a mesma formatação, independentemente de as colunas Ticker e Nome estarem congeladas.

#### Scenario: CSV com todas as colunas
- **WHEN** o usuário aciona "Copiar dados CSV" na sub-aba Fundamentos
- **THEN** o conteúdo copiado DEVE conter o cabeçalho e as linhas com todas as colunas da tabela, incluindo Ticker e Nome

## MODIFIED Requirements

### Requirement: Persistência da largura das colunas da tabela fundamentalista
O sistema DEVE armazenar no arquivo de configuração (`config.json`) a largura de cada coluna da tabela fundamentalista — tanto das colunas congeladas `Ticker` e `Nome` quanto das colunas roláveis — quando o usuário a ajusta e DEVE restaurá-las na próxima execução, associando cada largura ao identificador estável da coluna. As larguras DEVEM ser agregadas dos dois Treeviews que compõem a tabela e DEVEM determinar a largura do painel congelado.

#### Scenario: Largura restaurada na próxima execução
- **WHEN** o usuário redimensiona uma coluna e reabre a aplicação
- **THEN** a coluna DEVE reaparecer com a largura ajustada

#### Scenario: Largura de coluna congelada restaurada
- **WHEN** o usuário redimensiona a coluna `Ticker` ou `Nome` no painel congelado e reabre a aplicação
- **THEN** a coluna congelada DEVE reaparecer com a largura ajustada e o painel congelado DEVE usar a soma das larguras restauradas

#### Scenario: Sem preferência salva
- **WHEN** não há larguras salvas para a tabela fundamentalista
- **THEN** o sistema DEVE usar as larguras padrão
