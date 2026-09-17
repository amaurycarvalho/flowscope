## Purpose

Disponibilizar uma sub-aba na "Análise do Ticker" para navegar, pré-visualizar e abrir os documentos em cache relacionados ao ticker selecionado.

## ADDED Requirements

### Requirement: Sub-aba "Documentos" na Análise do Ticker

O sistema DEVE adicionar a sub-aba "Documentos" à "Análise do Ticker". Ao se tornar ativa, a sub-aba DEVE carregar o catálogo de documentos do ticker selecionado e exibir a árvore correspondente.

#### Scenario: Sub-aba disponível
- **WHEN** o usuário navega para a "Análise do Ticker"
- **THEN** a sub-aba "Documentos" DEVE estar disponível

#### Scenario: Ativação carrega o catálogo
- **WHEN** a sub-aba "Documentos" se torna ativa para o ticker selecionado
- **THEN** a árvore DEVE ser montada a partir do catálogo do ticker

### Requirement: Árvore hierárquica de documentos

A sub-aba DEVE exibir uma árvore com o nome do ticker no topo e, abaixo, os níveis de ano, mês e categoria, e por fim os arquivos. Pastas DEVEM expandir e recolher; somente arquivos DEVEM abrir.

#### Scenario: Estrutura da árvore
- **WHEN** o catálogo do ticker contém documentos em `2026/02/aviso-aos-acionistas`
- **THEN** a árvore DEVE exibir o ticker, o ano, o mês, a categoria e os arquivos nessa ordem

#### Scenario: Duplo-clique em pasta
- **WHEN** o usuário dá duplo-clique em um nó de pasta
- **THEN** a pasta DEVE expandir ou recolher, sem abrir arquivo

### Requirement: Pré-visualização textual

Ao selecionar um arquivo, o sistema DEVE exibir uma pré-visualização textual em caixa de texto somente-leitura ao lado da árvore. Para arquivos HTML, o texto DEVE ser derivado do HTML; para PDFs, o texto DEVE ser extraído com `pypdf`. A extração DEVE ocorrer fora da thread da interface, com estado de carregamento, e DEVE resultar em mensagem informativa quando não houver texto extraível.

#### Scenario: Seleção de PDF
- **WHEN** o usuário seleciona um arquivo PDF
- **THEN** o sistema DEVE exibir o texto extraído do PDF na caixa somente-leitura

#### Scenario: Seleção de HTML
- **WHEN** o usuário seleciona um arquivo HTML
- **THEN** o sistema DEVE exibir o texto derivado do HTML na caixa somente-leitura

#### Scenario: Extração sem texto
- **WHEN** o arquivo não tem texto extraível
- **THEN** o sistema DEVE exibir uma mensagem informativa, sem erro

### Requirement: Abertura no aplicativo padrão

O sistema DEVE abrir o arquivo selecionado no aplicativo padrão do sistema operacional — PDF no leitor de PDFs e HTML no navegador — por duplo-clique, pela tecla Enter ou pelo botão "Abrir".

#### Scenario: Abrir PDF
- **WHEN** o usuário dá duplo-clique em um arquivo PDF
- **THEN** o arquivo DEVE ser aberto no leitor de PDFs padrão do sistema

#### Scenario: Abrir HTML
- **WHEN** o usuário dá duplo-clique em um arquivo HTML
- **THEN** o arquivo DEVE ser aberto no navegador padrão do sistema

#### Scenario: Abrir pela tecla ou botão
- **WHEN** o usuário pressiona Enter ou clica em "Abrir" com um arquivo selecionado
- **THEN** o arquivo DEVE ser aberto no aplicativo padrão correspondente ao seu tipo

### Requirement: Estado vazio e atualização

A sub-aba DEVE exibir uma mensagem informativa quando o ticker não tem documentos em cache e DEVE oferecer um controle para atualizar a varredura do catálogo.

#### Scenario: Ticker sem documentos
- **WHEN** o ticker selecionado não tem documentos em cache
- **THEN** a sub-aba DEVE exibir mensagem de ausência de documentos

#### Scenario: Atualização manual
- **WHEN** o usuário aciona o controle de atualização
- **THEN** o sistema DEVE re-varrer o catálogo e remontar a árvore do ticker
