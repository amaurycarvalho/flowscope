## Purpose

Núcleo único de navegação da árvore de conhecimento, que executa as operações canônicas sobre o cache local e é reusado pelo chat, pelos subcomandos CLI e pelo servidor MCP, garantindo paridade de schemas, limites, paginação e erros.

## ADDED Requirements

### Requirement: Núcleo de navegação compartilhado e confinamento de leitura

O sistema DEVE prover um núcleo único que valida e executa as operações de navegação sobre a árvore de conhecimento, lendo estritamente o cache local do FlowScope. O núcleo NÃO DEVE resumir, extrair, baixar nem consultar a B3/CVM durante a navegação. O chat interno, os subcomandos CLI e o servidor MCP DEVEM reusar o mesmo núcleo, de modo que a mesma operação produza o mesmo resultado estruturado em qualquer superfície.

#### Scenario: Paridade entre superfícies

- **WHEN** a mesma operação (ex.: `listar /documentos/PETR4`) é executada pelo chat, pela CLI e pelo servidor MCP
- **THEN** o resultado estruturado DEVE ser o mesmo, respeitando os mesmos limites, a mesma paginação e os mesmos erros

#### Scenario: Leitura somente do cache local

- **WHEN** qualquer operação de navegação é executada
- **THEN** nenhuma chamada de rede, resumo, extração ou download DEVE ocorrer

### Requirement: Operações canônicas do núcleo

O núcleo DEVE suportar exatamente as operações `listar`, `obter`, `contar`, `existe`, `buscar`, `buscar_semantico` e o manifesto de navegação. O núcleo NÃO DEVE expor operações de reset de navegação nem de execução em lote. Operações DEVEM ser executadas na ordem em que são submetidas, com resultado por operação e sem timestamps.

#### Scenario: Operação desconhecida é recusada

- **WHEN** uma operação fora do conjunto canônico é submetida
- **THEN** o núcleo DEVE devolver erro estruturado com motivo de operação desconhecida e a lista de operações válidas

#### Scenario: Reset e lote não existem no núcleo

- **WHEN** o catálogo de operações do núcleo é enumerado
- **THEN** ele NÃO DEVE conter operações de reset de navegação nem de execução em lote

### Requirement: Ordenação determinística das listagens

As operações que devolvem conjuntos (`listar`, `buscar`, `buscar_semantico`) DEVEM devolver os itens em ordem determinística e estável, derivada do caminho canônico, para que a paginação por cursor seja reproduzível.

#### Scenario: Ordem estável entre chamadas

- **WHEN** a mesma listagem é solicitada duas vezes sem mudança de estado
- **THEN** a ordem dos itens DEVE ser idêntica

### Requirement: Paginação por cursor opaco

As operações `listar`, `buscar` e `buscar_semantico` DEVEM aceitar um argumento opcional `cursor` e DEVEM devolver `nextCursor` apenas quando houver mais resultados; a ausência de `nextCursor` DEVE significar fim dos resultados. O cursor DEVE ser um token opaco para o cliente, codificado de forma determinística e autocontida, contendo a versão, a operação, o caminho e a posição; ele NÃO DEVE depender de estado de sessão do servidor. Um cursor malformado, de versão desconhecida ou originado de outra operação ou caminho DEVE ser recusado com erro estruturado recuperável `cursor_invalido`. `listar` DEVE aplicar tamanho de página padrão de 100 itens, `buscar` DEVE manter o limite de 50 resultados e `buscar_semantico` DEVE manter o limite de 20 resultados.

#### Scenario: Continuação por cursor

- **WHEN** uma listagem devolve `nextCursor` e o cliente repete a operação com esse cursor
- **THEN** o núcleo DEVE devolver a página seguinte e omitir `nextCursor` quando a listagem terminar

#### Scenario: Fim dos resultados

- **WHEN** todos os itens disponíveis já foram devolvidos
- **THEN** a resposta NÃO DEVE conter `nextCursor`

#### Scenario: Cursor inválido

- **WHEN** o cliente envia um cursor malformado, de versão desconhecida ou pertencente a outra operação ou caminho
- **THEN** o núcleo DEVE devolver erro estruturado com motivo `cursor_invalido` e uma dica de recuperação, sem encerrar o fluxo

#### Scenario: Paginação é sensível a mudança de estado

- **WHEN** o estado local muda entre duas páginas
- **THEN** a paginação DEVE ser tratada como melhor esforço, podendo deslocar itens, e o cliente DEVE poder refazer a operação para uma nova visão

### Requirement: Paginação de conteúdo pesado por offset e limite

A operação `obter` DEVE manter a paginação explícita por `offset` (inteiro maior ou igual a zero) e `limite` (inteiro maior que zero) para nós de conteúdo pesado, devolvendo o trecho `[offset, offset+limite)`, o total de caracteres, o `offset` e o `limite` aplicados e o indicador de continuação. Sem os campos, DEVE devolver a página padrão a partir do início. `obter` NÃO DEVE usar cursor.

#### Scenario: Página intermediária de conteúdo pesado

- **WHEN** `obter` recebe `offset` e `limite` válidos sobre um texto maior que o limite
- **THEN** o resultado DEVE conter o trecho correspondente e sinalizar o total e a continuação

#### Scenario: Offset além do fim

- **WHEN** o `offset` é maior ou igual ao total do texto
- **THEN** o resultado DEVE ser vazio e sinalizar que não há continuação, sem erro

### Requirement: Erros estruturados recuperáveis

O núcleo DEVE devolver, para falhas de domínio recuperáveis (ex.: caminho inválido, campo ausente, tipo inválido, curinga inválido, regex inválida ou bloqueada, timeout de regex, campo inexistente, índice indisponível, cursor inválido), um erro estruturado com `motivo`, `detalhe` e, quando houver alternativa, `dica` de recuperação. Esses erros NÃO DEVEM ser tratados como falha interna. Toda falha inesperada DEVE ser devolvida como erro recuperável de erro interno, sem encerrar o fluxo do chamador, e todo erro estruturado DEVE ser registrado em log.

#### Scenario: Erro recuperável traz dica

- **WHEN** uma operação falha de forma recuperável
- **THEN** o erro estruturado DEVE conter `motivo`, `detalhe` e, quando aplicável, `dica`

#### Scenario: Falha inesperada vira erro interno

- **WHEN** uma operação falha de forma inesperada
- **THEN** o núcleo DEVE devolver erro estruturado de erro interno e continuar apto a executar novas operações

### Requirement: Rejeição de traversal em caminhos

O núcleo DEVE tratar caminhos como canônicos e DEVE recusar segmentos de traversal (`.` e `..`) com erro estruturado de caminho inválido, além de normalizar barras redundantes.

#### Scenario: Segmento de traversal recusado

- **WHEN** um caminho contém um segmento `.` ou `..`
- **THEN** o núcleo DEVE devolver erro estruturado com motivo de caminho inválido, sem resolver o caminho

### Requirement: Limites canônicos da navegação

O núcleo DEVE aplicar os limites canônicos da navegação de forma centralizada: no máximo 50 resultados por `buscar` (sinalizando truncamento quando exceder), trecho de no máximo 200 caracteres por resultado de busca, página de até 12.000 caracteres por `obter` de conteúdo pesado, timeout de 100 ms por regex, bloqueio de padrões regulares catastróficos e teto de 4.000 tokens do manifesto. As superfícies DEVEM consumir esses limites do núcleo, sem redefini-los.

#### Scenario: Busca truncada sinaliza

- **WHEN** `buscar` casa mais de 50 nós
- **THEN** o resultado DEVE ser truncado em 50 e sinalizado como truncado

#### Scenario: Timeout de regex

- **WHEN** uma busca excede 100 ms
- **THEN** o núcleo DEVE abortar a busca e devolver erro estruturado com motivo de timeout de regex

### Requirement: Exposição do manifesto de navegação

O núcleo DEVE expor o manifesto de navegação (persona, descrição da árvore, mapa de caminhos, listas de chaves, playbook e protocolo) de forma determinística e byte-a-byte estável enquanto a assinatura do estado não mudar, respeitando o teto de tokens, para reuso pelo servidor MCP.

#### Scenario: Manifesto determinístico

- **WHEN** o manifesto é solicitado duas vezes sem mudança de estado
- **THEN** o conteúdo DEVE ser idêntico entre as chamadas
