# Spec Delta

## ADDED Requirements

### Requirement: Atualizar o calendário de feriados

O sistema DEVE aceitar `flowscope atualizar feriados [--ano <AAAA>]...`. Sem `--ano`, DEVE atualizar o ano corrente no fuso local do processo. A atualização DEVE forçar a revalidação na ANBIMA, ignorando o TTL, gravar o cache de forma atômica e executar o housekeeping. A saída DEVE ser JSON estruturado com o estado de cada ano.

#### Scenario: Atualização do ano corrente
- **WHEN** o usuário executa `flowscope atualizar feriados` sem `--ano`
- **THEN** o ano corrente no fuso local é revalidado na ANBIMA
- **THEN** o JSON de saída informa o estado `ok` e a origem dos feriados

#### Scenario: Atualização de anos específicos
- **WHEN** o usuário executa `flowscope atualizar feriados --ano 2026 --ano 2027`
- **THEN** os dois anos são revalidados na ANBIMA
- **THEN** o JSON informa o estado de cada ano

#### Scenario: Falha com cache anterior
- **WHEN** a ANBIMA falha para um ano que possui cache anterior
- **THEN** o cache anterior é preservado
- **THEN** o JSON informa o estado `defasado`

#### Scenario: Falha sem cache anterior
- **WHEN** a ANBIMA falha para um ano sem cache anterior
- **THEN** o JSON informa `calendario_indisponivel` para o ano
- **THEN** o processo encerra com código 1

#### Scenario: Housekeeping após sucesso
- **WHEN** a atualização de pelo menos um ano termina com sucesso
- **THEN** o housekeeping remove os anos fora de `[ano_corrente - 3, ano_corrente + 1]`
- **THEN** o ano da operação corrente nunca é removido
