# Spec Delta — llm-chat-tree

## ADDED Requirements

### Requirement: Campo `fontes` no JSON de resposta

O protocolo DEVE aceitar um campo opcional `fontes` no objeto JSON de resposta, relevante apenas no turno final (quando `solicitacoes` está vazio). Cada entrada DEVE aceitar `{"caminho": ..., "rotulo": ...}`, com `rotulo` opcional, e, por tolerância, uma string contendo apenas o caminho. Entradas sem `caminho` textual válido DEVEM ser ignoradas. Respostas sem `fontes`, em texto puro, ou o resumo forçado por limite de iterações DEVEM ser aceitos sem erro, com conjunto declarado vazio.

#### Scenario: Fontes declaradas no turno final
- **WHEN** a resposta final da LLM contém `"fontes": [{"caminho": "/documentos/PETR4/<chave>/texto", "rotulo": "Fato Relevante 15/07"}]`
- **THEN** o caminho e o rótulo DEVEM ser registrados como fontes declaradas da resposta

#### Scenario: Caminho declarado como string
- **WHEN** a resposta final contém `"fontes": ["/noticias/<grupo>/<chave>"]`
- **THEN** o caminho DEVE ser aceito como fonte declarada, sem rótulo

#### Scenario: Fontes em turno intermediário são ignoradas
- **WHEN** a resposta contém `solicitacoes` não vazias e também um campo `fontes`
- **THEN** o campo `fontes` NÃO DEVE ser usado para a resposta final do turno

#### Scenario: Entrada inválida é ignorada
- **WHEN** `fontes` contém um item sem `caminho` textual válido
- **THEN** o item DEVE ser descartado sem encerrar o loop, preservando as demais entradas

#### Scenario: Resposta sem fontes declaradas
- **WHEN** a resposta final não traz `fontes` ou o texto não é JSON reconhecido
- **THEN** o conjunto de fontes declaradas DEVE ser vazio, sem erro

### Requirement: Derivação determinística das fontes consultadas

O sistema DEVE derivar as fontes consultadas dos resultados de navegação bem-sucedidos de cada ciclo: os itens de `listar`, o caminho obtido por `obter` e os itens de `buscar`/`buscar_semantico`. Os caminhos DEVEM ser deduplicados preservando a primeira ocorrência e mantidos em ordem determinística. Resultados com erro NÃO DEVEM gerar fonte.

#### Scenario: `obter` gera fonte
- **WHEN** a LLM obtém com sucesso `/documentos/PETR4/<chave>/texto`
- **THEN** esse caminho DEVE integrar as fontes consultadas

#### Scenario: `listar` gera fonte dos filhos
- **WHEN** a LLM lista um nó interno com filhos
- **THEN** o caminho de cada filho retornado DEVE integrar as fontes consultadas

#### Scenario: Busca gera fonte dos resultados
- **WHEN** `buscar` ou `buscar_semantico` retorna itens
- **THEN** o caminho de cada item retornado DEVE integrar as fontes consultadas

#### Scenario: Duplicatas são deduplicadas
- **WHEN** o mesmo caminho é consultado em mais de um ciclo
- **THEN** ele DEVE aparecer uma única vez nas fontes consultadas

#### Scenario: Operação com erro não gera fonte
- **WHEN** uma operação de navegação responde com erro estruturado
- **THEN** nenhum caminho daquela operação DEVE integrar as fontes consultadas

### Requirement: Merge de rótulos declarados com caminhos da árvore

Cada caminho declarado pela LLM DEVE ser normalizado e validado contra a árvore de conhecimento. Caminho existente DEVE receber o rótulo declarado e ser incluído na lista final caso ainda não tenha sido derivado; caminho inexistente DEVE ser descartado e registrado em log. A lista final DEVE ter como base as fontes derivadas, com os rótulos declarados associados quando houver; sem declaradas, a lista final DEVE conter apenas as derivadas, sem rótulos.

#### Scenario: Caminho declarado existente recebe rótulo
- **WHEN** a LLM declara um caminho que integra as fontes derivadas
- **THEN** a fonte correspondente DEVE exibir o rótulo declarado

#### Scenario: Caminho declarado inexistente é descartado
- **WHEN** a LLM declara um caminho que não existe na árvore
- **THEN** ele NÃO DEVE integrar a lista final e o descarte DEVE ser registrado em log

#### Scenario: Caminho existente não derivado é incluído
- **WHEN** a LLM declara um caminho válido que a extração não capturou
- **THEN** ele DEVE integrar a lista final, com o rótulo declarado quando houver

#### Scenario: Sem fontes declaradas
- **WHEN** a LLM não declara `fontes`
- **THEN** a lista final DEVE conter as fontes derivadas, sem rótulos

#### Scenario: Declaração repetida não duplica
- **WHEN** a LLM declara o mesmo caminho mais de uma vez
- **THEN** a lista final DEVE conter o caminho uma única vez

### Requirement: Fontes fora do corpo da resposta

As instruções enviadas à LLM DEVEM proibir a citação da lista de fontes no corpo de `resposta` e exigir que as fontes consultadas sejam declaradas no campo estruturado `fontes` do JSON de resposta.

#### Scenario: Instrução proíbe citação no corpo
- **WHEN** o prompt de sistema e o formato de resposta são montados
- **THEN** eles DEVEM orientar a LLM a não listar nem citar as fontes dentro do texto de `resposta`

#### Scenario: Instrução exige o campo estruturado
- **WHEN** a resposta final é conclusiva
- **THEN** as instruções DEVEM orientar a LLM a declarar as fontes consultadas em `fontes`
