## Why

Referências a arquivos do projeto por caminhos absolutos são específicas da máquina: quebram portabilidade, revisão, reuso e execução em ambientes diferentes. O código, os testes, os scripts e a documentação devem acessar os arquivos do projeto por caminhos relativos à raiz do repositório. O mesmo vale para ferramentas e agentes que manipulam os arquivos do projeto.

## What Changes

- Adicionar um standard de engenharia exigindo que referências a arquivos do projeto usem caminhos relativos à raiz (ou resolvidos a partir de `__file__`/configuração).
- Proibir caminhos absolutos específicos da máquina em código, testes, scripts e documentação.
- Estender a mesma regra a ferramentas de desenvolvimento e agentes que acessam arquivos do projeto.

## Capabilities

### New Capabilities
<!-- Nenhuma capacidade nova. -->

### Modified Capabilities
- `engineering-standards`: novo requisito "Referências de caminho portáveis", normatizando o uso de caminhos relativos e proibindo caminhos absolutos específicos da máquina.

## Impact

- `openspec/specs/engineering-standards/spec.md` (novo requisito).
- Convenções de código, testes, scripts e documentação que referenciam arquivos do projeto.
- Uso de ferramentas e agentes que acessam arquivos do projeto.
