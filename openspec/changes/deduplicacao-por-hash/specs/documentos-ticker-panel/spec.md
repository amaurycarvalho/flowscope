## MODIFIED Requirements

### Requirement: Estado vazio e atualização

A sub-aba DEVE exibir uma mensagem informativa quando o ticker não tem documentos em cache e DEVE oferecer um controle para atualizar o catálogo. Ao acionar o controle, o sistema DEVE adquirir os documentos do ticker (quando houver aquisição disponível), executar o housekeeping de deduplicação por conteúdo do ticker e remontar a árvore do catálogo.

#### Scenario: Ticker sem documentos
- **WHEN** o ticker selecionado não tem documentos em cache
- **THEN** a sub-aba DEVE exibir mensagem de ausência de documentos

#### Scenario: Atualização manual
- **WHEN** o usuário aciona o controle de atualização
- **THEN** o sistema DEVE adquirir os documentos do ticker (quando disponível), executar o housekeeping de deduplicação por conteúdo e remontar a árvore do ticker

#### Scenario: Deduplicação no Atualizar
- **WHEN** o ticker tem documentos em cache com o mesmo conteúdo, em datas ou raízes diferentes
- **THEN** após o "Atualizar" apenas o registro mais antigo DEVE permanecer na árvore
