# noticias-panel Specification

## Purpose

Fornece a sub-aba "Notícias" na Análise Geral, com árvore dos artigos, pré-visualização do conteúdo, resumos por LLM e controles de atualização.

## Requirements

### Requirement: Sub-aba "Notícias" na Análise Geral

O sistema DEVE expor a sub-aba "Notícias" na "Análise Geral", organizando os itens em uma árvore e exibindo o conteúdo do item selecionado em um campo de texto. A árvore DEVE ter a raiz "Notícias" e, abaixo dela, as categorias de topo "Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição de Ações" e, por último, "Geral", cada uma seguindo a sub-estrutura ano → mês → categoria → item. A sub-aba DEVE oferecer botões "Atualizar", "Abrir", "I.A." (configuração) e "Resumir pendentes", com barra de progresso durante a aquisição.

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

### Requirement: Classificação da "Geral" por tipo de notícia

O sistema DEVE classificar cada notícia da "Geral" em um tipo típico derivado da whitelist de eventos, agrupando a árvore por ano → mês → tipo → item. A classificação DEVE incluir, no mínimo, os tipos "Negociação", "Listagem e Registro", "Ofertas e OPA", "Participações", "Reorganização Societária", "Recuperação e Liquidação", "Eventos de Capital", "Governança e Auditoria" e "Esclarecimentos e Oscilações". Títulos que não correspondam a nenhum tipo DEVEM ser agrupados em "Outros". Cada termo da whitelist DEVE estar associado a um tipo (nenhum termo da whitelist cai em "Outros").

#### Scenario: Título típico classificado
- **WHEN** uma notícia da "Geral" tem título de um evento da whitelist
- **THEN** ela DEVE ser agrupada no tipo correspondente

#### Scenario: Cobertura da whitelist
- **WHEN** todos os termos da whitelist são classificados
- **THEN** nenhum deles DEVE cair em "Outros"

### Requirement: Carga inicial somente do cache local

A sub-aba DEVE montar a árvore e a pré-visualização lendo apenas o cache local (índice de metadados, HTML, textos e resumos), sem consultar a B3 ao ser aberta ou ao trocar de aba. A listagem e a aquisição de novos itens DEVEM ocorrer somente pelo botão "Atualizar", em segundo plano. A ausência de cache ou de índice DEVE resultar em estado vazio, sem erro, e entradas do índice sem HTML correspondente NÃO DEVEM aparecer.

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
- **THEN** a aquisição DEVE rodar em segundo plano, gravar o cache e o índice, e a árvore DEVE ser remontada a partir do cache local

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

#### Scenario: Pré-visualização resolve o documento vinculado da CVM
- **WHEN** uma notícia "Geral" com URL do visualizador da CVM RAD é selecionada
- **THEN** o conteúdo vinculado DEVE ser baixado, extraído e exibido no corpo

#### Scenario: Pré-visualização resolve o documento vinculado do FNET
- **WHEN** uma notícia "Geral" com URL do visualizador do FNET é selecionada
- **THEN** o PDF apontado pelo `iframe` do visualizador DEVE ser baixado, extraído e exibido no corpo

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
