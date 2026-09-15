## ADDED Requirements

### Requirement: Sub-aba Evolução dos Fundamentos

A aba "Análise do Ticker" DEVE conter a sub-aba "Evolução dos Fundamentos", ativa e selecionável, exibindo o painel de evolução dos fundamentos do ticker selecionado no lugar de um placeholder de texto.

#### Scenario: Sub-aba disponível na Análise do Ticker

- **WHEN** o usuário navega para a aba "Análise do Ticker"
- **THEN** a sub-aba "Evolução dos Fundamentos" DEVE estar ativa e selecionável

#### Scenario: Painel exibido na sub-aba

- **WHEN** o usuário seleciona a sub-aba "Evolução dos Fundamentos"
- **THEN** o sistema DEVE exibir o painel de evolução dos fundamentos, e não um placeholder de texto

### Requirement: Duplo clique na tabela de Fundamentos ativa a evolução

O sistema DEVE reagir ao duplo clique em uma linha da tabela da sub-aba "Fundamentos" (aba "Análise Geral"), usando o ticker da linha como o ticker da sub-aba "Evolução dos Fundamentos" e tornando essa sub-aba ativa.

#### Scenario: Duplo clique seleciona ticker e troca de sub-aba

- **WHEN** o usuário dá duplo clique em uma linha da tabela de "Fundamentos"
- **THEN** o sistema DEVE usar o ticker daquela linha na sub-aba "Evolução dos Fundamentos" e selecioná-la na aba "Análise do Ticker"

#### Scenario: Ticker do duplo clique prevalece

- **WHEN** o duplo clique é feito em uma linha cujo ticker difere do ticker selecionado na lista de tickers
- **THEN** o painel de evolução DEVE ser preenchido com o ticker da linha clicada

#### Scenario: Duplo clique sem histórico

- **WHEN** o ticker da linha clicada não possui observações no cache histórico
- **THEN** a sub-aba DEVE se tornar ativa exibindo o estado vazio, sem erro

### Requirement: Preenchimento preguiçoso e independente da carga B3

A sub-aba "Evolução dos Fundamentos" DEVE ser preenchida somente quando selecionada e DEVE funcionar apenas com o cache histórico, mesmo quando não houver dados da B3 carregados na sessão corrente.

#### Scenario: Preenchimento ao selecionar a sub-aba

- **WHEN** o usuário seleciona a sub-aba "Evolução dos Fundamentos"
- **THEN** o sistema DEVE montar e exibir a evolução naquele momento

#### Scenario: Sem dados B3 carregados

- **WHEN** não há dados da B3 carregados e o ticker possui observações no cache histórico
- **THEN** o sistema DEVE exibir a evolução normalmente, sem depender de dados da B3

#### Scenario: Sem preenchimento fora da sub-aba

- **WHEN** a sub-aba ativa não é "Evolução dos Fundamentos"
- **THEN** o sistema NÃO DEVE montar o painel de evolução

### Requirement: OrientationPanel da sub-aba Evolução dos Fundamentos

O OrientationPanel DEVE exibir conteúdo explicativo da sub-aba "Evolução dos Fundamentos", composto por objetivo, pergunta respondida, indicadores envolvidos e como interpretar, no mesmo padrão das demais sub-abas.

#### Scenario: Conteúdo explicativo ao selecionar a sub-aba

- **WHEN** o usuário seleciona a sub-aba "Evolução dos Fundamentos"
- **THEN** o OrientationPanel DEVE exibir o título e o texto explicativo da sub-aba, com as seções no padrão existente
