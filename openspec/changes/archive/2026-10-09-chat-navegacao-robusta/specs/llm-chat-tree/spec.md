## MODIFIED Requirements

### Requirement: Árvore de conhecimento cache-only resolvível por caminho

O sistema DEVE montar a árvore de conhecimento apenas a partir do estado local já em cache, sem resumir, extrair, baixar ou consultar a B3/CVM durante o chat. Todo nó DEVE ser resolvível por um caminho canônico. Nós internos DEVEM retornar os filhos imediatos (nome e metadado curto) e nós folha DEVEM retornar conteúdo. Nós sem dado (pendentes de resumo ou extração) NÃO DEVEM existir e DEVEM ser omitidos em silêncio por `listar`. A árvore NÃO DEVE conter nós internos vazios: um ramo estrutural sem itens DEVE ser omitido por completo, em vez de existir como folha vazia, que induziria `listar` a devolver `nao_interno`. O índice de caminhos DEVE viver em memória e o conteúdo pesado DEVE ser lido do cache de arquivos sob demanda.

#### Scenario: Navegação por caminho
- **WHEN** a LLM solicita um nó interno
- **THEN** o sistema DEVE devolver os filhos imediatos com nome e metadado curto

#### Scenario: Ramos grandes com nó interno por chave
- **WHEN** um ramo expõe itens por ticker ou por grupo (ex.: documentos e notícias)
- **THEN** ele DEVE ter um nó interno por chave (ex.: `/documentos/<ticker>`) cujos filhos são os conteúdos (ex.: `curto`, `longo`, `texto`), evitando uma listagem plana de todo o ramo

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

O sistema DEVE compor um manifesto único enviado como prefixo de sistema, contendo: persona e regras, descrição da árvore, **o mapa dos caminhos canônicos de cada ramo**, metadados curtos de abas/sub-abas/indicadores/campos/grupos, o protocolo de navegação e as listas de chaves (tickers, campos, abas, indicadores, grupos), sem valores pesados. O mapa e a descrição DEVEM listar apenas os ramos efetivamente presentes na árvore corrente, omitindo os caminhos canônicos de ramos ausentes, para não induzir a LLM a navegar caminhos inexistentes. Metadados iguais ao nome do nó DEVEM ser omitidos por redundantes. O manifesto DEVE ser byte-a-byte idêntico entre turnos enquanto a assinatura do estado não mudar. O manifesto DEVE respeitar um teto de 4.000 tokens; ao estourar, o ramo mais volumoso DEVE degradar para "só chaves". A assinatura do estado DEVE ser derivada do conjunto de arquivos (hash + mtime) e da watchlist.

#### Scenario: Mapa da árvore no manifesto
- **WHEN** o manifesto é montado
- **THEN** ele DEVE descrever os caminhos canônicos de cada ramo presente (ex.: `/documentos/<ticker>/curto`, `/noticias/<grupo>/indice`), para a LLM navegar sem adivinhar

#### Scenario: Ramo ausente não é anunciado
- **WHEN** a árvore corrente não contém um ramo (ex.: `/guidance` sem entradas ou `/flowscope/indicadores` vazio)
- **THEN** o mapa e a descrição NÃO DEVEM citar os caminhos canônicos desse ramo

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

O sistema DEVE interpretar a resposta da LLM de forma tolerante (bloco cercado, texto cru ou trecho entre a primeira `{` e a última `}`), aceitando apenas dicionário com a chave `resposta`; sem JSON reconhecido, o texto inteiro DEVE ser tratado como resposta final e o loop DEVE encerrar. O protocolo DEVE aceitar as operações `listar`, `obter`, `contar`, `existe`, `buscar`, `buscar_semantico` e `resetar_navegacao`. Operação desconhecida, caminho inválido, campo obrigatório ausente, **campo com tipo inválido**, curinga fora de `contar` ou em formato não suportado, **campo de busca inexistente**, regex inválida ou bloqueada, uso incorreto de `listar`/`obter` e falha inesperada DEVEM ser devolvidos à LLM como erro estruturado, sem encerrar o loop, incluindo uma **dica de recuperação** sempre que houver uma alternativa (ex.: `listar` numa folha DEVE sugerir `obter`; `obter` num nó interno DEVE sugerir `listar`; caminho inexistente DEVE sugerir `existe` e `listar(<pai>)` com o pai concreto; `em`/`max` inválidos DEVEM indicar o tipo esperado; `em` inexistente DEVE listar os campos disponíveis; regex inválida DEVE pedir correção de sintaxe). Resultados de busca sem casamento DEVEM trazer dica para ampliar a consulta. Quando `buscar_semantico` responder `indice_indisponivel`, o protocolo DEVE orientar a LLM a usar `buscar(caminho, regex, em=[...])` como busca determinística por campos, em vez de desistir da busca, e DEVE orientá-la a preferir o nó `indice` ou `buscar` a listar um ramo grande por inteiro. Todo erro estruturado devolvido à LLM DEVE ser registrado em log. As operações de um mesmo turno DEVEM ser executadas na ordem da lista e agregadas em um único bloco determinístico, sem timestamps.

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
- **WHEN** um caminho não existe, mesmo que o pai imediato também não exista (ex.: uma chave de notícia errada)
- **THEN** a dica de `caminho_invalido` DEVE indicar `listar(<ancestral>)` com o **ancestral existente mais próximo**, e não um caminho também inválido

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
