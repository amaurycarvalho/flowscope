## MODIFIED Requirements

### Requirement: Carga inicial somente do cache local

A sub-aba DEVE montar a árvore e a pré-visualização lendo apenas o cache local (índice de metadados, HTML, textos e resumos), sem consultar a B3 ao ser aberta ou ao trocar de aba. A listagem e a aquisição de novos itens DEVEM ocorrer somente pelo botão "Atualizar", em segundo plano, que DEVE também executar o housekeeping de deduplicação por conteúdo das notícias. A ausência de cache ou de índice DEVE resultar em estado vazio, sem erro, e entradas do índice sem HTML correspondente NÃO DEVEM aparecer.

#### Scenario: Abertura sem consultar a B3
- **WHEN** a sub-aba "Notícias" é aberta
- **THEN** a árvore DEVE ser montada apenas com o cache local, sem requisição à B3

#### Scenario: Cache local com itens indexados
- **WHEN** há itens no índice e o HTML correspondente em cache
- **THEN** a árvore DEVE exibi-los sem depender de rede

#### Scenario: Cache frio
- **WHEN** não há índice nem itens em cache
- **THEN** a sub-aba DEVE exibir o estado vazio, sem erro

#### Scenario: Entrada de índice sem HTML
- **WHEN** o índice referencia um HTML que não existe
- **THEN** o item NÃO DEVE ser exibido na árvore

#### Scenario: Atualizar reconstrói a partir da B3
- **WHEN** o usuário aciona "Atualizar"
- **THEN** a aquisição DEVE rodar em segundo plano, gravar o cache e o índice, o housekeeping de deduplicação DEVE ser executado e a árvore DEVE ser remontada a partir do cache local

#### Scenario: Deduplicação no Atualizar
- **WHEN** há notícias em cache com o mesmo conteúdo em datas ou URLs diferentes
- **THEN** após o "Atualizar" apenas o registro mais antigo DEVE permanecer na árvore
