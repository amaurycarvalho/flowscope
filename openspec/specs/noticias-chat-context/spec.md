# noticias-chat-context Specification

## Purpose

Disponibiliza o conteúdo das notícias em cache como fonte de contexto da aba de chat "Chat AI", com a relevância por ticker inferida pela LLM. A fonte opera em duas camadas: um índice compacto de todos os itens e a leitura do resumo/texto integral sob demanda pelas chaves.

## Requirements

### Requirement: Índice compacto das notícias no contexto do Chat AI

O sistema DEVE disponibilizar um **índice compacto** dos itens em cache da sub-aba "Notícias" como seção própria do contexto da aba "Chat AI", com uma linha por item contendo a seção, a data, o tipo, o título e uma **chave curta estável**. O índice DEVE cobrir as quatro categorias ("Geral", "Censuras Públicas", "Condições Excepcionais" e "Programas de Aquisição de Ações"), intercalando as seções e ordenando cada uma do mais recente ao mais antigo, de modo que todas apareçam mesmo com orçamento curto. O índice DEVE respeitar um teto de caracteres próprio e DEVE instruir a LLM a pedir as chaves cujo conteúdo integral deseja.

#### Scenario: Índice com todas as categorias
- **WHEN** o contexto do chat inclui notícias em cache das quatro categorias
- **THEN** o índice DEVE conter ao menos uma linha de cada categoria com itens

#### Scenario: Índice compacto e com chaves
- **WHEN** o índice é montado
- **THEN** cada linha DEVE conter seção, data, tipo, título e chave curta, e NÃO DEVE conter o corpo da notícia

#### Scenario: Teto do índice
- **WHEN** o número de itens excede o orçamento do índice
- **THEN** os itens mais recentes de cada categoria DEVEM ser priorizados e o índice DEVE respeitar o teto

#### Scenario: Cache frio de notícias
- **WHEN** não há notícias em cache
- **THEN** o contexto DEVE ser montado sem a seção de notícias, sem erro

### Requirement: Leitura sob demanda do conteúdo integral

O sistema DEVE permitir que a LLM peça, na resposta estruturada, as chaves das notícias cujo conteúdo integral precisa ler. Ao atender às chaves, o sistema DEVE devolver o resumo (longo, com fallback para o curto) e/ou o texto resolvido da notícia, aplicando tetos por item e global. O pedido DEVE somar as chaves dos documentos por ticker e das notícias no mesmo gate de confirmação.

#### Scenario: Notícia lida por chave
- **WHEN** a LLM devolve a chave de uma notícia
- **THEN** o contexto da segunda chamada DEVE conter o resumo e/ou o texto dessa notícia

#### Scenario: Resumo preferido
- **WHEN** a notícia tem resumo longo
- **THEN** o resumo longo DEVE ser entregue

#### Scenario: Soma de documentos e notícias
- **WHEN** a LLM devolve chaves de documentos e de notícias
- **THEN** ambas as origens DEVEM ser resolvidas e somadas na leitura e no gate de confirmação

#### Scenario: Documento vinculado não baixado
- **WHEN** a notícia "Geral" pedida é um apontador cujo documento vinculado (CVM RAD/FNET) ainda não foi baixado
- **THEN** o sistema DEVE sinalizar que o documento não está disponível e NÃO DEVE apresentar a URL como conteúdo

### Requirement: Relevância por ticker inferida pela LLM

O sistema NÃO DEVE exigir um seletor de escopo de ticker. O índice das notícias do período DEVE ser oferecido ao contexto e a LLM DEVE selecionar as relacionadas ao ticker referido na pergunta, inferido a partir dela.

#### Scenario: Pergunta sobre um ticker
- **WHEN** a pergunta menciona um ticker específico
- **THEN** a LLM DEVE pedir as chaves das notícias relacionadas a esse ticker, sem filtro prévio na montagem do contexto

#### Scenario: Pergunta geral de mercado
- **WHEN** a pergunta é sobre o mercado sem um ticker específico
- **THEN** o índice das notícias do período DEVE estar disponível no contexto

### Requirement: Integração com o ponto de extensão do llm-chat

O sistema DEVE registrar as notícias como fonte adicional de contexto por meio do ponto de extensão exposto pela change `llm-chat`, sem alterar a ordem da cascata de documentos. A fonte adicional DEVE expor a resolução de chaves para participar do escalonamento.

#### Scenario: Fonte registrada
- **WHEN** a aba "Chat AI" monta o contexto
- **THEN** as notícias DEVEM ser consideradas uma fonte adicional, ao lado do conhecimento do FlowScope, dos fundamentos e dos documentos

#### Scenario: Fonte sem escalonamento
- **WHEN** uma fonte adicional não expõe resolução de chaves
- **THEN** ela DEVE permanecer apenas textual, sem participar da leitura sob demanda

### Requirement: Leitura somente do cache local

A fonte de notícias do chat NÃO DEVE consultar a B3 ao montar o contexto nem ao ler o conteúdo integral: ela DEVE ler apenas o índice de metadados e o conteúdo em cache local, de modo que uma pergunta não fique presa à indisponibilidade da rede.

#### Scenario: Montagem sem rede
- **WHEN** a aba "Chat AI" monta o contexto com notícias em cache
- **THEN** a fonte DEVE ser montada apenas com o cache local, sem requisição à B3

#### Scenario: Leitura sem rede
- **WHEN** a LLM pede o conteúdo integral de uma notícia
- **THEN** o texto DEVE vir do cache local, sem novo download
