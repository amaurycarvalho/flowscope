# noticias-chat-context Specification

## Purpose

Disponibiliza o conteúdo das notícias em cache como fonte de contexto da aba de chat "Chat AI", com a relevância por ticker inferida pela LLM. A fonte opera em duas camadas: um índice compacto de todos os itens e a leitura do resumo/texto integral sob demanda pelas chaves.

## Requirements

### Requirement: Relevância por ticker inferida pela LLM

O sistema NÃO DEVE exigir um seletor de escopo de ticker. O ramo `/noticias` DEVE ser oferecido na árvore e a LLM DEVE selecionar as notícias relacionadas ao ticker referido na pergunta, inferido a partir dela, navegando o índice.

#### Scenario: Pergunta sobre um ticker

- **WHEN** a pergunta menciona um ticker específico
- **THEN** a LLM DEVE buscar no ramo `/noticias` os itens relacionados a esse ticker

#### Scenario: Pergunta geral de mercado

- **WHEN** a pergunta é sobre o mercado sem um ticker específico
- **THEN** a LLM DEVE selecionar os itens relacionados navegando o índice

### Requirement: Leitura somente do cache local

A fonte de notícias do chat NÃO DEVE consultar a B3 nem extrair ou gerar conteúdo: ela DEVE ler apenas o índice de metadados e o conteúdo já em cache local, tanto ao montar o contexto quanto ao ler o conteúdo integral das chaves, de modo que uma pergunta não fique presa à indisponibilidade da rede nem a processamentos não solicitados.

#### Scenario: Montagem sem rede

- **WHEN** a aba "Chat AI" monta o contexto com notícias em cache
- **THEN** a fonte DEVE ser montada apenas com o cache local, sem requisição à B3

#### Scenario: Leitura sem rede

- **WHEN** a LLM pede o conteúdo integral de uma notícia
- **THEN** o texto DEVE vir do cache local, sem novo download e sem extração sob demanda

### Requirement: Ramo de notícias na árvore de conhecimento

O sistema DEVE expor as notícias em cache da sub-aba "Notícias" como o ramo `/noticias` da árvore de conhecimento, com o nó `/noticias/grupos` listando os quatro grupos fixos ("Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição" e "Geral") e o nó `/noticias/<grupo>/indice` contendo uma linha por item com a data, o tipo, o título e uma **chave curta estável** (`n<sha1[:10]>`). O índice DEVE conter somente itens recuperáveis — aqueles com resumo ou texto já em cache — e NÃO DEVE listar itens pendentes de extração ou de resumo, que DEVEM ser omitidos em silêncio. A seleção de relevância DEVE ser feita pela própria LLM por navegação (`listar`/`buscar`) sobre o índice, sem filtro determinístico por pergunta e sem confirmação própria de envio.

#### Scenario: Grupos fixos na árvore

- **WHEN** a LLM lista `/noticias/grupos`
- **THEN** os quatro grupos DEVEM ser retornados

#### Scenario: Índice restrito a itens recuperáveis

- **WHEN** o cache de notícias contém itens com resumo ou texto e itens pendentes de processamento
- **THEN** o índice DEVE conter apenas os itens recuperáveis e NÃO DEVE listar os pendentes

#### Scenario: Filtro pela LLM por navegação

- **WHEN** a pergunta menciona um ticker ou uma palavra-chave presente nos títulos
- **THEN** a LLM DEVE usar `buscar` no ramo `/noticias` para selecionar os itens relacionados

#### Scenario: Índice compacto e com chaves

- **WHEN** o índice de um grupo é obtido
- **THEN** cada linha DEVE conter data, tipo, título e chave curta, e NÃO DEVE conter o corpo da notícia

#### Scenario: Cache frio de notícias

- **WHEN** não há notícias em cache
- **THEN** o ramo `/noticias` DEVE existir sem itens, sem erro

### Requirement: Leitura de notícias por nós da árvore

O sistema DEVE expor, para cada notícia recuperável, os nós `/noticias/<grupo>/<chave>/titulo`, `/noticias/<grupo>/<chave>/resumo` e `/noticias/<grupo>/<chave>/texto`, obtidos por navegação. O resumo DEVE ser o longo, com fallback para o curto. Os tetos DEVEM ser em tokens, por nó, sem extrair nem baixar conteúdo sob demanda. Chaves que não correspondam a itens recuperáveis NÃO DEVEM existir como nós.

#### Scenario: Notícia lida por nó

- **WHEN** a LLM obtém `/noticias/<grupo>/<chave>/resumo`
- **THEN** o sistema DEVE devolver o resumo longo em cache da notícia, com fallback para o curto

#### Scenario: Texto integral por nó

- **WHEN** a LLM obtém `/noticias/<grupo>/<chave>/texto`
- **THEN** o sistema DEVE devolver o texto em cache, respeitando o teto em tokens do nó

#### Scenario: Documento vinculado não baixado

- **WHEN** a notícia "Geral" é um apontador cujo documento vinculado (CVM RAD/FNET) ainda não foi baixado
- **THEN** ela NÃO DEVE ser considerada recuperável e os seus nós NÃO DEVEM existir, sem baixar o documento

### Requirement: Integração das notícias como ramo da árvore

O sistema DEVE registrar as notícias como provedor do ramo `/noticias` da árvore de conhecimento exposta pela change `llm-chat-tree`, resolvendo os caminhos dos seus nós nos mesmos tetos e gates das demais fontes. Falha ou ausência de notícias NÃO DEVE impedir a montagem dos demais ramos.

#### Scenario: Ramo registrado

- **WHEN** a aba "Chat AI" monta a árvore
- **THEN** as notícias DEVEM ser expostas como o ramo `/noticias`, ao lado do conhecimento do FlowScope, dos fundamentos e dos documentos

#### Scenario: Falha da fonte de notícias

- **WHEN** a fonte de notícias falha ao resolver um nó
- **THEN** os demais ramos DEVEM permanecer disponíveis e o erro DEVE ser logado
