## MODIFIED Requirements

### Requirement: Sub-aba "Notícias" na Análise Geral

O sistema DEVE expor a sub-aba "Notícias" na "Análise Geral", organizando os itens em uma árvore e exibindo o conteúdo do item selecionado em um campo de texto. A árvore DEVE ter a raiz "Notícias" e, abaixo dela, as categorias de topo "Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição de Ações" e, por último, "Geral", cada uma seguindo a sub-estrutura ano → mês → categoria → item. A sub-aba DEVE oferecer os botões "Atualizar", "Abrir", um combobox de modelo ativo com a opção `None`, um botão de configuração com o ícone `ai-properties.png` e "Resumir pendentes", com barra de progresso durante a aquisição. O botão "I.A." textual NÃO DEVE mais existir. Trocar o item do combobox DEVE persistir imediatamente o novo provedor ativo e reavaliar o estado dos resumos; o combobox e o botão de configuração DEVEM ser desabilitados durante processamentos, junto com os demais controles.

#### Scenario: Árvore e pré-visualização

- **WHEN** a sub-aba "Notícias" é exibida com itens em cache
- **THEN** a árvore DEVE listar as categorias de topo com itens e a seleção DEVE exibir o texto do item

#### Scenario: "Geral" por último

- **WHEN** a árvore lista as categorias de topo com itens
- **THEN** a categoria "Geral" DEVE aparecer depois das categorias regulatórias

#### Scenario: Seleção da raiz

- **WHEN** o nó raiz "Notícias" é selecionado
- **THEN** a pré-visualização DEVE exibir a lista de todas as categorias com itens

#### Scenario: Árvore expandida só até o primeiro nível

- **WHEN** a árvore de notícias é carregada (inicialmente ou após "Atualizar")
- **THEN** a raiz DEVE estar expandida e as categorias de topo, os anos, os meses, os tipos e os itens DEVEM estar recolhidos

#### Scenario: Tipo de notícia no 3º nível da "Geral"

- **WHEN** os itens da categoria "Geral" são exibidos
- **THEN** o nível de categoria DEVE ser o tipo típico da notícia (ano → mês → tipo → item), e não a agência

#### Scenario: Tipo "Outros" para títulos não classificados

- **WHEN** um título da "Geral" não corresponde a nenhum tipo típico da whitelist
- **THEN** ele DEVE ser agrupado em "Outros"

#### Scenario: Tipos específicos por fonte nas demais seções

- **WHEN** os itens de uma seção regulatória são exibidos
- **THEN** o nível de categoria DEVE ser o ticker/emissor em censuras, o segmento em condições e a empresa em programas

#### Scenario: Atualização com progresso

- **WHEN** o usuário aciona "Atualizar"
- **THEN** a aquisição DEVE rodar em segundo plano com progresso e reexibir a árvore ao concluir

#### Scenario: Cancelamento reflete a carga parcial

- **WHEN** o usuário cancela a aquisição
- **THEN** a árvore DEVE ser remontada com os itens já persistidos assim que o worker encerrar, sem sobrescrever uma carga iniciada depois

#### Scenario: Sem itens

- **WHEN** não há itens para nenhuma categoria
- **THEN** a sub-aba DEVE exibir um estado vazio, sem erro

#### Scenario: Seletor de modelo e botão de configuração na barra

- **WHEN** a sub-aba "Notícias" é exibida
- **THEN** o combobox de modelo ativo e o botão de configuração com ícone DEVEM estar visíveis na barra de controles, no lugar antes ocupado pelo botão "I.A."

#### Scenario: Troca de modelo pelo combobox

- **WHEN** o usuário seleciona um provedor ativo no combobox
- **THEN** o provedor ativo DEVE ser persistido e o estado do botão "Resumir pendentes" DEVE ser reavaliado
