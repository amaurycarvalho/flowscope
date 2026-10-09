# noticias-panel Specification

## Purpose

Fornece a sub-aba "Notícias" na Análise Geral, com árvore dos artigos, pré-visualização do conteúdo, resumos por LLM e controles de atualização.

## Requirements

### Requirement: Sub-aba "Notícias" na Análise Geral

O sistema DEVE expor a sub-aba "Notícias" na "Análise Geral", organizando os itens em uma árvore e exibindo o conteúdo do item selecionado em um campo de texto. A árvore DEVE ter a raiz "Notícias" e, abaixo dela, as categorias de topo "Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição de Ações" e, por último, "Geral", cada uma seguindo a sub-estrutura ano → mês → categoria → item. A sub-aba DEVE oferecer os botões "Atualizar", "Abrir", um combobox de modelo ativo com a opção `None`, um botão de configuração com o ícone `ai-properties.png` e "Resumir pendentes", com barra de progresso durante a aquisição. O botão "I.A." textual NÃO DEVE mais existir. Trocar o item do combobox DEVE persistir imediatamente o novo provedor ativo e reavaliar o estado dos resumos; o combobox e o botão de configuração DEVEM ser desabilitados durante processamentos, junto com os demais controles.

#### Scenario: Árvore e pré-visualização

- **WHEN** a sub-aba "Notícias" é exibida com itens em cache
- **THEN** a árvore DEVE listar as categorias de topo com itens e a seleção DEVE exibir o texto do item

#### Scenario: "Geral" por último

- **WHEN** a árvore lista as categorias de topo com itens
- **THEN** a categoria "Geral" DEVE aparecer depois das categorias regulatórias

#### Scenario: Seleção da raiz

- **WHEN** o nó raiz "Notícias" é selecionado
- **THEN** a pré-visualização DEVE exibir a lista de todas as categorias com itens

#### Scenario: Árvore expandida só até o primeiro nível

- **WHEN** a árvore de notícias é carregada (inicialmente ou após "Atualizar")
- **THEN** a raiz DEVE estar expandida e as categorias de topo, os anos, os meses, os tipos e os itens DEVEM estar recolhidos

#### Scenario: Tipo de notícia no 3º nível da "Geral"

- **WHEN** os itens da categoria "Geral" são exibidos
- **THEN** o nível de categoria DEVE ser o tipo típico da notícia (ano → mês → tipo → item), e não a agência

#### Scenario: Tipo "Outros" para títulos não classificados

- **WHEN** um título da "Geral" não corresponde a nenhum tipo típico da whitelist
- **THEN** ele DEVE ser agrupado em "Outros"

#### Scenario: Tipos específicos por fonte nas demais seções

- **WHEN** os itens de uma seção regulatória são exibidos
- **THEN** o nível de categoria DEVE ser o ticker/emissor em censuras, o segmento em condições e a empresa em programas

#### Scenario: Atualização com progresso

- **WHEN** o usuário aciona "Atualizar"
- **THEN** a aquisição DEVE rodar em segundo plano com progresso e reexibir a árvore ao concluir

#### Scenario: Cancelamento reflete a carga parcial

- **WHEN** o usuário cancela a aquisição
- **THEN** a árvore DEVE ser remontada com os itens já persistidos assim que o worker encerrar, sem sobrescrever uma carga iniciada depois

#### Scenario: Sem itens

- **WHEN** não há itens para nenhuma categoria
- **THEN** a sub-aba DEVE exibir um estado vazio, sem erro

#### Scenario: Seletor de modelo e botão de configuração na barra

- **WHEN** a sub-aba "Notícias" é exibida
- **THEN** o combobox de modelo ativo e o botão de configuração com ícone DEVEM estar visíveis na barra de controles, no lugar antes ocupado pelo botão "I.A."

#### Scenario: Troca de modelo pelo combobox

- **WHEN** o usuário seleciona um provedor ativo no combobox
- **THEN** o provedor ativo DEVE ser persistido e o estado do botão "Resumir pendentes" DEVE ser reavaliado

### Requirement: Classificação da "Geral" por tipo de notícia

O sistema DEVE classificar cada notícia da "Geral" em um tipo típico derivado da whitelist de eventos, agrupando a árvore por ano → mês → tipo → item. A classificação DEVE incluir, no mínimo, os tipos "Negociação", "Listagem e Registro", "Ofertas e OPA", "Participações", "Reorganização Societária", "Recuperação e Liquidação", "Eventos de Capital", "Governança e Auditoria" e "Esclarecimentos e Oscilações". Títulos que não correspondam a nenhum tipo DEVEM ser agrupados em "Outros". Cada termo da whitelist DEVE estar associado a um tipo (nenhum termo da whitelist cai em "Outros").

#### Scenario: Título típico classificado
- **WHEN** uma notícia da "Geral" tem título de um evento da whitelist
- **THEN** ela DEVE ser agrupada no tipo correspondente

#### Scenario: Cobertura da whitelist
- **WHEN** todos os termos da whitelist são classificados
- **THEN** nenhum deles DEVE cair em "Outros"

### Requirement: Carga inicial somente do cache local

A sub-aba DEVE montar a árvore e a pré-visualização lendo apenas o cache local (índice de metadados, HTML, textos e resumos), sem consultar a B3 ao ser aberta ou ao trocar de aba. A listagem e a aquisição de novos itens DEVEM ocorrer somente pelo botão "Atualizar", em segundo plano, que DEVE também executar o housekeeping de deduplicação por conteúdo das notícias. A ausência de cache ou de índice DEVE resultar em estado vazio, sem erro, e entradas do índice sem HTML correspondente NÃO DEVEM aparecer.

#### Scenario: Abertura sem consultar a B3
- **WHEN** a sub-aba "Notícias" é aberta
- **THEN** a árvore DEVE ser montada apenas com o cache local, sem requisição à B3

#### Scenario: Cache local com itens indexados
- **WHEN** há itens no índice e o HTML correspondente em cache
- **THEN** a árvore DEVE exibi-los sem depender de rede

#### Scenario: Cache frio
- **WHEN** não há índice nem itens em cache
- **THEN** a sub-aba DEVE exibir o estado vazio, sem erro

#### Scenario: Entrada de índice sem HTML
- **WHEN** o índice referencia um HTML que não existe
- **THEN** o item NÃO DEVE ser exibido na árvore

#### Scenario: Atualizar reconstrói a partir da B3
- **WHEN** o usuário aciona "Atualizar"
- **THEN** a aquisição DEVE rodar em segundo plano, gravar o cache e o índice, o housekeeping de deduplicação DEVE ser executado e a árvore DEVE ser remontada a partir do cache local

#### Scenario: Deduplicação no Atualizar
- **WHEN** há notícias em cache com o mesmo conteúdo em datas ou URLs diferentes
- **THEN** após o "Atualizar" apenas o registro mais antigo DEVE permanecer na árvore

### Requirement: Pré-visualização e abertura do item

O sistema DEVE extrair o texto do HTML do item em cache para a pré-visualização e DEVE permitir abrir a URL do item no navegador padrão quando houver URL. Itens sem texto extraível DEVEM exibir uma mensagem informativa e itens sem URL NÃO DEVEM habilitar o botão "Abrir".

#### Scenario: Item com texto
- **WHEN** um item com HTML legível é selecionado
- **THEN** o texto extraído DEVE ser exibido na pré-visualização

#### Scenario: Item sem texto extraível
- **WHEN** o HTML do item não produz texto
- **THEN** a pré-visualização DEVE exibir a mensagem de ausência de texto

#### Scenario: Corpo do artigo da "Geral"
- **WHEN** um item da categoria "Geral" é pré-visualizado ou resumido
- **THEN** o texto DEVE ser extraído do corpo do artigo do Plantão B3 (`#conteudoDetalhe`), sem a moldura de busca e navegação da página

#### Scenario: Abrir no navegador
- **WHEN** o usuário aciona "Abrir" em um item com URL
- **THEN** a URL DEVE ser aberta no navegador padrão

#### Scenario: Item sem URL
- **WHEN** um item sem URL (censura, condição ou programa) é selecionado
- **THEN** o botão "Abrir" DEVE permanecer desabilitado

### Requirement: Documento vinculado sob demanda

Quando o corpo de uma notícia "Geral" for apenas um apontador para um documento, o sistema DEVE baixar e extrair o conteúdo vinculado ao selecionar a notícia e ao processar "Resumir pendentes". As URLs suportadas incluem o **visualizador da CVM RAD** (`rad.cvm.gov.br`) e o **visualizador do FNET** (`fnet.bmfbovespa.com.br`). O texto do documento extraído DEVE substituir o apontador no corpo e ser persistido no cache de textos, evitando novo download. Se o download não puder ser concluído (captcha habilitado, falha de rede ou formato inesperado), o corpo original DEVE ser mantido, sem erro.

Quando o documento vinculado for um PDF protegido por senha que não abre com senha vazia, o sistema DEVE solicitar a senha ao usuário no preview interativo, na thread da interface, e tentar novamente a extração com a senha informada, fora da thread da interface. A solicitação DEVE ser limitada a 3 tentativas por notícia/seleção (parametrizável), avisando sobre a senha incorreta e parando ao esgotar o limite. O texto obtido DEVE ser persistido no cache de textos e a senha NÃO DEVE ser persistida. Cancelar a solicitação DEVE manter o corpo original, sem erro. A solicitação DEVE ocorrer apenas no fluxo interativo; o resumo em lote NÃO DEVE abrir diálogo de senha.

Quando a extração do documento vinculado resultar parcial (ao menos uma página não extraída), a pré-visualização DEVE anotar a quantidade de páginas não extraídas antes do conteúdo. O texto parcial NÃO DEVE ser persistido no cache de textos nem usado para gerar resumo, de modo que a notícia permaneça pendente. A extração parcial DEVE ser retentada automaticamente quando a notícia for selecionada ou clicada novamente e quando "Resumir pendentes" for acionado, sem controle dedicado de "Tentar novamente".

#### Scenario: Pré-visualização resolve o documento vinculado da CVM
- **WHEN** uma notícia "Geral" com URL do visualizador da CVM RAD é selecionada
- **THEN** o conteúdo vinculado DEVE ser baixado, extraído e exibido no corpo

#### Scenario: Pré-visualização resolve o documento vinculado do FNET
- **WHEN** uma notícia "Geral" com URL do visualizador do FNET é selecionada
- **THEN** o PDF apontado pelo `iframe` do visualizador DEVE ser baixado, extraído e exibido no corpo

#### Scenario: Documento vinculado protegido solicita senha
- **WHEN** o documento vinculado é um PDF protegido cujo texto não foi extraído com senha vazia
- **THEN** o sistema DEVE abrir uma caixa de diálogo solicitando a senha

#### Scenario: Senha correta extrai e cacheia
- **WHEN** o usuário informa a senha correta do documento vinculado protegido
- **THEN** o sistema DEVE extrair o texto, persistí-lo no cache e exibi-lo no corpo

#### Scenario: Senha incorreta permite nova tentativa
- **WHEN** o usuário informa uma senha incorreta e ainda há tentativas disponíveis
- **THEN** o sistema DEVE informar a falha e permitir nova tentativa ou cancelamento

#### Scenario: Limite de tentativas atingido
- **WHEN** o usuário esgota as 3 tentativas de senha do documento vinculado
- **THEN** o sistema DEVE parar de solicitar a senha e manter o corpo original, sem erro

#### Scenario: Cancelamento mantém o corpo original
- **WHEN** o usuário cancela a solicitação de senha
- **THEN** o sistema DEVE manter o corpo original da notícia, sem erro

#### Scenario: Extração parcial é anotada
- **WHEN** a extração do documento vinculado resulta parcial
- **THEN** a pré-visualização DEVE anotar as páginas não extraídas antes do conteúdo

#### Scenario: Selecionar novamente retenta o documento vinculado
- **WHEN** o documento vinculado foi extraído parcialmente e o usuário seleciona ou clica na notícia novamente
- **THEN** o sistema DEVE refazer o download e a extração do documento vinculado, sem exigir controle dedicado

#### Scenario: Resumir pendentes retenta o documento vinculado
- **WHEN** o documento vinculado de uma notícia foi extraído parcialmente e o usuário aciona "Resumir pendentes"
- **THEN** o sistema DEVE refazer o download e a extração e, se completa, gerar o resumo; se ainda parcial, manter a notícia pendente

#### Scenario: Extração parcial não gera resumo
- **WHEN** o documento vinculado de uma notícia é extraído parcialmente
- **THEN** nenhum resumo DEVE ser gerado e a notícia DEVE permanecer pendente

#### Scenario: Resumo em lote usa o documento vinculado
- **WHEN** "Resumir pendentes" processa uma notícia "Geral" com documento vinculado
- **THEN** o resumo DEVE ser gerado a partir do conteúdo vinculado

#### Scenario: Cache evita novo download
- **WHEN** a notícia é reaberta após o documento vinculado já ter sido resolvido
- **THEN** o texto do cache DEVE ser reutilizado, sem novo download

#### Scenario: Captcha ou falha mantém o corpo
- **WHEN** o documento vinculado exige captcha, falha a rede ou vem em formato inesperado
- **THEN** a notícia DEVE exibir o corpo original, sem erro

#### Scenario: Apontador não resolvido é reprocessado
- **WHEN** o texto cacheado de uma notícia "Geral" é idêntico ao apontador atual (download anterior não concluído)
- **THEN** o download DEVE ser tentado novamente na próxima seleção ou em "Resumir pendentes"

#### Scenario: Apontador não resolvido não gera resumo
- **WHEN** "Resumir pendentes" processa uma notícia "Geral" cujo documento vinculado não pôde ser baixado
- **THEN** nenhum resumo DEVE ser gerado para ela e o item DEVE permanecer pendente para nova tentativa

#### Scenario: Lote não solicita senha
- **WHEN** o resumo em lote processa uma notícia cujo documento vinculado é protegido
- **THEN** o sistema NÃO DEVE abrir diálogo de senha e DEVE manter a notícia pendente

### Requirement: Contrato do resolvedor de documento vinculado injetado

O resolvedor de documento vinculado injetado no painel de notícias DEVE aceitar, na mesma chamada, o texto do apontador e a senha opcional. Uma incompatibilidade entre a assinatura do resolvedor e a forma como o painel o invoca NÃO DEVE propagar exceção: a notícia DEVE continuar sendo exibida e processada a partir do corpo original, e o lote DEVE manter o item pendente para nova tentativa. O resolvedor usado em produção (`baixar_conteudo_vinculado`) DEVE ser compatível com esse contrato.

#### Scenario: Resolvedor de produção resolve o vínculo sem erro de assinatura

- **WHEN** o painel usa o resolvedor de produção com uma notícia "Geral" cujo corpo aponta para uma URL suportada (CVM RAD ou FNET)
- **THEN** o download e a extração do conteúdo vinculado DEVEM ocorrer sem `TypeError`, e o conteúdo vinculado DEVE ser exibido no corpo

#### Scenario: Senha posicional é aceita pelo resolvedor

- **WHEN** o resolvedor de produção é chamado com o texto do apontador e uma senha como segundo argumento posicional
- **THEN** a chamada NÃO DEVE falhar por incompatibilidade de assinatura

#### Scenario: Falha do resolvedor não interrompe o painel

- **WHEN** o resolvedor injetado levanta exceção ao tentar baixar o documento vinculado
- **THEN** a notícia DEVE exibir o corpo original e o processamento em lote NÃO DEVE abortar

### Requirement: Resumo curto e longo por LLM

O sistema DEVE gerar, para cada notícia, um resumo curto e um longo usando a LLM, persistindo-os em cache por notícia. A geração DEVE reutilizar o serviço de resumo existente e tolerar falhas da LLM sem interromper o processamento em lote. Quando a LLM não estiver configurada, a sub-aba DEVE orientar a configuração.

#### Scenario: Geração de resumo
- **WHEN** a LLM está configurada e o artigo tem texto, mas não tem resumo
- **THEN** os resumos curto e longo DEVEM ser gerados e persistidos

#### Scenario: LLM não configurada
- **WHEN** a LLM não está configurada
- **THEN** a sub-aba DEVE orientar a configuração, sem gerar resumos

#### Scenario: Falha da LLM no lote
- **WHEN** a geração de resumo de um item falha durante o lote
- **THEN** o erro DEVE ser registrado e os demais itens DEVEM continuar

### Requirement: Ordem do resumo em lote das notícias

Ao acionar "Resumir pendentes" na sub-aba "Notícias", o sistema DEVE processar os itens sem `long_summary` agrupados pela categoria de topo na ordem "Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição de Ações" e "Geral" e, dentro de cada grupo, da notícia mais recente para a mais antiga segundo a data de publicação. Datas ausentes ou empatadas DEVEM ter desempate determinista, de modo que a ordem do lote seja estável entre execuções.

#### Scenario: Grupos processados na ordem definida
- **WHEN** há notícias pendentes em mais de uma categoria de topo
- **THEN** o lote DEVE concluir todos os pendentes de "Censuras Públicas" antes de "Condições Excepcionais", depois "Programas de Aquisição de Ações" e, por último, "Geral"

#### Scenario: Notícias mais recentes primeiro no grupo
- **WHEN** um grupo tem notícias pendentes publicadas em datas distintas
- **THEN** os resumos DEVEM ser gerados da data de publicação mais recente para a mais antiga

#### Scenario: Data ausente ou empatada tem ordem estável
- **WHEN** duas notícias do mesmo grupo têm a mesma data de publicação ou data ausente
- **THEN** a ordem entre elas DEVE ser determinista e repetível entre execuções

### Requirement: Persistência imediata do resumo em lote das notícias

Cada resumo gerado no lote das notícias DEVE ser gravado no cache persistente imediatamente após a sua geração, antes de processar a próxima notícia, de modo que uma interrupção — cancelamento, fechamento do aplicativo ou falha — preserve todos os resumos já gerados e perca no máximo a notícia em processamento. Gravações concorrentes entre o lote e a geração individual de resumo NÃO DEVEM perder nenhum resumo já gravado.

#### Scenario: Persistência imediata por notícia
- **WHEN** o lote gera o resumo de uma notícia e avança para a próxima
- **THEN** o resumo da notícia anterior já DEVE estar gravado no cache persistente, antes da geração da próxima

#### Scenario: Interrupção preserva os resumos já gerados
- **WHEN** o lote é cancelado, o aplicativo é fechado ou falha após gerar resumos de algumas notícias
- **THEN** os resumos já gerados DEVEM estar gravados no cache persistente

#### Scenario: Gravação concorrente não perde resumos
- **WHEN** o lote e a geração individual de resumo gravam resumos do mesmo escopo de notícias em paralelo
- **THEN** nenhum resumo já gravado DEVE ser perdido

### Requirement: Montagem assíncrona a partir do cache local

O sistema DEVE montar a árvore e a pré-visualização da sub-aba "Notícias" a partir do cache local fora da thread da interface, exibindo um estado de carregamento durante a leitura e aplicando o resultado por evento na thread do Tk. A leitura continua limitada ao cache local, sem consultar a B3, e trocar de aba ou acionar "Atualizar" DEVE descartar leituras obsoletas.

#### Scenario: Abertura com estado de carregamento
- **WHEN** a sub-aba "Notícias" é aberta
- **THEN** a leitura do cache local DEVE ocorrer fora da thread da interface e a árvore DEVE ser montada por evento ao concluir

#### Scenario: Interface responsiva durante a leitura
- **WHEN** a leitura do índice e a verificação do HTML dos itens está em andamento
- **THEN** a thread do Tk DEVE continuar processando eventos

#### Scenario: Sem consulta à B3
- **WHEN** a sub-aba "Notícias" é aberta ou o usuário troca de aba
- **THEN** nenhuma requisição à B3 DEVE ser feita durante a leitura do cache local

#### Scenario: Cache frio resulta em estado vazio
- **WHEN** não há índice nem itens em cache
- **THEN** a sub-aba DEVE exibir o estado vazio, sem erro

#### Scenario: Leitura obsoleta descartada
- **WHEN** uma nova leitura é iniciada antes de a anterior concluir
- **THEN** o resultado da leitura anterior NÃO DEVE sobrescrever a árvore montada pela mais recente

### Requirement: Remontagem pelo término do job, sem polling na interface

A remontagem da árvore de notícias após um cancelamento DEVE ser disparada pelo término do job que ainda estava encerrando, não por um laço de espera ativa na thread da interface. A thread do Tk NÃO DEVE executar polling repetido (ex.: consultas periódicas `is_alive`) aguardando o worker terminar. A remontagem DEVE preservar a carga mais recente: se um novo "Atualizar" já tiver começado, a remontagem do job encerrado NÃO DEVE sobrescrever o resultado da carga nova.

#### Scenario: Cancelamento remonta sem polling
- **WHEN** o usuário cancela a aquisição de notícias
- **THEN** a árvore DEVE ser remontada com os itens já persistidos quando o job publicar o término, sem a thread da interface consultar periodicamente a thread de trabalho

#### Scenario: Carga nova tem precedência
- **WHEN** um novo "Atualizar" é iniciado antes de o worker cancelado encerrar
- **THEN** a remontagem do job encerrado NÃO DEVE sobrescrever a árvore da carga nova

#### Scenario: Interface não fica em espera ativa
- **WHEN** há um job de notícias em cancelamento
- **THEN** a thread da interface NÃO DEVE manter um laço de espera ativa enquanto o worker encerra

### Requirement: Mensagem de conclusão honesta da aquisição de notícias

Ao concluir a aquisição de notícias acionada pelo usuário, o sistema DEVE informar o desfecho de forma honesta: quando ao menos um item for adquirido, a barra de status DEVE indicar a atualização; quando nenhum item for adquirido, o sistema NÃO DEVE afirmar que as notícias foram atualizadas, exibindo uma mensagem neutra. A tolerância a falhas de aquisição permanece: nenhum desses casos DEVE ser tratado como erro fatal.

#### Scenario: Notícias adquiridas informam atualização

- **WHEN** a aquisição conclui com ao menos um item adquirido
- **THEN** a barra de status DEVE indicar que as notícias foram atualizadas

#### Scenario: Nada adquirido não afirma atualização

- **WHEN** a aquisição conclui sem adquirir nenhum item, seja por ausência de itens ou por indisponibilidade tolerada
- **THEN** a barra de status NÃO DEVE afirmar "Notícias atualizadas!", exibindo mensagem neutra

### Requirement: Falha na leitura assíncrona sai do carregamento

Quando a leitura assíncrona do cache local da sub-aba "Notícias" falhar, o sistema DEVE abandonar o estado de carregamento e exibir uma mensagem informativa, sem permanecer carregando indefinidamente e sem erro fatal.

#### Scenario: Leitura falha não trava o carregamento

- **WHEN** a leitura assíncrona do cache local falha
- **THEN** a sub-aba DEVE sair do estado de carregamento e exibir mensagem informativa

#### Scenario: Leitura obsoleta não altera o estado

- **WHEN** uma leitura é substituída por outra mais recente e a anterior falha
- **THEN** o desfecho da leitura anterior NÃO DEVE alterar o estado apresentado
