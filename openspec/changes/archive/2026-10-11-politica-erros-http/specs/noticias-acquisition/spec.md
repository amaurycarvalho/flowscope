## MODIFIED Requirements

### Requirement: Aquisição das fontes regulatórias

O sistema DEVE carregar as censuras públicas, as condições excepcionais e os programas de aquisição de ações por meio do `RegulacaoRepository` e tolerar a indisponibilidade de cada fonte sem interromper as demais nem a categoria "Geral". As requisições dessas fontes DEVEM usar a política central de status HTTP (`politica-erros-http`). A leitura dos programas DEVE declarar um override de ponto de chamada que trata o 404 como repetível, pois o endpoint responde 404 de forma intermitente; fora desse override, o 404 permanece permanente.

#### Scenario: Fontes carregadas
- **WHEN** as páginas e o endpoint das fontes regulatórias estão acessíveis
- **THEN** censuras, condições excepcionais e programas DEVEM ser convertidos em itens da sub-aba

#### Scenario: Falha de uma fonte
- **WHEN** uma das fontes regulatórias falha
- **THEN** as demais fontes e a categoria "Geral" DEVEM continuar

#### Scenario: Retry dos programas
- **WHEN** o endpoint de programas responde 404 numa tentativa e o ponto de chamada declara o override de 404
- **THEN** a leitura DEVE tentar novamente antes de desistir

#### Scenario: Erro transitório das páginas é repetido
- **WHEN** a requisição de uma página de censuras ou condições falha com 502 ou 504
- **THEN** o sistema DEVE repetir conforme a política central antes de desistir

### Requirement: Aquisição do corpo do item

O sistema DEVE baixar o corpo de cada notícia a partir da sua URL quando ela existir e, quando NÃO houver URL, usar o próprio item como conteúdo. O download do corpo DEVEM usar a política central de status HTTP, repetindo `THROTTLE`, `TRANSITORIO` e `GATEWAY` e não repetindo `PERMANENTE`. A aquisição DEVE tolerar falha por item (sem conteúdo ou erro de rede) sem interromper os demais, reportar progresso e respeitar cancelamento.

#### Scenario: Item com URL baixado
- **WHEN** uma notícia do Plantão B3 tem URL acessível
- **THEN** o corpo do artigo DEVE ser baixado e gravado no cache

#### Scenario: Item sem URL usa o próprio conteúdo
- **WHEN** uma censura, condição excepcional ou programa de aquisição não tem URL
- **THEN** o próprio item DEVE ser gravado como conteúdo no cache

#### Scenario: Falha em um item
- **WHEN** o download de um artigo falha
- **THEN** os demais itens DEVEM continuar e o erro DEVE ser registrado no log

#### Scenario: Notícia do Plantão sem URL
- **WHEN** uma notícia do Plantão B3 não tem URL
- **THEN** ela DEVE ser ignorada na aquisição, sem erro

#### Scenario: Erro transitório do corpo é repetido
- **WHEN** o download do corpo de uma notícia falha com 502 e a tentativa seguinte sucede
- **THEN** o corpo DEVE ser gravado sem propagar a falha
