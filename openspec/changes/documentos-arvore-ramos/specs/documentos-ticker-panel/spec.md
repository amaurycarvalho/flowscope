## MODIFIED Requirements

### Requirement: Árvore hierárquica de documentos

A sub-aba DEVE exibir uma árvore com o nome do ticker no topo e, abaixo, três ramos: Guidance, Documentos e Direitos e obrigações. O ramo Documentos DEVE conter os níveis de ano, mês e categoria e, por fim, os arquivos. O ramo Guidance DEVE agrupar os guidances por ano e mês e exibir uma folha por guidance com valor (somente para tickers FII). O ramo Direitos e obrigações DEVE conter os sub-ramos Direitos e Obrigações. Pastas DEVEM expandir e recolher; somente arquivos DEVEM abrir.

#### Scenario: Estrutura da árvore
- **WHEN** o catálogo do ticker contém documentos em `2026/02/aviso-aos-acionistas`
- **THEN** a árvore DEVE exibir o ticker e os ramos Guidance, Documentos e Direitos e obrigações, com o documento sob Documentos → ano → mês → categoria → arquivos

#### Scenario: Duplo-clique em pasta
- **WHEN** o usuário dá duplo-clique em um nó de pasta
- **THEN** a pasta DEVE expandir ou recolher, sem abrir arquivo

### Requirement: Lista Markdown do agrupamento

Ao selecionar um nó de agrupamento da árvore (ticker, ramo Documentos, ano, mês, categoria, ramo Guidance, ano ou mês do guidance), o sistema DEVE exibir no campo de texto uma lista textual, em Markdown, dos itens contidos nesse agrupamento. Para os documentos, o agrupamento selecionado DEVE ser o cabeçalho de nível `#` e cada sub-agrupamento contido DEVE incrementar o nível (`##`, `###`, ...), com cada documento como item de lista seguido do seu `short_summary`. Para o ramo Guidance e seus anos/meses, cada guidance DEVE aparecer como um item de lista com o texto formatado do guidance.

#### Scenario: Agrupamento do ticker selecionado
- **WHEN** o usuário seleciona o nó do ticker
- **THEN** o campo de texto DEVE exibir o ticker como `#`, os anos como `##`, os meses como `###`, as categorias como `####` e os documentos como itens de lista com seus resumos curtos

#### Scenario: Ramo Documentos selecionado
- **WHEN** o usuário seleciona o ramo Documentos
- **THEN** o campo de texto DEVE exibir os anos como `##`, os meses como `###`, as categorias como `####` e os documentos como itens de lista com seus resumos curtos

#### Scenario: Agrupamento de categoria selecionado
- **WHEN** o usuário seleciona um nó de categoria
- **THEN** a categoria DEVE ser o cabeçalho de nível `#` e os documentos contidos DEVEM aparecer como itens de lista com seus resumos curtos

#### Scenario: Documento sem resumo curto na lista
- **WHEN** um documento da lista não tem `short_summary` preenchido
- **THEN** o item DEVE exibir a mensagem de resumo indisponível definida pela regra de indisponibilidade

#### Scenario: Agrupamento de guidance selecionado
- **WHEN** o usuário seleciona o ramo Guidance, um ano ou um mês do guidance
- **THEN** o campo de texto DEVE exibir todos os guidances contidos nesse agrupamento, cada um como um item de lista com o texto formatado do guidance

## ADDED Requirements

### Requirement: Ramo Guidance da árvore de documentos

O sistema DEVE exibir o ramo Guidance apenas para tickers FII — identificados pela presença de documentos da categoria `Relatorio` no catálogo do ticker. O ramo DEVE agrupar as entradas de guidance com valor por ano e mês da data do relatório, exibindo uma folha por entrada. O rótulo da folha DEVE ser o texto formatado do guidance. Tickers FII sem nenhuma entrada de guidance com valor DEVEM exibir o ramo Guidance vazio. Ao selecionar uma folha, o campo de texto DEVE exibir o texto formatado do guidance e, em linha separada ao final, o rótulo curado do Relatório Gerencial associado, no formato `Relatório Gerencial — <mmm/aa> (<nome do arquivo>)`. Ao dar duplo-clique na folha, o foco da árvore DEVE saltar para a folha do Relatório Gerencial associado na ramificação Documentos, expandindo os ancestrais; quando o documento associado não estiver no catálogo apresentado, a navegação NÃO DEVE ocorrer nem falhar.

#### Scenario: FII com guidance exibe o ramo
- **WHEN** o ticker apresentado é FII e possui ao menos uma entrada de guidance com valor em cache
- **THEN** a árvore DEVE exibir o ramo Guidance com os anos, meses e uma folha por guidance

#### Scenario: Folha exibe o texto e o RG associado
- **WHEN** o usuário seleciona uma folha de guidance
- **THEN** o campo de texto DEVE exibir o texto formatado do guidance e, em linha separada, o rótulo curado do Relatório Gerencial associado

#### Scenario: Duplo-clique salta para o RG associado
- **WHEN** o usuário dá duplo-clique em uma folha de guidance cujo Relatório Gerencial está no catálogo apresentado
- **THEN** a árvore DEVE expandir os ancestrais do RG e selecioná-lo na ramificação Documentos, sem abrir o arquivo no aplicativo padrão

#### Scenario: RG associado ausente do catálogo
- **WHEN** o usuário dá duplo-clique em uma folha de guidance cujo Relatório Gerencial não está no catálogo apresentado
- **THEN** o sistema NÃO DEVE saltar nem falhar, mantendo a seleção atual

#### Scenario: FII sem guidance exibe ramo vazio
- **WHEN** o ticker apresentado é FII e não possui nenhuma entrada de guidance com valor em cache
- **THEN** a árvore DEVE exibir o ramo Guidance sem folhas

#### Scenario: Não-FII não exibe o ramo
- **WHEN** o catálogo do ticker apresentado não contém documentos da categoria `Relatorio`
- **THEN** a árvore NÃO DEVE exibir o ramo Guidance

### Requirement: Expansão inicial da árvore de documentos

Na primeira exibição de um ticker na sessão atual e a cada troca do ticker apresentado, a árvore DEVE ser exibida expandida apenas até o primeiro nível, com o nome do ticker aberto e os ramos Guidance, Documentos e Direitos e obrigações visíveis e recolhidos. Exibições seguintes do mesmo ticker DEVEM preservar o estado de expansão e a seleção do usuário.

#### Scenario: Primeira exibição expande só o primeiro nível
- **WHEN** o ticker apresentado é exibido pela primeira vez na sessão
- **THEN** o nome do ticker DEVE estar aberto e os três ramos DEVEM estar visíveis e recolhidos

#### Scenario: Troca de ticker reaplica o primeiro nível
- **WHEN** o ticker apresentado muda
- **THEN** a árvore DEVE ser exibida com o novo ticker aberto e os três ramos recolhidos

### Requirement: Remontagem da árvore de documentos após o lote de resumos

Ao término do processamento de "Resumir pendentes" — conclusão ou interrupção —, o sistema DEVE remontar a árvore da sub-aba "Documentos" a partir do cache atualizado, refletindo novos resumos e novas avaliações de guidance. A remontagem DEVE ocorrer fora da thread da interface e DEVE preservar o arquivo selecionado quando ele ainda existir, reexibindo a sua pré-visualização.

#### Scenario: Árvore remontada ao término do lote
- **WHEN** o lote de resumos termina
- **THEN** a árvore DEVE ser remontada a partir do cache atualizado, incluindo os novos resumos e as novas avaliações de guidance

#### Scenario: Seleção preservada
- **WHEN** o lote termina e o arquivo selecionado continua no catálogo
- **THEN** o sistema DEVE manter o arquivo selecionado e reexibir a sua pré-visualização
