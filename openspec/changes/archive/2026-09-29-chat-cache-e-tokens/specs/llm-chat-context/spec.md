## MODIFIED Requirements

### Requirement: Cascata de recuperação de documentos

O sistema DEVE recuperar o contexto documental em cascata sobre os caches mantidos pela sub-aba "Documentos", sem gerar nem extrair conteúdo durante o chat. A primeira camada DEVE conter os resumos cacheados (curto e longo) dos documentos do escopo; a segunda, quando a LLM devolver as chaves dos alvos, o texto integral dos documentos-alvo já extraído e em cache. Documentos pendentes de resumo ou de extração NÃO DEVEM ser preparados, resumidos, extraídos nem citados: eles DEVEM ser omitidos do contexto em silêncio. Quando não houver resumo nem texto em cache, o sistema DEVE montar o contexto sem a seção documental, sem erro e sem executar chamadas de completion adicionais para prepará-la. O escopo documental DEVE ser a watchlist completa e a LLM DEVE selecionar os documentos-alvo, por chave, a partir da pergunta.

#### Scenario: Resposta a partir dos resumos

- **WHEN** há resumos cacheados no escopo e eles bastam para responder
- **THEN** o sistema NÃO DEVE ler o texto integral, NÃO DEVE gerar resumos e DEVE devolver a resposta

#### Scenario: Escalada para o texto integral

- **WHEN** os resumos cacheados não bastam e a LLM devolve chaves de documentos-alvo
- **THEN** o sistema DEVE usar o texto integral desses alvos do cache, sem extraí-lo sob demanda

#### Scenario: Cache frio

- **WHEN** nenhum documento do escopo tem resumo ou texto em cache
- **THEN** o contexto DEVE ser montado sem a seção documental, sem erro e sem chamadas de completion para prepará-la

#### Scenario: Documento pendente é omitido em silêncio

- **WHEN** um documento do escopo não tem resumo nem texto em cache
- **THEN** ele NÃO DEVE aparecer no contexto, NÃO DEVE ser resumido nem extraído e NÃO DEVE ser citado na resposta

#### Scenario: Escopo único

- **WHEN** a pergunta é feita na aba "Chat AI"
- **THEN** o escopo documental DEVE ser a watchlist completa

#### Scenario: Seleção do ticker inferido

- **WHEN** a pergunta se refere a um ticker específico
- **THEN** a LLM DEVE indicar os documentos-alvo desse ticker pelas suas chaves
