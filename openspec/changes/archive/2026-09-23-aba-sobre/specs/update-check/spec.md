## Purpose

Verifica se há uma versão mais recente do FlowScope publicada no repositório GitHub e disponibiliza a URL da release para que a interface possa avisar o usuário e abri-la no navegador.

## ADDED Requirements

### Requirement: Verificação de nova versão no repositório

O sistema DEVE verificar, ao abrir a aba "Sobre", se há versão mais recente publicada no repositório `amaurycarvalho/flowscope`, no máximo uma vez por sessão. A verificação DEVE ocorrer fora da thread da interface e NÃO DEVE bloquear a janela. Falhas de rede, timeout ou resposta inesperada DEVEM ser tratadas silenciosamente, sem alterar a interface, podendo ser registradas no log.

#### Scenario: Primeira abertura da aba inicia a verificação

- **WHEN** a aba "Sobre" é aberta pela primeira vez na sessão
- **THEN** a verificação DEVE ser iniciada em background, sem bloquear a interface

#### Scenario: Aberturas seguintes não repetem a verificação

- **WHEN** a aba "Sobre" é aberta novamente na mesma sessão
- **THEN** nenhuma nova verificação DEVE ser iniciada

#### Scenario: Falha de rede é silenciosa

- **WHEN** a rede está indisponível ou a requisição excede o tempo limite
- **THEN** a interface NÃO DEVE exibir erro e NÃO DEVE travar

### Requirement: Obtenção da versão publicada

A verificação DEVE obter a versão publicada mais recente a partir de `https://github.com/amaurycarvalho/flowscope/releases/latest`, seguindo o redirecionamento e extraindo a tag do caminho final (`/releases/tag/vX.Y.Z`). Quando o endereço não redirecionar para uma tag, a verificação DEVE ser considerada sem novidade.

#### Scenario: Tag extraída do redirecionamento

- **WHEN** o redirecionamento termina em `/releases/tag/v1.2.0`
- **THEN** a versão publicada DEVE ser "1.2.0"

#### Scenario: Sem redirecionamento para tag

- **WHEN** o endereço não redireciona para uma tag de release
- **THEN** a verificação DEVE ser considerada sem novidade

### Requirement: Comparação semântica de versões

O sistema DEVE comparar a versão publicada com `flowscope.__version__` por comparação semântica numérica de três segmentos, tolerando o prefixo `v` e segmentos não numéricos sem lançar exceção.

#### Scenario: Versão publicada mais nova

- **WHEN** a versão publicada é "1.2.0" e a atual é "1.1.0"
- **THEN** o sistema DEVE indicar novidade e disponibilizar a URL da release

#### Scenario: Versão publicada igual ou anterior

- **WHEN** a versão publicada é "1.1.0" ou inferior à atual
- **THEN** o sistema NÃO DEVE indicar novidade

#### Scenario: Versão publicada inválida

- **WHEN** a versão publicada não pode ser interpretada como `X.Y.Z`
- **THEN** o sistema NÃO DEVE indicar novidade e NÃO DEVE lançar exceção

### Requirement: Disponibilização da URL da nova versão

Quando houver novidade, o sistema DEVE disponibilizar a URL `https://github.com/amaurycarvalho/flowscope/releases/tag/vX.Y.Z` correspondente à versão publicada, para abertura no navegador padrão.

#### Scenario: URL da release disponível

- **WHEN** há uma versão mais recente
- **THEN** a URL da release correspondente DEVE estar disponível para abertura no navegador
