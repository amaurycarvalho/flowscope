## MODIFIED Requirements

### Requirement: Índice compacto das notícias no contexto do Chat AI

O sistema DEVE disponibilizar um **índice compacto** dos itens em cache da sub-aba "Notícias" como seção própria do contexto da aba "Chat AI", com uma linha por item contendo a seção, a data, o tipo, o título e uma **chave curta estável**. O índice DEVE conter somente itens recuperáveis — aqueles com resumo ou texto já em cache — e NÃO DEVE listar itens pendentes de extração ou de resumo, que DEVEM ser omitidos em silêncio. Antes de montar o índice, o sistema DEVE aplicar um filtro determinístico por expressão regular, extraindo da pergunta termos como tickers e palavras-chave e casando-os com o título e os metadados dos itens. O índice DEVE cobrir as quatro categorias ("Geral", "Censuras Públicas", "Condições Excepcionais" e "Programas de Aquisição de Ações"), intercalando as seções e ordenando cada uma do mais recente ao mais antigo, de modo que todas apareçam mesmo com orçamento curto. O índice DEVE respeitar um teto de caracteres próprio e DEVE instruir a LLM a pedir as chaves cujo conteúdo integral deseja. Quando o índice filtrado exceder um limite de envio automático, o sistema DEVE pedir confirmação ao usuário antes de incluí-lo; abaixo do limite, DEVE incluí-lo sem confirmação. Quando o filtro não casar nenhum item, a seção de notícias NÃO DEVE ser incluída.

#### Scenario: Índice com todas as categorias

- **WHEN** o contexto do chat inclui notícias em cache das quatro categorias
- **THEN** o índice DEVE conter ao menos uma linha de cada categoria com itens

#### Scenario: Índice restrito a itens recuperáveis

- **WHEN** o cache de notícias contém itens com resumo ou texto e itens pendentes de processamento
- **THEN** o índice DEVE conter apenas os itens recuperáveis e NÃO DEVE listar os pendentes

#### Scenario: Filtro determinístico pela pergunta

- **WHEN** a pergunta menciona um ticker ou uma palavra-chave presente nos títulos
- **THEN** o índice DEVE conter apenas os itens cujo título ou metadados casam com o termo extraído

#### Scenario: Sem casamento omite a seção

- **WHEN** o filtro determinístico não casa nenhum item
- **THEN** a seção de notícias NÃO DEVE ser incluída no contexto

#### Scenario: Envio automático abaixo do limite

- **WHEN** o índice filtrado não excede o limite de envio automático
- **THEN** ele DEVE ser incluído sem confirmação do usuário

#### Scenario: Confirmação acima do limite

- **WHEN** o índice filtrado excede o limite de envio automático
- **THEN** o sistema DEVE pedir confirmação ao usuário antes de incluí-lo e, sem confirmação, NÃO DEVE incluí-lo

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

O sistema DEVE permitir que a LLM peça, na resposta estruturada, as chaves das notícias cujo conteúdo integral precisa ler. Ao atender às chaves, o sistema DEVE devolver o resumo (longo, com fallback para o curto) e/ou o texto já resolvido e em cache, aplicando tetos por item e global, sem extrair nem baixar conteúdo sob demanda. O pedido DEVE somar as chaves dos documentos por ticker e das notícias no mesmo gate de confirmação. Chaves que não correspondam a itens recuperáveis NÃO DEVEM ser extraídas nem sinalizadas.

#### Scenario: Notícia lida por chave

- **WHEN** a LLM devolve a chave de uma notícia recuperável
- **THEN** o contexto da segunda chamada DEVE conter o resumo e/ou o texto em cache dessa notícia

#### Scenario: Resumo preferido

- **WHEN** a notícia tem resumo longo em cache
- **THEN** o resumo longo DEVE ser entregue

#### Scenario: Soma de documentos e notícias

- **WHEN** a LLM devolve chaves de documentos e de notícias
- **THEN** ambas as origens DEVEM ser resolvidas e somadas na leitura e no gate de confirmação

#### Scenario: Documento vinculado não baixado

- **WHEN** a notícia "Geral" pedida é um apontador cujo documento vinculado (CVM RAD/FNET) ainda não foi baixado
- **THEN** ela NÃO DEVE ser considerada recuperável e DEVE ser omitida em silêncio, sem baixar o documento e sem apresentar a URL como conteúdo

### Requirement: Relevância por ticker inferida pela LLM

O sistema NÃO DEVE exigir um seletor de escopo de ticker. O índice filtrado DEVE ser oferecido ao contexto e a LLM DEVE selecionar as notícias relacionadas ao ticker referido na pergunta, inferido a partir dela.

#### Scenario: Pergunta sobre um ticker

- **WHEN** a pergunta menciona um ticker específico
- **THEN** o índice DEVE ser filtrado por esse termo e a LLM DEVE pedir as chaves das notícias relacionadas a ele

#### Scenario: Pergunta geral de mercado

- **WHEN** a pergunta é sobre o mercado sem um ticker específico
- **THEN** o índice DEVE conter apenas os itens que casem com os termos extraídos da pergunta e a LLM DEVE selecionar os relacionados entre eles

### Requirement: Leitura somente do cache local

A fonte de notícias do chat NÃO DEVE consultar a B3 nem extrair ou gerar conteúdo: ela DEVE ler apenas o índice de metadados e o conteúdo já em cache local, tanto ao montar o contexto quanto ao ler o conteúdo integral das chaves, de modo que uma pergunta não fique presa à indisponibilidade da rede nem a processamentos não solicitados.

#### Scenario: Montagem sem rede

- **WHEN** a aba "Chat AI" monta o contexto com notícias em cache
- **THEN** a fonte DEVE ser montada apenas com o cache local, sem requisição à B3

#### Scenario: Leitura sem rede

- **WHEN** a LLM pede o conteúdo integral de uma notícia
- **THEN** o texto DEVE vir do cache local, sem novo download e sem extração sob demanda
