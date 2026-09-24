## Purpose

Lista as notícias do Plantão B3, baixa o corpo de cada artigo e mantém um cache local do conteúdo para exibição e resumo.

## ADDED Requirements

### Requirement: Listagem das notícias

O sistema DEVE listar as notícias do Plantão B3 no período e com o filtro de palavra informados, retornando título, data de publicação, agência e URL. A listagem DEVE tolerar indisponibilidade sem interromper a interface.

#### Scenario: Notícias do período
- **WHEN** a listagem é solicitada para um período com notícias
- **THEN** as notícias DEVEM ser retornadas com título, data, agência e URL

#### Scenario: Falha de listagem
- **WHEN** a listagem falha por indisponibilidade de rede
- **THEN** uma lista vazia DEVE ser retornada sem erro fatal

### Requirement: Aquisição do corpo do artigo

O sistema DEVE baixar o corpo de cada notícia a partir da sua URL e gravá-lo em cache, tolerando falha por item (artigo sem URL, sem conteúdo ou erro de rede) sem interromper os demais. A aquisição DEVE reportar progresso e respeitar cancelamento.

#### Scenario: Artigo baixado
- **WHEN** uma notícia tem URL acessível
- **THEN** o corpo do artigo DEVE ser baixado e gravado no cache

#### Scenario: Falha em um artigo
- **WHEN** o download de um artigo falha
- **THEN** os demais artigos DEVEM continuar e o erro DEVE ser registrado no log

#### Scenario: Notícia sem URL
- **WHEN** uma notícia não tem URL
- **THEN** ela DEVE ser ignorada na aquisição, sem erro

### Requirement: Cache das notícias

O sistema DEVE manter um cache próprio do HTML das notícias, independente do cache de listagem, com uma chave estável derivada de URL ou, na ausência desta, de data, agência e título. O cache NÃO DEVE ser sobrescrito quando já existir conteúdo para a mesma chave.

#### Scenario: Reexecução sem rebaixar
- **WHEN** a aquisição é executada novamente para a mesma notícia já em cache
- **THEN** o corpo já cacheado NÃO DEVE ser baixado de novo

#### Scenario: Chave estável sem URL
- **WHEN** a notícia não tem URL
- **THEN** a chave DEVE ser derivada de data, agência e título
