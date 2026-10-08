## MODIFIED Requirements

### Requirement: Documento vinculado sob demanda

Quando o corpo de uma notícia "Geral" for apenas um apontador para um documento, o sistema DEVE baixar e extrair o conteúdo vinculado ao selecionar a notícia e ao processar "Resumir pendentes". As URLs suportadas incluem o **visualizador da CVM RAD** (`rad.cvm.gov.br`) e o **visualizador do FNET** (`fnet.bmfbovespa.com.br`). O texto do documento extraído DEVE substituir o apontador no corpo e ser persistido no cache de textos, evitando novo download. Se o download não puder ser concluído (captcha habilitado, falha de rede ou formato inesperado), o corpo original DEVE ser mantido, sem erro.

Quando o documento vinculado for um PDF protegido por senha que não abre com senha vazia, o sistema DEVE solicitar a senha ao usuário no preview interativo, na thread da interface, e tentar novamente a extração com a senha informada, fora da thread da interface. A solicitação DEVE ser limitada a 3 tentativas por notícia/seleção (parametrizável), avisando sobre a senha incorreta e parando ao esgotar o limite. O texto obtido DEVE ser persistido no cache de textos e a senha NÃO DEVE ser persistida. Cancelar a solicitação DEVE manter o corpo original, sem erro. A solicitação DEVE ocorrer apenas no fluxo interativo; o resumo em lote NÃO DEVE abrir diálogo de senha.

Quando a extração do documento vinculado resultar parcial (ao menos uma página não extraída), a pré-visualização DEVE anotar a quantidade de páginas não extraídas antes do conteúdo. O texto parcial NÃO DEVE ser persistido no cache de textos nem usado para gerar resumo, de modo que a notícia permaneça pendente. A extração parcial DEVE ser retentada automaticamente quando a notícia for selecionada ou clicada novamente e quando "Resumir pendentes" for acionado, sem controle dedicado de "Tentar novamente".

#### Scenario: Pré-visualização resolve o documento vinculado da CVM
- **WHEN** uma notícia "Geral" com URL do visualizador da CVM RAD é selecionada
- **THEN** o conteúdo vinculado DEVE ser baixado, extraído e exibido no corpo

#### Scenario: Pré-visualização resolve o documento vinculado do FNET
- **WHEN** uma notícia "Geral" com URL do visualizador do FNET é selecionada
- **THEN** o PDF apontado pelo `iframe` do visualizador DEVE ser baixado, extraído e exibido no corpo

#### Scenario: Documento vinculado protegido solicita senha
- **WHEN** o documento vinculado é um PDF protegido cujo texto não foi extraído com senha vazia
- **THEN** o sistema DEVE abrir uma caixa de diálogo solicitando a senha

#### Scenario: Senha correta extrai e cacheia
- **WHEN** o usuário informa a senha correta do documento vinculado protegido
- **THEN** o sistema DEVE extrair o texto, persistí-lo no cache e exibi-lo no corpo

#### Scenario: Senha incorreta permite nova tentativa
- **WHEN** o usuário informa uma senha incorreta e ainda há tentativas disponíveis
- **THEN** o sistema DEVE informar a falha e permitir nova tentativa ou cancelamento

#### Scenario: Limite de tentativas atingido
- **WHEN** o usuário esgota as 3 tentativas de senha do documento vinculado
- **THEN** o sistema DEVE parar de solicitar a senha e manter o corpo original, sem erro

#### Scenario: Cancelamento mantém o corpo original
- **WHEN** o usuário cancela a solicitação de senha
- **THEN** o sistema DEVE manter o corpo original da notícia, sem erro

#### Scenario: Extração parcial é anotada
- **WHEN** a extração do documento vinculado resulta parcial
- **THEN** a pré-visualização DEVE anotar as páginas não extraídas antes do conteúdo

#### Scenario: Selecionar novamente retenta o documento vinculado
- **WHEN** o documento vinculado foi extraído parcialmente e o usuário seleciona ou clica na notícia novamente
- **THEN** o sistema DEVE refazer o download e a extração do documento vinculado, sem exigir controle dedicado

#### Scenario: Resumir pendentes retenta o documento vinculado
- **WHEN** o documento vinculado de uma notícia foi extraído parcialmente e o usuário aciona "Resumir pendentes"
- **THEN** o sistema DEVE refazer o download e a extração e, se completa, gerar o resumo; se ainda parcial, manter a notícia pendente

#### Scenario: Extração parcial não gera resumo
- **WHEN** o documento vinculado de uma notícia é extraído parcialmente
- **THEN** nenhum resumo DEVE ser gerado e a notícia DEVE permanecer pendente

#### Scenario: Resumo em lote usa o documento vinculado
- **WHEN** "Resumir pendentes" processa uma notícia "Geral" com documento vinculado
- **THEN** o resumo DEVE ser gerado a partir do conteúdo vinculado

#### Scenario: Cache evita novo download
- **WHEN** a notícia é reaberta após o documento vinculado já ter sido resolvido
- **THEN** o texto do cache DEVE ser reutilizado, sem novo download

#### Scenario: Captcha ou falha mantém o corpo
- **WHEN** o documento vinculado exige captcha, falha a rede ou vem em formato inesperado
- **THEN** a notícia DEVE exibir o corpo original, sem erro

#### Scenario: Apontador não resolvido é reprocessado
- **WHEN** o texto cacheado de uma notícia "Geral" é idêntico ao apontador atual (download anterior não concluído)
- **THEN** o download DEVE ser tentado novamente na próxima seleção ou em "Resumir pendentes"

#### Scenario: Apontador não resolvido não gera resumo
- **WHEN** "Resumir pendentes" processa uma notícia "Geral" cujo documento vinculado não pôde ser baixado
- **THEN** nenhum resumo DEVE ser gerado para ela e o item DEVE permanecer pendente para nova tentativa

#### Scenario: Lote não solicita senha
- **WHEN** o resumo em lote processa uma notícia cujo documento vinculado é protegido
- **THEN** o sistema NÃO DEVE abrir diálogo de senha e DEVE manter a notícia pendente
