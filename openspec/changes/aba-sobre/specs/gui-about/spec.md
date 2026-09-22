## Purpose

Define a aba de nível superior "Sobre" da GUI, que reúne informações institucionais do FlowScope, apresentação do projeto e atalhos para o repositório, o log da aplicação e a página de uma eventual nova versão.

## ADDED Requirements

### Requirement: Aba "Sobre" de nível superior

O sistema DEVE adicionar uma aba de nível superior "Sobre" ao notebook principal, posicionada imediatamente após a aba "Análise do Ticker". A aba DEVE conter conteúdo próprio com rolagem vertical e NÃO DEVE alterar o painel de orientação à direita, que permanece exibindo seu último conteúdo.

#### Scenario: Posicionamento após a Análise do Ticker

- **WHEN** o usuário observa as abas de nível superior
- **THEN** a aba "Sobre" DEVE aparecer imediatamente após "Análise do Ticker"

#### Scenario: Painel de orientação permanece inalterado

- **WHEN** o usuário seleciona a aba "Sobre"
- **THEN** o conteúdo do Sobre DEVE ser exibido e o painel de orientação à direita NÃO DEVE ser atualizado

#### Scenario: Conteúdo rolável

- **WHEN** o conteúdo da aba excede a altura disponível
- **THEN** o sistema DEVE permitir a rolagem vertical do conteúdo

### Requirement: Informações institucionais na aba "Sobre"

O sistema DEVE exibir, na aba "Sobre", nesta ordem: o ícone da aplicação; o nome e a versão no formato `FlowScope vX.Y.Z`; a data de lançamento em formato ISO (`YYYY-MM-DD`); e a licença "Software livre e de código aberto (GNU GPLv3)". A versão DEVE ser obtida de `flowscope.__version__` e a data de `flowscope.__release_date__`.

#### Scenario: Ordem das informações

- **WHEN** a aba "Sobre" é exibida
- **THEN** o ícone, o nome com a versão, a data ISO e a licença DEVEM aparecer nessa ordem

#### Scenario: Valores de versão e data

- **WHEN** `__version__` é "1.1.0" e `__release_date__` é "2026-09-18"
- **THEN** a aba DEVE exibir "FlowScope v1.1.0" e "2026-09-18"

### Requirement: Texto de apresentação do projeto

A aba "Sobre" DEVE exibir um texto de apresentação curto do FlowScope, derivado da seção de descrição do `README.md`, caracterizando a ferramenta como open source de análise quantitativa de fluxo de ordens sobre os dados públicos consolidados da B3, com interface gráfica e linha de comando multiplataforma.

#### Scenario: Apresentação exibida

- **WHEN** a aba "Sobre" é exibida
- **THEN** o texto de apresentação DEVE ser exibido após as informações institucionais

### Requirement: Link para o repositório do projeto

A aba "Sobre" DEVE exibir um botão que abre `https://github.com/amaurycarvalho/flowscope` no navegador padrão do sistema.

#### Scenario: Abertura do repositório

- **WHEN** o usuário aciona o botão do repositório
- **THEN** o navegador padrão DEVE abrir a URL do repositório do projeto

### Requirement: Acesso ao log da aplicação

A aba "Sobre" DEVE exibir um botão que abre o arquivo de log `~/.flowscope/logs/flowscope.log` no aplicativo padrão do sistema. Quando o arquivo ainda não existir, o sistema DEVE informar a indisponibilidade na barra de status, sem falhar silenciosamente.

#### Scenario: Log existente é aberto

- **WHEN** o usuário aciona o botão do log e o arquivo existe
- **THEN** o aplicativo padrão DEVE abrir o arquivo de log

#### Scenario: Log inexistente informa indisponibilidade

- **WHEN** o usuário aciona o botão do log e o arquivo não existe
- **THEN** a barra de status DEVE informar que o log ainda não está disponível

### Requirement: Aviso de nova versão na aba "Sobre"

A aba "Sobre" DEVE, quando a verificação de versão indicar uma versão mais recente, exibir ao final do conteúdo um aviso "Nova versão vX.Y.Z disponível" e um botão que abre a página da release no navegador padrão. Quando não houver versão mais nova ou a verificação falhar, nenhum aviso DEVE ser exibido.

#### Scenario: Nova versão disponível

- **WHEN** a verificação indica uma versão mais recente que a atual
- **THEN** o aviso e o botão para a página da release DEVEM ser exibidos ao final do conteúdo

#### Scenario: Sem novidade

- **WHEN** não há versão mais recente ou a verificação não pôde ser concluída
- **THEN** nenhum aviso de nova versão DEVE ser exibido

### Requirement: Independência da aba "Sobre" em relação aos dados da B3

A aba "Sobre" NÃO DEVE depender de dados da B3. O tratamento de troca de aba DEVE reconhecer "Sobre" sem tentar resolver gráfico nem sub-aba, e a restauração da última aba DEVE selecionar "Sobre" sem alterar os sub-notebooks.

#### Scenario: Troca de aba não resolve gráfico

- **WHEN** o usuário seleciona a aba "Sobre"
- **THEN** o sistema NÃO DEVE tentar resolver ou atualizar gráficos nem sub-abas

#### Scenario: Restauração da última aba

- **WHEN** a aplicação é reaberta com a última aba selecionada igual a "Sobre"
- **THEN** a aba "Sobre" DEVE ser restaurada sem alterar os sub-notebooks
