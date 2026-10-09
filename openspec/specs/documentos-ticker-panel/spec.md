# documentos-ticker-panel Specification

## Purpose

Disponibilizar uma sub-aba na "Análise do Ticker" para navegar, pré-visualizar e abrir os documentos em cache relacionados ao ticker selecionado.

## Requirements

### Requirement: Sub-aba "Documentos" na Análise do Ticker

O sistema DEVE adicionar a sub-aba "Documentos" à "Análise do Ticker". Ao se tornar ativa, a sub-aba DEVE carregar o catálogo de documentos do ticker apresentado e exibir a árvore correspondente.

#### Scenario: Sub-aba disponível
- **WHEN** o usuário navega para a "Análise do Ticker"
- **THEN** a sub-aba "Documentos" DEVE estar disponível

#### Scenario: Ativação carrega o catálogo
- **WHEN** a sub-aba "Documentos" se torna ativa para o ticker apresentado
- **THEN** a árvore DEVE ser montada a partir do catálogo do ticker

#### Scenario: Ticker sincronizado com a Evolução dos Fundamentos
- **WHEN** há um ticker fixado na sub-aba "Evolução dos Fundamentos"
- **THEN** a sub-aba "Documentos" DEVE carregar o catálogo desse mesmo ticker

### Requirement: Árvore hierárquica de documentos

A sub-aba DEVE exibir uma árvore com o nome do ticker no topo e, abaixo, três ramos: Guidance, Documentos e Direitos e obrigações. O ramo Documentos DEVE conter os níveis de ano, mês e categoria e, por fim, os arquivos. O ramo Guidance DEVE agrupar os guidances por ano e mês e exibir uma folha por guidance com valor (somente para tickers FII). O ramo Direitos e obrigações DEVE conter os sub-ramos Direitos e Obrigações. Pastas DEVEM expandir e recolher; somente arquivos DEVEM abrir.

#### Scenario: Estrutura da árvore
- **WHEN** o catálogo do ticker contém documentos em `2026/02/aviso-aos-acionistas`
- **THEN** a árvore DEVE exibir o ticker e os ramos Guidance, Documentos e Direitos e obrigações, com o documento sob Documentos → ano → mês → categoria → arquivos

#### Scenario: Duplo-clique em pasta
- **WHEN** o usuário dá duplo-clique em um nó de pasta
- **THEN** a pasta DEVE expandir ou recolher, sem abrir arquivo

### Requirement: Pré-visualização textual

Ao selecionar um arquivo, o sistema DEVE exibir uma pré-visualização textual em caixa de texto somente-leitura ao lado da árvore. Para arquivos HTML, o texto DEVE ser derivado do HTML; para PDFs, o texto DEVE ser extraído com `pypdf`. A extração DEVE ocorrer fora da thread da interface, com estado de carregamento, e DEVE resultar em mensagem informativa quando não houver texto extraível. A extração de PDF DEVE tolerar falhas por página, preservando o texto das páginas legíveis. O texto do documento DEVE ser lido do cache persistente de texto por documento; a conversão do arquivo DEVE ocorrer apenas quando o texto ainda não estiver em cache, e o resultado DEVE ser gravado no cache para os acessos seguintes. A pré-visualização de um documento DEVE ser composta pelo `long_summary`, por uma linha em branco, pelo texto do guidance do Relatório Gerencial quando houver, por outra linha em branco, por uma linha contendo `---`, outra linha em branco e o texto integral do documento. O guidance exibido DEVE ser o do Relatório Gerencial específico selecionado e DEVE usar a mesma formatação do item da coluna `Informações adicionais` da sub-aba "Fundamentos". Para documento que não seja um Relatório Gerencial ou sem guidance avaliado, o guidance DEVE ser omitido, mantendo-se a composição pelo `long_summary`, linha em branco, `---`, linha em branco e o texto integral; na ausência de `long_summary`, o guidance, quando houver, DEVE figurar imediatamente antes do `---`.

A leitura do cache de texto e a avaliação de necessidade de resumo/guidance do documento DEVEM ocorrer fora da thread da interface; a thread do Tk DEVE apenas publicar o estado de carregamento e exibir o resultado final.

Quando o PDF estiver protegido por senha e o texto não puder ser extraído com senha vazia, o sistema DEVE solicitar a senha ao usuário em caixa de diálogo, na thread da interface, e tentar novamente a extração com a senha informada, fora da thread da interface. A solicitação DEVE ser limitada a 3 tentativas por documento/seleção (parametrizável), avisando sobre a senha incorreta e parando ao esgotar o limite. O texto obtido DEVE ser gravado no cache e a senha NÃO DEVE ser persistida. Cancelar a solicitação DEVE resultar na mensagem informativa de ausência de texto, sem erro. A solicitação DEVE ocorrer apenas no fluxo interativo de pré-visualização; o resumo em lote NÃO DEVE abrir diálogo de senha.

Quando a extração resultar parcial (ao menos uma página não extraída), a pré-visualização DEVE anotar a quantidade de páginas não extraídas antes do conteúdo. O texto parcial NÃO DEVE ser gravado no cache nem usado para gerar resumo, de modo que o documento permaneça pendente. A extração parcial DEVE ser retentada automaticamente quando o documento for selecionado ou clicado novamente e quando "Resumir pendentes" for acionado, sem controle dedicado de "Tentar novamente".

#### Scenario: Seleção de PDF
- **WHEN** o usuário seleciona um arquivo PDF
- **THEN** o sistema DEVE exibir o texto extraído do PDF na caixa somente-leitura

#### Scenario: Seleção de HTML
- **WHEN** o usuário seleciona um arquivo HTML
- **THEN** o sistema DEVE exibir o texto derivado do HTML na caixa somente-leitura

#### Scenario: Extração sem texto
- **WHEN** o arquivo não tem texto extraível
- **THEN** o sistema DEVE exibir uma mensagem informativa, sem erro

#### Scenario: Página ilegível preserva o restante
- **WHEN** um PDF tem uma página ilegível e outras legíveis
- **THEN** o sistema DEVE exibir o texto das páginas legíveis, sem erro

#### Scenario: Texto parcial é anotado
- **WHEN** um PDF é extraído parcialmente
- **THEN** a pré-visualização DEVE exibir a anotação com o número de páginas não extraídas antes do texto

#### Scenario: Texto parcial não gera resumo
- **WHEN** um PDF é extraído parcialmente e a LLM está configurada
- **THEN** o sistema NÃO DEVE gerar resumo nem persistir o texto parcial, mantendo o documento pendente

#### Scenario: Selecionar novamente retenta a extração parcial
- **WHEN** o documento foi extraído parcialmente e o usuário o seleciona ou clica nele novamente
- **THEN** o sistema DEVE refazer a extração do documento, sem exigir controle dedicado

#### Scenario: Resumir pendentes retenta a extração parcial
- **WHEN** o documento foi extraído parcialmente e o usuário aciona "Resumir pendentes"
- **THEN** o sistema DEVE refazer a extração do documento e, se completa, gerar o resumo; se ainda parcial, mantê-lo pendente

#### Scenario: PDF protegido solicita senha
- **WHEN** o usuário seleciona um PDF protegido cujo texto não foi extraído com senha vazia
- **THEN** o sistema DEVE abrir uma caixa de diálogo solicitando a senha

#### Scenario: Senha correta extrai e cacheia
- **WHEN** o usuário informa a senha correta do PDF protegido
- **THEN** o sistema DEVE extrair o texto, gravá-lo no cache e exibi-lo na pré-visualização

#### Scenario: Senha incorreta permite nova tentativa
- **WHEN** o usuário informa uma senha incorreta e ainda há tentativas disponíveis
- **THEN** o sistema DEVE informar a falha e permitir nova tentativa ou cancelamento

#### Scenario: Limite de tentativas atingido
- **WHEN** o usuário esgota as 3 tentativas de senha do documento
- **THEN** o sistema DEVE parar de solicitar a senha e exibir a mensagem informativa, sem erro

#### Scenario: Cancelamento exibe ausência de texto
- **WHEN** o usuário cancela a solicitação de senha
- **THEN** o sistema DEVE exibir a mensagem informativa de ausência de texto, sem erro

#### Scenario: Lote não solicita senha
- **WHEN** o resumo em lote processa um PDF protegido
- **THEN** o sistema NÃO DEVE abrir diálogo de senha e DEVE pular o documento

#### Scenario: RG com guidance intercala o texto
- **WHEN** o usuário seleciona um Relatório Gerencial com guidance avaliado
- **THEN** a caixa DEVE exibir o `long_summary`, uma linha em branco, o texto do guidance, uma linha em branco, `---`, uma linha em branco e o texto integral do documento

#### Scenario: RG sem guidance mantém a composição
- **WHEN** o usuário seleciona um Relatório Gerencial sem guidance avaliado
- **THEN** a caixa DEVE exibir a composição sem o item de guidance

#### Scenario: Documento de outra categoria não exibe guidance
- **WHEN** o usuário seleciona um documento que não é um Relatório Gerencial e existe guidance no ledger do ticker
- **THEN** a caixa NÃO DEVE exibir o item de guidance

#### Scenario: Documento com resumo longo
- **WHEN** o documento selecionado tem `long_summary` preenchido
- **THEN** a caixa DEVE exibir o `long_summary`, seguido de linha em branco, `---`, linha em branco e o texto integral do documento

#### Scenario: Texto lido do cache
- **WHEN** o texto de um documento já está em cache e o documento é selecionado
- **THEN** a caixa DEVE exibir o texto do cache, sem reconverter o arquivo

#### Scenario: Conversão apenas no primeiro acesso
- **WHEN** o texto de um documento não está em cache e o documento é selecionado
- **THEN** o sistema DEVE converter o arquivo, gravar o texto no cache e exibir a pré-visualização

#### Scenario: Interface não bloqueada pela leitura de cache
- **WHEN** um documento já está em cache e é selecionado
- **THEN** a thread do Tk NÃO DEVE ler o cache nem avaliar resumo/guidance antes de exibir o estado de carregamento

#### Scenario: Resultado do preview é publicado na thread do Tk
- **WHEN** o worker de pré-visualização conclui a leitura do cache e a geração do resumo
- **THEN** a pré-visualização DEVE ser aplicada à caixa somente-leitura na thread do Tk

#### Scenario: Documento já resumido abre direto
- **WHEN** o documento tem texto em cache e resumo disponível
- **THEN** a pré-visualização DEVE ser exibida sem reavaliação síncrona na thread do Tk

#### Scenario: Lote recompõe o preview com o guidance
- **WHEN** o resumo em lote é aplicado ao documento atualmente selecionado e há guidance avaliado para ele
- **THEN** a pré-visualização recomposta DEVE incluir o item de guidance

### Requirement: Abertura no aplicativo padrão

O sistema DEVE abrir o arquivo selecionado no aplicativo padrão do sistema operacional — PDF no leitor de PDFs e HTML no navegador — por duplo-clique, pela tecla Enter ou pelo botão "Abrir documento". O botão "Abrir documento" DEVE permanecer desabilitado enquanto nenhum arquivo estiver selecionado, habilitando-se apenas quando um documento for selecionado.

#### Scenario: Abrir PDF
- **WHEN** o usuário dá duplo-clique em um arquivo PDF
- **THEN** o arquivo DEVE ser aberto no leitor de PDFs padrão do sistema

#### Scenario: Abrir HTML
- **WHEN** o usuário dá duplo-clique em um arquivo HTML
- **THEN** o arquivo DEVE ser aberto no navegador padrão do sistema

#### Scenario: Abrir pela tecla ou botão
- **WHEN** o usuário pressiona Enter ou clica em "Abrir documento" com um arquivo selecionado
- **THEN** o arquivo DEVE ser aberto no aplicativo padrão correspondente ao seu tipo

#### Scenario: Botão desabilitado sem documento selecionado
- **WHEN** nenhum arquivo está selecionado ou uma pasta está selecionada
- **THEN** o botão "Abrir documento" DEVE estar desabilitado

### Requirement: Estado vazio e atualização

A sub-aba DEVE exibir uma mensagem informativa quando o ticker não tem documentos em cache e DEVE oferecer um controle para atualizar o catálogo. Ao acionar o controle, o sistema DEVE adquirir os documentos do ticker (quando houver aquisição disponível), executar o housekeeping de deduplicação por conteúdo do ticker e remontar a árvore do catálogo.

#### Scenario: Ticker sem documentos
- **WHEN** o ticker selecionado não tem documentos em cache
- **THEN** a sub-aba DEVE exibir mensagem de ausência de documentos

#### Scenario: Atualização manual
- **WHEN** o usuário aciona o controle de atualização
- **THEN** o sistema DEVE adquirir os documentos do ticker (quando disponível), executar o housekeeping de deduplicação por conteúdo e remontar a árvore do ticker

#### Scenario: Deduplicação no Atualizar
- **WHEN** o ticker tem documentos em cache com o mesmo conteúdo, em datas ou raízes diferentes
- **THEN** após o "Atualizar" apenas o registro mais antigo DEVE permanecer na árvore

### Requirement: Seletor de modelo ativo e botão de configuração na barra de documentos

A sub-aba "Documentos" DEVE exibir, na barra de controles e imediatamente após o botão "Abrir documento", um combobox com os provedores ativos e a opção `None` e, logo após, um botão de configuração com o ícone `ai-properties.png`. O botão "I.A." textual NÃO DEVE mais existir. O combobox e o botão DEVEM estar disponíveis independentemente de haver documentos em cache ou ticker selecionado, pois a configuração de LLM é global. Trocar o item do combobox DEVE persistir imediatamente o novo provedor ativo e reavaliar o estado dos resumos; acionar o botão DEVE abrir o diálogo de configuração de LLM. Durante processamentos, o combobox e o botão DEVEM ser desabilitados e restaurados ao estado anterior, junto com os demais controles do painel.

#### Scenario: Botão disponível na barra

- **WHEN** o usuário navega para a sub-aba "Documentos"
- **THEN** o combobox de modelo ativo DEVE ser exibido imediatamente após o botão "Abrir documento" e o botão de configuração com ícone logo após o combobox

#### Scenario: Acionamento abre o diálogo de configuração

- **WHEN** o usuário clica no botão de configuração com ícone
- **THEN** o diálogo de configuração de LLM DEVE ser aberto

#### Scenario: Botão disponível sem documentos

- **WHEN** o ticker não tem documentos em cache ou nenhum ticker está selecionado
- **THEN** o combobox e o botão de configuração DEVEM permanecer habilitados

#### Scenario: Botão desabilitado durante cargas de dados

- **WHEN** uma carga de dados ou um resumo em lote está em andamento
- **THEN** o combobox e o botão de configuração DEVEM ser desabilitados junto com os demais controles do painel e restaurados ao término

#### Scenario: Troca de modelo pelo combobox

- **WHEN** o usuário seleciona um provedor ativo no combobox
- **THEN** o provedor ativo DEVE ser persistido e o estado do botão "Resumir pendentes" DEVE ser reavaliado

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

### Requirement: Mensagem de indisponibilidade de resumo

Quando um resumo não estiver preenchido, o sistema DEVE exibir `Resumo indisponível.` seguido de ` Clique no documento para análise.` se a LLM estiver configurada, ou seguido de ` Configure a LLM pelo botão de configuração e teste a comunicação.` caso contrário. A LLM DEVE ser considerada configurada quando o provedor for diferente de `none` e as dependências `[llm]` estiverem presentes.

#### Scenario: LLM configurada

- **WHEN** o resumo está ausente e a LLM está configurada
- **THEN** a mensagem DEVE orientar clicar no documento para análise

#### Scenario: LLM não configurada

- **WHEN** o resumo está ausente e a LLM não está configurada
- **THEN** a mensagem DEVE ser `Resumo indisponível. Configure a LLM pelo botão de configuração e teste a comunicação.`

### Requirement: Geração de resumo sob demanda

Ao selecionar um documento sem `long_summary` com a LLM configurada, o sistema DEVE enviar o texto integral do documento ao serviço de resumo, persistir o `short_summary` e o `long_summary` resultantes no catálogo do documento e exibir a pré-visualização composta. A geração DEVE ocorrer fora da thread da interface, com estado de carregamento, e resultados de seleções anteriores DEVEM ser descartados quando a seleção mudar. Quando não houver texto extraível para o documento, o sistema NÃO DEVE gerar resumo nem chamar a LLM, exibindo o marcador de ausência de texto.

#### Scenario: Documento sem resumo com LLM configurada
- **WHEN** o usuário seleciona um documento sem `long_summary` e a LLM está configurada
- **THEN** o sistema DEVE gerar os dois resumos, persistí-los e exibir o `long_summary` seguido de `---` e do texto do documento

#### Scenario: Resumo gerado fica disponível na lista
- **WHEN** o resumo de um documento é gerado
- **THEN** uma seleção posterior do agrupamento DEVE exibir o `short_summary` desse documento

#### Scenario: Resultado obsoleto descartado
- **WHEN** o usuário troca a seleção enquanto um resumo é gerado
- **THEN** o resultado da geração anterior NÃO DEVE ser exibido para a nova seleção

#### Scenario: LLM não configurada
- **WHEN** o usuário seleciona um documento sem `long_summary` e a LLM não está configurada
- **THEN** o sistema DEVE exibir a mensagem de indisponibilidade como `long_summary`, sem chamar a LLM

#### Scenario: Falha na geração
- **WHEN** a geração do resumo falha por indisponibilidade, comunicação, provedor ou cota
- **THEN** o sistema DEVE exibir a mensagem de indisponibilidade, sem interromper a interface

#### Scenario: Sem texto extraível não gera resumo
- **WHEN** o documento não tem texto extraível e a LLM está configurada
- **THEN** o sistema NÃO DEVE chamar a LLM nem persistir resumo, exibindo o marcador de ausência de texto

### Requirement: Campo de texto somente-leitura com atalhos e cursor

O campo de texto DEVE permanecer somente-leitura, impedindo alterações de conteúdo, e ao mesmo tempo DEVE aceitar os atalhos de teclado de seleção e cópia (Ctrl+A, Ctrl+C, Shift+setas) e a navegação pelo teclado, exibindo o cursor de foco. A seleção com o mouse DEVE continuar funcionando. O atalho Ctrl+A DEVE ser vinculado explicitamente ao campo, independentemente do mapeamento padrão do toolkit.

#### Scenario: Selecionar tudo com Ctrl+A
- **WHEN** o campo de texto está focado e o usuário pressiona Ctrl+A
- **THEN** todo o conteúdo DEVE ser selecionado

#### Scenario: Ctrl+A independente do toolkit
- **WHEN** o atalho padrão de "selecionar tudo" do toolkit não estiver associado a Ctrl+A (ex.: X11, onde `<<SelectAll>>` é Ctrl+barra)
- **THEN** Ctrl+A DEVE ainda selecionar todo o conteúdo do campo

#### Scenario: Cópia com Ctrl+C
- **WHEN** o usuário pressiona Ctrl+C com texto selecionado
- **THEN** a seleção DEVE ser copiada para a área de transferência

#### Scenario: Cursor visível
- **WHEN** o campo de texto recebe o foco
- **THEN** o cursor de inserção DEVE ser visível

#### Scenario: Edição bloqueada
- **WHEN** o usuário pressiona uma tecla que alteraria o conteúdo (ex.: uma letra)
- **THEN** o conteúdo DEVE permanecer inalterado

### Requirement: Cópia do conteúdo da pré-visualização

Quando a sub-aba "Documentos" estiver ativa, o botão "Copiar dados CSV" DEVE copiar o conteúdo atual do campo de texto da pré-visualização para a área de transferência e DEVE estar habilitado nessa sub-aba mesmo sem dados da B3 carregados. Nas demais sub-abas, o botão DEVE preservar o comportamento de cópia de CSV.

#### Scenario: Documentos ativa copia a pré-visualização
- **WHEN** a sub-aba "Documentos" está ativa e o usuário aciona o botão "Copiar dados CSV"
- **THEN** o conteúdo atual do campo de texto DEVE ser copiado para a área de transferência

#### Scenario: Botão habilitado em Documentos sem dados
- **WHEN** o usuário entra na sub-aba "Documentos" sem dados da B3 carregados
- **THEN** o botão "Copiar dados CSV" DEVE estar habilitado

#### Scenario: Outra sub-aba mantém a cópia de CSV
- **WHEN** a sub-aba ativa não é "Documentos" e o usuário aciona o botão "Copiar dados CSV"
- **THEN** o CSV do contexto atual DEVE ser copiado

### Requirement: Persistência da configuração de I.A.

O botão "Salvar" do diálogo de configuração de I.A. DEVE gravar a última configuração de `llm.chat` e fechar o diálogo. A configuração DEVE permanecer no arquivo após o fechamento da aplicação, DEVE ser recarregada para uso do sistema no próximo início e DEVE aparecer preenchida quando o diálogo for reaberto. A gravação das preferências da interface NÃO DEVE sobrescrever o bloco `llm`.

#### Scenario: Salvar fecha o diálogo
- **WHEN** o usuário aciona "Salvar" no diálogo de I.A.
- **THEN** a configuração DEVE ser gravada e o diálogo DEVE ser fechado

#### Scenario: Reabertura mostra a última configuração
- **WHEN** o diálogo de I.A. é reaberto após um salvamento
- **THEN** os campos DEVEM exibir os últimos valores salvos

#### Scenario: Configuração sobrevive ao fechamento da aplicação
- **WHEN** a aplicação é fechada após salvar a configuração de I.A.
- **THEN** o bloco `llm.chat` DEVE permanecer no arquivo e ser recarregado no próximo início

### Requirement: Rolagem vertical na árvore e na pré-visualização

A árvore de documentos e o campo de texto da pré-visualização DEVEM exibir uma barra de rolagem vertical visível e funcional, inclusive quando o painel for mais estreito que a largura requisitada pelo conteúdo. A rolagem vertical DEVE funcionar pela barra e pela roda do mouse.

#### Scenario: Barra visível na árvore
- **WHEN** a sub-aba "Documentos" exibe a árvore
- **THEN** a barra de rolagem vertical da árvore DEVE estar visível e mapeada

#### Scenario: Barra visível na pré-visualização
- **WHEN** a sub-aba "Documentos" exibe o campo de texto
- **THEN** a barra de rolagem vertical do campo DEVE estar visível e mapeada

#### Scenario: Painel estreito não oculta a barra
- **WHEN** o painel da árvore ou da pré-visualização é mais estreito que a largura requisitada pelo conteúdo
- **THEN** a barra de rolagem vertical DEVE permanecer visível

#### Scenario: Rolagem pela roda do mouse
- **WHEN** o ponteiro está sobre a árvore ou sobre o campo de texto e o usuário usa a roda do mouse
- **THEN** o conteúdo DEVE rolar verticalmente

### Requirement: Botão "Resumir pendentes" na barra de documentos

A sub-aba "Documentos" DEVE exibir um botão "Resumir pendentes" na barra de controles, imediatamente após o seletor de modelo ativo e o botão de configuração, sempre visível. O botão DEVE estar habilitado somente quando a LLM estiver configurada, nenhum resumo em lote estiver em andamento e existir, no ticker apresentado, ao menos um documento sem `long_summary` ou — quando a IA estiver ativa — ao menos um Relatório Gerencial (documento da categoria `Relatorio`, própria de FII) cuja avaliação de guidance no ledger esteja ausente ou não marcada como `ia`; caso contrário DEVE estar desabilitado. O Relatório Gerencial É o documento de FII usado como gatilho; não se DEVE depender da classificação de tipo do ticker, indisponível no painel. A LLM DEVE ser considerada configurada quando o provedor for diferente de `none` e as dependências `[llm]` estiverem presentes. A verificação de pendências de guidance DEVE consultar o ledger fora da thread da interface, junto da leitura do catálogo, e a thread do Tk NÃO DEVE ler o ledger ao reavaliar o botão. Ao salvar a configuração ou trocar o provedor pelo combobox, o estado do botão DEVE ser reavaliado. Durante o lote e durante as cargas de dados, o botão DEVE ser desabilitado e restaurado ao término, junto com os demais controles do painel.

#### Scenario: Botão disponível na barra

- **WHEN** o usuário navega para a sub-aba "Documentos"
- **THEN** o botão "Resumir pendentes" DEVE ser exibido imediatamente após o seletor de modelo ativo e o botão de configuração

#### Scenario: Habilitado com pendentes e LLM configurada

- **WHEN** a LLM está configurada e o ticker apresentado tem ao menos um documento sem `long_summary`
- **THEN** o botão "Resumir pendentes" DEVE estar habilitado

#### Scenario: Habilitado com RGs já resumidos pendentes de guidance

- **WHEN** a LLM está configurada, todos os documentos do ticker apresentado já têm `long_summary` e ao menos um Relatório Gerencial (categoria `Relatorio`) não tem avaliação de guidance marcada como `ia`
- **THEN** o botão "Resumir pendentes" DEVE estar habilitado

#### Scenario: Desabilitado com pendências de guidance sem IA

- **WHEN** a IA não está configurada e o único pendente é um Relatório Gerencial já resumido sem avaliação de guidance marcada como `ia`
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado

#### Scenario: Sem Relatório Gerencial não habilita por guidance

- **WHEN** o ticker apresentado só tem documentos de outras categorias, todos com `long_summary`, ainda que exista guidance no ledger
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado

#### Scenario: Desabilitado sem LLM configurada

- **WHEN** a LLM não está configurada
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado, sem ser ocultado

#### Scenario: Desabilitado sem pendentes

- **WHEN** todos os documentos do ticker apresentado já têm `long_summary`
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado

#### Scenario: Reavaliação quando o catálogo muda

- **WHEN** o último documento pendente passa a ter `long_summary` por um resumo individual (sem troca de aba)
- **THEN** o botão "Resumir pendentes" DEVE ser reavaliado e ficar desabilitado

#### Scenario: Reavaliação após salvar a configuração

- **WHEN** o usuário salva uma configuração de LLM válida no diálogo de configuração e há documentos pendentes
- **THEN** o botão "Resumir pendentes" DEVE passar a estar habilitado

#### Scenario: Reavaliação após trocar o modelo

- **WHEN** o usuário troca o provedor ativo pelo combobox e há documentos pendentes
- **THEN** o botão "Resumir pendentes" DEVE ser reavaliado conforme a disponibilidade da LLM

#### Scenario: Desabilitado durante o lote e cargas de dados

- **WHEN** um resumo em lote ou uma carga de dados está em andamento
- **THEN** o botão "Resumir pendentes" DEVE ser desabilitado junto com os demais controles do painel e restaurado ao término

### Requirement: Resumo em lote dos documentos pendentes

Ao acionar o botão "Resumir pendentes", o sistema DEVE processar, fora da thread da interface, os documentos do ticker apresentado sem `long_summary` e os Relatórios Gerenciais (categoria `Relatorio`, própria de FII) já resumidos cuja avaliação de guidance esteja pendente (entrada ausente no ledger ou não marcada como `ia`, com a IA ativa), em duas fases: preparar o texto — reutilizando o texto em cache e convertendo apenas quando ausente — e gerar o resumo via LLM, como se cada documento tivesse sido selecionado. Para os Relatórios Gerenciais já resumidos, a geração de resumo DEVE ser pulada e apenas a avaliação de guidance DEVE ocorrer, reaproveitando os resumos e o texto em cache, sem reextrair o arquivo. Cada resumo gerado DEVE ser gravado no cache persistente imediatamente após a sua geração e antes de processar o próximo documento, na própria thread de trabalho, de modo que uma interrupção — cancelamento, fechamento do aplicativo ou falha — preserve todos os resumos já gerados e perca no máximo o documento em processamento. O `short_summary` e o `long_summary` resultantes DEVEM ser refletidos no catálogo do documento. O andamento DEVE ser exibido na barra de status com a barra de progresso, uma fase por vez. Documentos sem texto extraível DEVEM ser pulados, sem chamada à LLM. Ao concluir, o sistema DEVE exibir o desfecho e reavaliar o estado do botão.

#### Scenario: Lote com documentos pendentes
- **WHEN** o usuário aciona "Resumir pendentes" com a LLM configurada e documentos sem `long_summary`
- **THEN** o sistema DEVE gerar e persistir os resumos de cada documento pendente e exibir o desfecho

#### Scenario: Lote avalia guidance de RG já resumido
- **WHEN** o usuário aciona "Resumir pendentes" e há um Relatório Gerencial já resumido com avaliação de guidance pendente
- **THEN** o sistema DEVE avaliar o guidance desse RG sem regerar seu resumo, reaproveitando os resumos e o texto em cache

#### Scenario: Progresso em duas fases
- **WHEN** o lote está em andamento
- **THEN** a barra de status e a barra de progresso DEVEM exibir a fase corrente ("preparar texto" e, em seguida, "resumir") com o avanço de cada uma, indicando quantos documentos foram concluídos e o total (ex.: `Preparando textos — 3/40`)

#### Scenario: Avanço da fase é exibido durante o processamento
- **WHEN** uma fase processa vários documentos e cada um leva tempo para concluir
- **THEN** a barra de progresso e a barra de status DEVEM avançar a cada documento concluído, sem aguardar o término da fase

#### Scenario: Fase instantânea continua visível
- **WHEN** a preparação dos textos é instantânea (todos os textos já estão em cache) e o lote avança para a fase de resumo
- **THEN** a fase "preparar texto" DEVE ter sido exibida na barra de status antes de "resumir", ainda que por tempo mínimo

#### Scenario: Documento já resumido é pulado
- **WHEN** um documento do ticker já tem `long_summary`
- **THEN** ele NÃO DEVE ser reprocessado no lote

#### Scenario: Documento sem texto extraível é pulado
- **WHEN** um documento pendente não tem texto extraível
- **THEN** o sistema NÃO DEVE chamar a LLM para ele e DEVE contabilizá-lo como pulado no desfecho

#### Scenario: Resumo gerado fica disponível na lista
- **WHEN** o lote conclui
- **THEN** uma seleção posterior do agrupamento DEVE exibir o `short_summary` dos documentos resumidos

#### Scenario: Persistência imediata por documento
- **WHEN** o lote gera o resumo de um documento e avança para o próximo
- **THEN** o resumo do documento anterior já DEVE estar gravado no cache persistente, antes da geração do próximo

#### Scenario: Interrupção preserva os resumos já gerados
- **WHEN** o lote é cancelado, o aplicativo é fechado ou falha após gerar resumos de alguns documentos
- **THEN** os resumos já gerados DEVEM estar gravados no cache persistente

#### Scenario: Interrupção por erro
- **WHEN** ocorre um erro em qualquer documento durante o lote
- **THEN** o lote DEVE ser interrompido, a barra de status DEVE reportar o documento e um motivo de falha amigável, e os controles DEVEM ser liberados

#### Scenario: Resultado do lote é descartado ao trocar de ticker
- **WHEN** o ticker apresentado muda enquanto o lote está em andamento
- **THEN** os resultados do lote anterior NÃO DEVEM ser aplicados ao novo ticker

### Requirement: Estado derivado do botão "Resumir pendentes" durante o lote

Enquanto um resumo em lote estiver em andamento, o estado derivado do botão "Resumir pendentes" DEVE permanecer desabilitado, ainda que o catálogo mude (documentos passando a ter `long_summary`) ou que a reavaliação de estado seja disparada no meio do processamento. Ao término do lote — conclusão ou interrupção — o estado DEVE ser reavaliado considerando a disponibilidade remanescente: habilitado se a LLM estiver configurada e ainda houver documentos sem `long_summary` ou, com IA ativa, Relatórios Gerenciais pendentes de guidance; desabilitado caso contrário.

#### Scenario: Reavaliação por documento resumido não reabilita durante o lote
- **WHEN** o lote está em andamento e documentos do ticker passam a ter `long_summary` a cada resultado aplicado
- **THEN** o botão "Resumir pendentes" DEVE permanecer desabilitado durante todo o processamento, até o término

#### Scenario: Reavaliação intermediária por resumo individual não reabilita durante o lote
- **WHEN** o lote está em andamento e uma reavaliação do catálogo é disparada (por resumo individual concorrente ou recarregamento do painel)
- **THEN** o botão "Resumir pendentes" DEVE permanecer desabilitado

#### Scenario: Reabilitação ao término com pendentes restantes
- **WHEN** o lote é interrompido por erro e ainda há documentos do ticker sem `long_summary` ou RGs pendentes de guidance
- **THEN** o botão "Resumir pendentes" DEVE voltar a ficar habilitado

#### Scenario: Desabilitado ao término sem pendentes restantes
- **WHEN** o lote conclui e todos os documentos do ticker já têm `long_summary` e não há RGs pendentes de guidance
- **THEN** o botão "Resumir pendentes" DEVE permanecer desabilitado

### Requirement: Leitura do catálogo fora da thread da interface

O sistema DEVE ler o catálogo de documentos do ticker fora da thread da interface e montar a árvore a partir de um evento na thread do Tk. Enquanto a leitura ocorre, a sub-aba DEVE exibir um estado de carregamento, e a thread do Tk DEVE permanecer responsiva. Trocar de ticker ou acionar a atualização DEVE descartar a leitura anterior em favor da mais recente.

#### Scenario: Ativação com estado de carregamento
- **WHEN** a sub-aba "Documentos" se torna ativa para o ticker apresentado
- **THEN** a leitura do catálogo DEVE ocorrer fora da thread da interface e a árvore DEVE ser montada por evento ao concluir

#### Scenario: Interface responsiva durante a varredura
- **WHEN** a varredura do catálogo de um ticker com muitos documentos está em andamento
- **THEN** a thread do Tk DEVE continuar processando eventos

#### Scenario: Cache frio resulta em estado vazio
- **WHEN** o ticker não tem documentos em cache
- **THEN** a sub-aba DEVE exibir a mensagem de ausência de documentos, sem erro

#### Scenario: Atualização manual relê em background
- **WHEN** o usuário aciona o controle de atualização
- **THEN** a nova varredura DEVE ocorrer fora da thread da interface e remontar a árvore por evento

#### Scenario: Troca de ticker descarta leitura obsoleta
- **WHEN** o ticker apresentado muda enquanto uma leitura de catálogo está em andamento
- **THEN** o resultado da leitura anterior NÃO DEVE ser aplicado ao novo ticker

### Requirement: Falha na pré-visualização sai do carregamento

Quando a extração de texto ou a geração do resumo da pré-visualização de um documento falhar, o sistema DEVE abandonar o estado de carregamento e exibir uma mensagem informativa na caixa de pré-visualização, sem permanecer "Carregando…" indefinidamente e sem erro fatal. O desfecho da pré-visualização de um documento que já não está mais selecionado NÃO DEVE alterar a caixa.

#### Scenario: Falha de extração ou resumo exibe mensagem

- **WHEN** o trabalho de pré-visualização falha ao extrair o texto ou ao gerar o resumo
- **THEN** a caixa de pré-visualização DEVE sair do estado de carregamento e exibir mensagem informativa

#### Scenario: Falha de documento não selecionado é descartada

- **WHEN** o trabalho de pré-visualização de um documento falha após o usuário selecionar outro documento
- **THEN** o desfecho NÃO DEVE alterar a pré-visualização do documento atualmente selecionado

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
