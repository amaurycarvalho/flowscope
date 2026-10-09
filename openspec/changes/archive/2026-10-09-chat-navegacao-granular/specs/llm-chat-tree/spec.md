## MODIFIED Requirements

### Requirement: Árvore de conhecimento cache-only resolvível por caminho

O sistema DEVE montar a árvore de conhecimento apenas a partir do estado local já em cache, sem resumir, extrair, baixar ou consultar a B3/CVM durante o chat. Todo nó DEVE ser resolvível por um caminho canônico. Nós internos DEVEM retornar os filhos imediatos (nome e metadado curto) e nós folha DEVEM retornar conteúdo. Nós sem dado (pendentes de resumo ou extração) NÃO DEVEM existir e DEVEM ser omitidos em silêncio por `listar`. A árvore NÃO DEVE conter nós internos vazios: um ramo estrutural sem itens (ex.: `/flowscope/abas` ou `/fundamentos/valores`) DEVE ser omitido por completo, em vez de existir como folha vazia. O índice de caminhos DEVE viver em memória e o conteúdo pesado DEVE ser lido do cache de arquivos sob demanda. Documentos e guidance DEVEM expor granularidade por item: `/documentos/<ticker>` DEVE ter um nó de índice e um nó interno por documento, e `/guidance/<ticker>` DEVE ter um nó de índice (ver os requisitos específicos).

#### Scenario: Navegação por caminho
- **WHEN** a LLM solicita um nó interno
- **THEN** o sistema DEVE devolver os filhos imediatos com nome e metadado curto

#### Scenario: Ramos grandes com nó interno por chave
- **WHEN** um ramo expõe itens por ticker ou por grupo (ex.: documentos e notícias)
- **THEN** ele DEVE ter um nó interno por chave (ex.: `/documentos/<ticker>` e `/documentos/<ticker>/<chave>`) cujos filhos são os conteúdos (ex.: `indice`, `curto`, `longo`, `texto`), evitando uma listagem plana de todo o ramo

#### Scenario: Conteúdo de nó folha
- **WHEN** a LLM solicita um nó folha com dado em cache
- **THEN** o sistema DEVE devolver o conteúdo daquele nó

#### Scenario: Nó sem dado é omitido
- **WHEN** um documento ou notícia não tem resumo nem texto em cache
- **THEN** o nó correspondente NÃO DEVE ser listado e NÃO DEVE ser citado

#### Scenario: Sem efeitos colaterais
- **WHEN** o chat navega a árvore
- **THEN** nenhum conteúdo DEVE ser gerado, extraído ou baixado

#### Scenario: Cache frio
- **WHEN** nenhuma fonte tem dado em cache
- **THEN** a árvore DEVE ser montada apenas com os ramos estruturais, sem erro

#### Scenario: Ramo interno vazio é omitido
- **WHEN** um ramo estrutural (ex.: `/flowscope/indicadores` ou `/fundamentos/valores`) não tem itens
- **THEN** ele NÃO DEVE existir como nó folha vazio e `existe(caminho)` DEVE ser falso, sem gerar `nao_interno` ao navegar

### Requirement: Manifesto estável como prefixo cacheável

O sistema DEVE compor um manifesto único enviado como prefixo de sistema, contendo: persona e regras, descrição da árvore, **o mapa dos caminhos canônicos de cada ramo**, metadados curtos de abas/sub-abas/indicadores/campos/grupos, o playbook de intenção→ramo, o protocolo de navegação e as listas de chaves (tickers, campos, abas, **sub-abas**, indicadores, grupos), sem valores pesados. O mapa e a descrição DEVEM listar apenas os ramos efetivamente presentes na árvore corrente, omitindo os caminhos canônicos de ramos ausentes, para não induzir a LLM a navegar caminhos inexistentes. O mapa DEVE anunciar o nó de aba (`/flowscope/abas/<aba>`) e as sub-abas. Metadados iguais ao nome do nó DEVEM ser omitidos por redundantes e metadados longos NÃO DEVEM integrar a seção de metadados (aplicado um teto curto por metadado), para que o conteúdo pesado não seja pré-injetado. O manifesto DEVE ser byte-a-byte idêntico entre turnos enquanto a assinatura do estado não mudar. O manifesto DEVE respeitar um teto de 4.000 tokens; ao estourar, o ramo mais volumoso DEVE degradar para "só chaves". A assinatura do estado DEVE ser derivada do conjunto de arquivos (hash + mtime) e da watchlist.

#### Scenario: Mapa da árvore no manifesto
- **WHEN** o manifesto é montado
- **THEN** ele DEVE descrever os caminhos canônicos de cada ramo presente (ex.: `/documentos/<ticker>/indice`, `/documentos/<ticker>/<chave>/texto`, `/noticias/<grupo>/indice`), para a LLM navegar sem adivinhar

#### Scenario: Ramo ausente não é anunciado
- **WHEN** a árvore corrente não contém um ramo (ex.: `/guidance` sem entradas ou `/flowscope/indicadores` vazio)
- **THEN** o mapa e a descrição NÃO DEVEM citar os caminhos canônicos desse ramo

#### Scenario: Abas e sub-abas anunciadas
- **WHEN** há abas com sub-abas na árvore corrente
- **THEN** o mapa DEVE anunciar `/flowscope/abas/<aba>` e a lista de chaves DEVE nomear as sub-abas de cada aba

#### Scenario: Metadado longo não integra o manifesto
- **WHEN** o metadado de um nó excede o teto curto (ex.: o texto integral de uma sub-aba)
- **THEN** a linha correspondente NÃO DEVE integrar a seção de metadados, preservando os metadados curtos e o teto de tokens

#### Scenario: Metadado redundante é omitido
- **WHEN** o metadado de um nó é igual ao seu nome
- **THEN** a linha correspondente NÃO DEVE integrar a seção de metadados do manifesto

#### Scenario: Manifesto idêntico entre turnos
- **WHEN** duas perguntas consecutivas são feitas sem mudança de estado
- **THEN** o manifesto DEVE ser byte-a-byte idêntico entre os turnos

#### Scenario: Reconstrução por mudança de estado
- **WHEN** fundamentos são recarregados, um resumo é cacheado ou a watchlist muda
- **THEN** a assinatura DEVE mudar, o manifesto DEVE ser recomputado e a navegação acumulada DEVE ser descartada

#### Scenario: Teto do manifesto
- **WHEN** o manifesto excede 4.000 tokens para a watchlist canônica
- **THEN** o ramo mais volumoso DEVE degradar para "só chaves" e um teste de regressão DEVE falhar se o teto for excedido

#### Scenario: Metadado ausente degrada
- **WHEN** não há metadado curado para uma chave
- **THEN** o manifesto DEVE exibir apenas a chave, sem erro

### Requirement: Protocolo de navegação JSON determinístico

O sistema DEVE interpretar a resposta da LLM de forma tolerante (bloco cercado, texto cru ou trecho entre a primeira `{` e a última `}`), aceitando apenas dicionário com a chave `resposta`; sem JSON reconhecido, o texto inteiro DEVE ser tratado como resposta final e o loop DEVE encerrar. O protocolo DEVE aceitar as operações `listar`, `obter`, `contar`, `existe`, `buscar`, `buscar_semantico` e `resetar_navegacao`. Operação desconhecida, caminho inválido, campo obrigatório ausente, campo com tipo inválido, curinga fora de `contar` ou em formato não suportado, campo de busca inexistente, regex inválida ou bloqueada, uso incorreto de `listar`/`obter` e falha inesperada DEVEM ser devolvidos à LLM como erro estruturado, sem encerrar o loop, incluindo uma dica de recuperação sempre que houver uma alternativa. Resultados de busca sem casamento DEVEM trazer dica para ampliar a consulta. Quando `buscar_semantico` responder `indice_indisponivel`, o protocolo DEVE orientar a LLM a usar `buscar(caminho, regex, em=[...])` como busca determinística por campos, e DEVE orientá-la a preferir o nó `indice` ou `buscar` a listar um ramo grande por inteiro. O bloco agregado de todo turno DEVE devolver um `foco` com o último caminho cujo conteúdo foi obtido com sucesso (`obter`), para resolver referências do turno seguinte. O manifesto/protocolo DEVEM orientar a LLM a **não prometer navegação futura** ("vou abrir"/"preciso ler"): quando faltarem dados, ela DEVE emitir `solicitacoes` com `resposta` nulo e só finalizar quando o conteúdo necessário já estiver no contexto, reusando o `foco` para o alvo já obtido em vez de reabri-lo. Todo erro estruturado devolvido à LLM DEVE ser registrado em log. As operações de um mesmo turno DEVEM ser executadas na ordem da lista e agregadas em um único bloco determinístico, sem timestamps.

#### Scenario: Resposta estruturada reconhecida
- **WHEN** a LLM devolve `{"resposta": null, "solicitacoes": [{"op": "contar", "caminho": "/documentos/PETR4/*"}]}`
- **THEN** o sistema DEVE executar a operação e agregar o resultado no bloco de navegação

#### Scenario: Formato não reconhecido encerra
- **WHEN** a resposta não contém um JSON com `resposta`
- **THEN** o texto inteiro DEVE ser tratado como resposta final, sem nova rodada

#### Scenario: Operação inválida devolve erro estruturado
- **WHEN** a LLM emite uma operação desconhecida ou um caminho inválido
- **THEN** o sistema DEVE devolver um erro estruturado à LLM e contabilizar a iteração

#### Scenario: Erro de navegação traz dica de recuperação
- **WHEN** a LLM usa `listar` num nó folha, `obter` num nó interno ou um caminho inexistente
- **THEN** o erro estruturado DEVE conter uma dica indicando a operação correta (`obter`, `listar` ou `existe`), permitindo a recuperação no ciclo seguinte

#### Scenario: Foco devolvido após obter
- **WHEN** a LLM executa `obter` com sucesso em um caminho
- **THEN** o bloco do turno DEVE conter `foco` com esse caminho, para o turno seguinte resolver referências como "nesse documento"

#### Scenario: Resposta não promete navegação
- **WHEN** a resposta depende de um documento que ainda não foi obtido
- **THEN** o manifesto/protocolo DEVEM orientar a LLM a emitir `solicitacoes` (com `resposta` nulo) em vez de finalizar prometendo abrir

#### Scenario: Campo com tipo inválido é recusado com dica
- **WHEN** a LLM envia `em` que não é lista, `max` que não é inteiro positivo, ou `caminho`/`regex`/`consulta` que não são texto
- **THEN** o sistema DEVE devolver erro estruturado `tipo_invalido` com a dica do tipo esperado, sem derrubar o loop

#### Scenario: Curinga usado fora de contar
- **WHEN** a LLM usa `*` no caminho de `listar`, `obter`, `existe` ou `buscar`
- **THEN** o erro estruturado DEVE ter motivo `caminho_com_curinga` e dica de que o curinga só é aceito em `contar`

#### Scenario: Curinga em formato não suportado
- **WHEN** a LLM usa um curinga que não é o sufixo `/*` em `contar` (ex.: `/*/x`)
- **THEN** o erro estruturado DEVE ter motivo `curinga_invalido` e dica de usar um único `*` no final do caminho

#### Scenario: Busca com campo inexistente
- **WHEN** a LLM emite `buscar` com `em` nomeando campos que não existem no ramo
- **THEN** o erro estruturado DEVE ter motivo `campo_inexistente` e listar os campos disponíveis

#### Scenario: Busca sem casamento orienta ampliar
- **WHEN** `buscar` é válido mas nenhum nó casa
- **THEN** o resultado DEVE conter uma dica para verificar a grafia, ampliar os termos ou `listar(caminho)`

#### Scenario: Caminho inexistente sugere o ancestral existente
- **WHEN** um caminho não existe, mesmo que o pai imediato também não exista
- **THEN** a dica de `caminho_invalido` DEVE indicar `listar(<ancestral>)` com o ancestral existente mais próximo, e não um caminho também inválido

#### Scenario: Campo carregado sob demanda não é campo inexistente
- **WHEN** `buscar` usa `em` com um campo cujo valor é carregado sob demanda (ex.: `texto` de documentos e notícias)
- **THEN** o sistema NÃO DEVE acusar `campo_inexistente`; sem casamento, DEVE orientar `obter(caminho)` para ler o conteúdo pesado

#### Scenario: Busca semântica valida o caminho
- **WHEN** a LLM emite `buscar_semantico` com um caminho inexistente
- **THEN** o erro estruturado DEVE ter motivo `caminho_invalido` (não `indice_indisponivel`)

#### Scenario: Regex com sintaxe inválida
- **WHEN** a LLM envia um regex sintaticamente inválido
- **THEN** o erro estruturado DEVE ter motivo `regex_invalida` e dica para corrigir a sintaxe, distinto de `regex_bloqueada`

#### Scenario: Falha inesperada vira erro recuperável
- **WHEN** uma operação falha de forma inesperada
- **THEN** o sistema DEVE devolver erro estruturado `erro_interno` com dica de tentar outra abordagem, sem encerrar o loop

#### Scenario: Busca semântica sem backend orienta alternativa
- **WHEN** a LLM emite `buscar_semantico` sem índice vetorial e recebe `indice_indisponivel`
- **THEN** o manifesto e o prompt DEVEM orientar a usar `buscar(caminho, regex, em=[...])` (determinística por campos) em vez de desistir da busca ou listar o ramo inteiro

#### Scenario: Ramo grande é pesquisado, não listado
- **WHEN** a LLM precisa de um item em um ramo grande (ex.: `/noticias/Geral`)
- **THEN** o manifesto DEVE orientá-la a usar o nó `indice` ou `buscar`, evitando `listar` de todo o ramo

#### Scenario: Erro de navegação é registrado em log
- **WHEN** qualquer erro estruturado é devolvido à LLM
- **THEN** o sistema DEVE registrar em log a operação, o caminho, o motivo e o detalhe do erro

#### Scenario: Agregação determinística
- **WHEN** a LLM emite múltiplas operações no mesmo turno
- **THEN** elas DEVEM ser executadas na ordem da lista e agregadas em um único bloco estável

#### Scenario: Limite de operações por turno
- **WHEN** a LLM emite mais de 8 operações em um turno
- **THEN** o excedente DEVE ser recusado com erro estruturado

## ADDED Requirements

### Requirement: Índice e granularidade por documento

O ramo `/documentos` DEVE expor, sob cada ticker, um nó folha `indice` e um nó interno por documento recuperável. O `indice` DEVE listar os documentos do mais recente ao mais antigo, uma linha por documento, com categoria, período (`AAAA/MM`) e nome, sinalizando quais têm resumo e/ou texto em cache, respeitando um teto de caracteres. Cada linha DEVE trazer uma **prévia** (trecho curto do resumo, cortado em fim de frase ou palavra, rotulado como tal) e o **tipo do documento** — `RG mensal` quando for um Relatório Gerencial mensal avaliado (obtido do ledger de guidance) e `documento` caso contrário —, para a LLM distinguir um RG de cartas/comunicados sem um segundo salto; quando houver mais de um documento no mesmo mês e categoria, a linha DEVE sinalizar a posição (`posição/total`). A prévia é apenas um indicador de conteúdo: os resumos completos continuam nas folhas `curto` e `longo` de cada documento. Cada nó de documento DEVE ter uma chave curta e estável e expor as folhas `curto` (resumo curto do documento), `longo` (resumo longo do documento) e `texto` (texto integral do documento, carregado sob demanda), omitindo cada folha sem dado. As folhas de conteúdo DEVEM trazer `metadado` legível (`resumo curto`, `resumo longo`, `texto integral`) para serem autoexplicativas em `listar`, e esses metadados de documento NÃO DEVEM integrar a seção de metadados do manifesto. O nó do documento DEVE trazer `metadado` legível (categoria, período e nome) e `campos` pesquisáveis (`categoria`, `periodo`, `nome`). O `texto` DEVE ser do documento-alvo, e não a concatenação do ticker, para que o texto integral do documento escolhido não seja truncado por outros documentos.

#### Scenario: Índice do ticker ordenado por recência
- **WHEN** a LLM lista ou obtém `/documentos/ALZR11/indice`
- **THEN** o conteúdo DEVE começar pelo documento mais recente (ano/mês e nome decrescentes) com categoria, período e nome

#### Scenario: Índice distingue RG mensal de carta
- **WHEN** um mesmo mês tem um RG mensal avaliado e uma carta/comunicado classificados como `Relatorio`
- **THEN** a linha do RG DEVE trazer o tipo `RG mensal` e a do outro `documento`, cada uma com um trecho do resumo que permita distingui-las

#### Scenario: Índice sinaliza documentos repetidos no mês
- **WHEN** há mais de um documento no mesmo mês e categoria
- **THEN** cada linha DEVE sinalizar a posição (`posição/total`)

#### Scenario: Prévia não substitui os resumos
- **WHEN** a pergunta pede o resumo curto (ou longo) de um documento
- **THEN** a LLM DEVE abrir a folha `curto` (ou `longo`) correspondente, e não responder só com a prévia do índice

#### Scenario: Nó por documento com conteúdo próprio
- **WHEN** a LLM pede `/documentos/ALZR11/<chave>` de um relatório
- **THEN** o `texto` DEVE conter o integral daquele documento, e `curto`/`longo` os resumos daquele documento

#### Scenario: Documento sem resumo omite a folha
- **WHEN** um documento só tem texto em cache
- **THEN** as folhas `curto`/`longo` NÃO DEVEM existir para aquele documento, sem erro

#### Scenario: Folhas de conteúdo rotuladas
- **WHEN** a LLM lista um nó de documento
- **THEN** as folhas `curto`/`longo`/`texto` DEVEM trazer `metadado` legível (`resumo curto`/`resumo longo`/`texto integral`)

#### Scenario: Síntese usa os resumos do documento
- **WHEN** a pergunta pede um resumo curto de um ou mais documentos
- **THEN** a LLM DEVE poder obter `curto`/`longo` de cada chave do índice, sem precisar ler o texto integral

#### Scenario: Metadados estruturados do documento
- **WHEN** a LLM `listar` em `/documentos/<ticker>` ou navega um nó de documento
- **THEN** categoria, período e nome DEVEM estar no `metadado` e em `campos` pesquisáveis

#### Scenario: Período responde sem ler o texto
- **WHEN** a pergunta pede o período de um documento
- **THEN** o período DEVE estar acessível pelo `metadado`/`campos` do nó, sem exigir a leitura do `texto`

### Requirement: Índice de guidance por ticker

O ramo `/guidance/<ticker>` DEVE expor um nó folha `indice` que agrega as entradas com guidance em ordem cronológica decrescente, uma linha por entrada com o período (`mmm/aa`) e o valor do guidance, e o rótulo curado do Relatório Gerencial associado. O `indice` NÃO DEVE substituir as folhas por mês: a LLM DEVE poder obter a entrada detalhada em `/guidance/<ticker>/<ano>/<mes>/<guidance>`. As folhas de guidance DEVEM trazer `campos` pesquisáveis com o período, o texto do guidance e o rótulo do RG.

#### Scenario: Evolução temporal em uma navegação
- **WHEN** a pergunta pede a evolução do guidance de um ticker
- **THEN** `obter(/guidance/<ticker>/indice)` DEVE devolver a série por período com o rótulo do RG, sem exigir `obter` de cada folha

#### Scenario: Detalhe de uma entrada
- **WHEN** a LLM abre `/guidance/<ticker>/<ano>/<mes>/<guidance>`
- **THEN** o conteúdo DEVE trazer o texto do guidance e o rótulo do RG associado

### Requirement: Foco de referência entre perguntas

A navegação DEVE manter um `foco` correspondente ao último caminho cujo conteúdo foi obtido com sucesso na sessão de navegação. O `foco` DEVE ser reenviado no bloco do turno e preservado entre perguntas enquanto a assinatura do estado não mudar, de modo que a LLM resolva referências anafóricas ("nesse RG", "esse último") para o referente obtido no turno anterior. O `foco` DEVE ser descartado junto da navegação acumulada (mudança de assinatura, "Limpar" ou `resetar_navegacao`).

#### Scenario: Referência ao documento do turno anterior
- **WHEN** a pergunta anterior obteve um documento e a pergunta atual diz "nesse RG" sem nomear outro
- **THEN** a LLM DEVE utilizar o `foco` para responder sobre o mesmo documento

#### Scenario: Foco descartado com a navegação
- **WHEN** a assinatura do estado muda ou a LLM emite `resetar_navegacao`
- **THEN** o `foco` DEVE ser descartado junto da navegação acumulada

### Requirement: Playbook de navegação por intenção

O manifesto DEVE anunciar um playbook que associe intenções típicas aos ramos da árvore: evolução/histórico de guidance → `/guidance/<ticker>` (começando pelo `indice`); Relatório Gerencial mensal → `/guidance/<ticker>/indice`, que associa cada período ao arquivo do RG, seguido do texto integral do documento correspondente; comentar/analisar um documento específico → o `texto` integral de `/documentos/<ticker>/<chave>/texto`; resumo **curto** de um documento → a folha `curto`; resumo **longo** de um documento → a folha `longo` (o índice traz apenas uma prévia); funcionalidades e objetivo do aplicativo → `/flowscope/abas` e `/flowscope/meta`. O playbook DEVE orientar a decidir pelo conteúdo: como a categoria de cache não distingue um RG mensal de cartas/comunicados, a LLM DEVE confirmar o alvo (pelo resumo ou pelo índice de guidance) antes de concluir; e, ao comentar um documento, DEVE abrir o `texto` integral em vez de responder só com resumos. Cada linha do playbook DEVE ser anunciada apenas quando o ramo correspondente existir.

#### Scenario: Comentar um documento abre o texto integral
- **WHEN** a pergunta pede comentar ou analisar um documento específico
- **THEN** o manifesto DEVE orientar a abrir o `texto` integral do alvo, e não apenas `curto`/`longo`

#### Scenario: Resumo de vários documentos usa os resumos
- **WHEN** a pergunta pede uma lista ou resumo de vários documentos
- **THEN** o manifesto DEVE orientar a obter as folhas `longo`/`curto` das chaves do índice

#### Scenario: RG mensal identificado pelo índice de guidance
- **WHEN** a pergunta pede o Relatório Gerencial de um período
- **THEN** o manifesto DEVE orientar a usar `/guidance/<ticker>/indice` para identificar o arquivo do RG e abrir o seu texto integral

#### Scenario: Pergunta sobre o aplicativo usa os ramos certos
- **WHEN** a pergunta é sobre o objetivo do FlowScope ou o conteúdo de uma sub-aba
- **THEN** o manifesto DEVE orientar a navegar `/flowscope/abas/<aba>`/`/flowscope/meta`, com as sub-abas anunciadas

#### Scenario: Guidance usa o índice
- **WHEN** a pergunta pede a evolução do guidance de um ticker
- **THEN** o manifesto DEVE orientar a começar por `/guidance/<ticker>/indice`
