## ADDED Requirements

### Requirement: Referências de caminho portáveis

O código, os testes, os scripts e a documentação DEVEM referenciar arquivos do projeto por caminhos relativos à raiz do repositório, ou resolvidos a partir de `__file__`/configuração em tempo de execução. Caminhos absolutos específicos da máquina NÃO DEVEM ser embutidos em referências a arquivos do projeto. Ferramentas de desenvolvimento e agentes que acessam os arquivos do projeto DEVEM usar caminhos relativos à raiz do repositório.

#### Scenario: Código referencia arquivo do projeto por caminho relativo
- **WHEN** um módulo, teste ou script referencia um arquivo do projeto
- **THEN** a referência DEVE ser relativa à raiz do repositório ou derivada de `__file__`/configuração, sem embutir caminho absoluto da máquina

#### Scenario: Caminho absoluto específico da máquina é rejeitado
- **WHEN** uma referência a arquivo do projeto contém um caminho absoluto específico da máquina
- **THEN** isso DEVE ser considerado uma violação do engineering standard
- **AND** a referência DEVE ser convertida para caminho relativo à raiz

#### Scenario: Ferramenta ou agente acessa arquivos do projeto
- **WHEN** uma ferramenta de desenvolvimento ou um agente acessa arquivos do projeto
- **THEN** ela DEVE usar caminhos relativos à raiz do repositório
