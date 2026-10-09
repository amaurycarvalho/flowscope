## ADDED Requirements

### Requirement: Contrato do resolvedor de documento vinculado injetado

O resolvedor de documento vinculado injetado no painel de notícias DEVE aceitar, na mesma chamada, o texto do apontador e a senha opcional. Uma incompatibilidade entre a assinatura do resolvedor e a forma como o painel o invoca NÃO DEVE propagar exceção: a notícia DEVE continuar sendo exibida e processada a partir do corpo original, e o lote DEVE manter o item pendente para nova tentativa. O resolvedor usado em produção (`baixar_conteudo_vinculado`) DEVE ser compatível com esse contrato.

#### Scenario: Resolvedor de produção resolve o vínculo sem erro de assinatura

- **WHEN** o painel usa o resolvedor de produção com uma notícia "Geral" cujo corpo aponta para uma URL suportada (CVM RAD ou FNET)
- **THEN** o download e a extração do conteúdo vinculado DEVEM ocorrer sem `TypeError`, e o conteúdo vinculado DEVE ser exibido no corpo

#### Scenario: Senha posicional é aceita pelo resolvedor

- **WHEN** o resolvedor de produção é chamado com o texto do apontador e uma senha como segundo argumento posicional
- **THEN** a chamada NÃO DEVE falhar por incompatibilidade de assinatura

#### Scenario: Falha do resolvedor não interrompe o painel

- **WHEN** o resolvedor injetado levanta exceção ao tentar baixar o documento vinculado
- **THEN** a notícia DEVE exibir o corpo original e o processamento em lote NÃO DEVE abortar
