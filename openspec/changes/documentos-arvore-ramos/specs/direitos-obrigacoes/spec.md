## Purpose

Reservam lugar, na árvore da sub-aba "Documentos" e na árvore de conhecimento da aba "Chat AI", para os direitos (ativos) e as obrigações (passivos) de um ticker, que serão preenchidos por changes futuras.

## ADDED Requirements

### Requirement: Ramos placeholder de Direitos e Obrigações

A sub-aba "Documentos" DEVE exibir, sob o ticker, o ramo "Direitos e obrigações" com os sub-ramos "Direitos" (relacionado a ativos) e "Obrigações" (relacionado a passivos). A árvore de conhecimento do chat DEVE expor o ramo `/direitos-obrigacoes` com os nós `/direitos-obrigacoes/direitos` e `/direitos-obrigacoes/obrigacoes`. Ambos DEVEM existir vazios, sem dados, e ser preenchidos por changes futuras; DEVEM ser navegáveis sem erro e sinalizar explicitamente a ausência de dados.

#### Scenario: Ramo visível na árvore de documentos
- **WHEN** o usuário exibe a árvore de um ticker
- **THEN** o ramo "Direitos e obrigações" DEVE estar visível com os sub-ramos "Direitos" e "Obrigações"

#### Scenario: Sub-ramos vazios na árvore de documentos
- **WHEN** o usuário seleciona "Direitos" ou "Obrigações"
- **THEN** o campo de texto DEVE exibir a indicação de que não há dados, sem erro

#### Scenario: Navegação do ramo no chat
- **WHEN** a LLM lista `/direitos-obrigacoes`
- **THEN** o sistema DEVE devolver os nós `direitos` e `obrigacoes`

#### Scenario: Nós vazios são navegáveis no chat
- **WHEN** a LLM obtém `/direitos-obrigacoes/direitos` ou `/direitos-obrigacoes/obrigacoes`
- **THEN** o sistema DEVE devolver a indicação de ausência de dados, sem erro

#### Scenario: Estrutura preservada para changes futuras
- **WHEN** uma change futura preencher Direitos ou Obrigações com dados
- **THEN** o ramo DEVE permanecer com o mesmo caminho canônico, recebendo os novos itens como filhos
