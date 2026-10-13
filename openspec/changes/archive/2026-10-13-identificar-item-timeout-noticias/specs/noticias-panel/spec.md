## ADDED Requirements

### Requirement: Limite de tempo da resolução do documento vinculado

O tempo total da resolução do documento vinculado de uma notícia "Geral" — as requisições ao visualizador (GET/POST, com as retentativas) e a extração de texto do PDF baixado — DEVE ser limitado pelo mesmo orçamento de extração por item aplicado à notícia, de modo que a duração de cada item permaneça abaixo do limite de inatividade do job. Ao esgotar o orçamento, o sistema DEVE interromper a resolução, manter o corpo original da notícia, deixá-la pendente para nova tentativa e registrar o evento no log nomeando a notícia. Esgotar o orçamento NÃO DEVE propagar exceção nem encerrar o lote.

#### Scenario: Resolução dentro do orçamento

- **WHEN** a resolução do documento vinculado (rede + extração do PDF) conclui dentro do orçamento de extração por item
- **THEN** o conteúdo vinculado DEVE ser usado no corpo da notícia, como hoje

#### Scenario: Orçamento esgotado mantém a notícia pendente

- **WHEN** a resolução do documento vinculado excede o orçamento de extração por item
- **THEN** a notícia DEVE manter o corpo original, NÃO DEVE gerar resumo e DEVE permanecer pendente para nova tentativa

#### Scenario: Orçamento esgotado é registrado nomeando a notícia

- **WHEN** a resolução do documento vinculado de uma notícia excede o orçamento de extração por item
- **THEN** o evento DEVE ser registrado no log identificando a notícia afetada

#### Scenario: Orçamento esgotado não interrompe o lote

- **WHEN** "Resumir pendentes" processa uma notícia cujo documento vinculado esgota o orçamento
- **THEN** o lote DEVE prosseguir para os demais itens, sem propagar exceção

#### Scenario: Orçamento maior no reprocessamento

- **WHEN** o usuário confirma o reprocessamento após um encerramento por timeout e o orçamento corrente foi escalado
- **THEN** a resolução do documento vinculado DEVE respeitar o orçamento vigente, mais folgado

## MODIFIED Requirements

### Requirement: Contrato do resolvedor de documento vinculado injetado

O resolvedor de documento vinculado injetado no painel de notícias DEVE aceitar, na mesma chamada, o texto do apontador, a senha opcional e um orçamento opcional de tempo total. Uma incompatibilidade entre a assinatura do resolvedor e a forma como o painel o invoca NÃO DEVE propagar exceção: a notícia DEVE continuar sendo exibida e processada a partir do corpo original, e o lote DEVE manter o item pendente para nova tentativa. O resolvedor usado em produção (`baixar_conteudo_vinculado`) DEVE ser compatível com esse contrato e DEVE respeitar o orçamento de tempo total informado, assim como a senha.

#### Scenario: Resolvedor de produção resolve o vínculo sem erro de assinatura

- **WHEN** o painel usa o resolvedor de produção com uma notícia "Geral" cujo corpo aponta para uma URL suportada (CVM RAD ou FNET)
- **THEN** o download e a extração do conteúdo vinculado DEVEM ocorrer sem `TypeError`, e o conteúdo vinculado DEVE ser exibido no corpo

#### Scenario: Senha posicional é aceita pelo resolvedor

- **WHEN** o resolvedor de produção é chamado com o texto do apontador e uma senha como segundo argumento posicional
- **THEN** a chamada NÃO DEVE falhar por incompatibilidade de assinatura

#### Scenario: Orçamento de tempo total é aceito pelo resolvedor

- **WHEN** o painel invoca o resolvedor informando o orçamento de tempo total
- **THEN** a chamada NÃO DEVE falhar por incompatibilidade de assinatura e o orçamento DEVE limitar a duração da resolução

#### Scenario: Falha do resolvedor não interrompe o painel

- **WHEN** o resolvedor injetado levanta exceção ao tentar baixar o documento vinculado
- **THEN** a notícia DEVE exibir o corpo original e o processamento em lote NÃO DEVE abortar
