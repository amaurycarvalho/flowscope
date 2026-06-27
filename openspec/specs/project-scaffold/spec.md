## ADDED Requirements

### Requirement: Estrutura de diretórios Clean Architecture
O projeto DEVE seguir a estrutura Clean Architecture com diretórios `src/flowscope/` para código-fonte e `tests/` para testes, configurado via `pyproject.toml`.

#### Scenario: Estrutura de diretórios existe
- **WHEN** o projeto é clonado do repositório
- **THEN** os diretórios `src/flowscope/domain/`, `src/flowscope/application/`, `src/flowscope/infrastructure/`, `src/flowscope/presentation/` e `tests/` DEVEM existir com seus respectivos `__init__.py`

### Requirement: pyproject.toml como configuração central
O projeto DEVE ser configurado via `pyproject.toml` na raiz, definindo metadados do projeto, entry point `flowscope = "flowscope.presentation.main:main"` e dependências.

#### Scenario: Entry point configurado
- **WHEN** o pacote é instalado via `pip install -e .`
- **THEN** o comando `flowscope` DEVE estar disponível no PATH e executar `main()`

### Requirement: Ícones movidos para dentro do pacote
Os arquivos de ícones (`flowscope.png`, `flowscope.ico`, `flowscope.icns`) DEVEM ser movidos de `icons/` para `src/flowscope/icons/`.

#### Scenario: Ícones acessíveis como recursos do pacote
- **WHEN** o código referencia um ícone
- **THEN** ele DEVE usar caminho relativo ao pacote `src/flowscope/icons/` (ex: `importlib.resources` ou `pathlib` relativo a `__file__`)

### Requirement: Makefile atualizado para nova estrutura
O `Makefile` DEVE ser atualizado para referenciar a nova estrutura de diretórios e entry point.

#### Scenario: make install cria venv e instala dependências
- **WHEN** executado `make install`
- **THEN** um ambiente virtual `.venv` DEVE ser criado e as dependências de `pyproject.toml` instaladas

#### Scenario: make build gera executável
- **WHEN** executado `make build`
- **THEN** o PyInstaller DEVE gerar o executável `dist/flowscope` (ou `.exe` no Windows) a partir do entry point configurado em `pyproject.toml`

#### Scenario: make test executa testes
- **WHEN** executado `make test`
- **THEN** os testes em `tests/` DEVEM ser executados com unittest discover ou pytest

### Requirement: PyInstaller .spec atualizado
O arquivo `flowscope.spec` DEVE ser atualizado para apontar para o entry point `src/flowscope/presentation/main.py` e incluir os ícones e dados corretamente.

#### Scenario: Spec referencia entry point correto
- **WHEN** PyInstaller processa `flowscope.spec`
- **THEN** o `Analysis` DEVE apontar para `src/flowscope/presentation/main.py` e os `datas` DEVEM incluir `src/flowscope/icons/flowscope.png`

### Requirement: README.md atualizado com novos comandos
O `README.md` DEVE refletir a nova estrutura, substituindo referências a `python3 flowscope.py` por `python3 -m flowscope` ou pelo entry point do binário.

#### Scenario: Comandos no README refletem nova estrutura
- **WHEN** um usuário lê o README
- **THEN** as instruções de uso DEVEM mostrar `python3 -m flowscope --gui` (ou `flowscope --gui` após instalação) ao invés de `python3 flowscope.py --gui`
