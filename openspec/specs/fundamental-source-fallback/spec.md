# fundamental-source-fallback Specification

## Purpose
Composição de fontes fundamentalistas com prioridade por campo, usando o Fundamentus como fonte primária e B3, CVM e o motor de FFO como fallback, preservando a proveniência da origem de cada valor consumido pela análise fundamentalista.

## Requirements

### Requirement: Prioridade por campo na composição de fontes

O sistema DEVE resolver cada campo da análise fundamentalista consultando as fontes em ordem de prioridade, com o Fundamentus como primário, e DEVE usar a primeira fonte que fornecer o campo.

#### Scenario: Campo presente no Fundamentus
- **WHEN** o Fundamentus fornece `P/VP` para o ticker
- **THEN** o sistema DEVE usar o valor do Fundamentus sem consultar o fallback para esse campo

#### Scenario: Campo ausente no Fundamentus
- **WHEN** o Fundamentus não fornece `P/VP` para o ticker
- **THEN** o sistema DEVE buscar `P/VP` no fallback (CVM) e usar o valor encontrado

### Requirement: Fallback por falha de conexão ou scraping

Quando a aquisição no Fundamentus falhar (rede, layout alterado ou ticker não encontrado), o sistema DEVE continuar a análise usando as fontes de fallback, sem interromper os demais tickers.

#### Scenario: Fundamentus indisponível
- **WHEN** a requisição ao Fundamentus falha para um ticker
- **THEN** o sistema DEVE compor os campos com B3/CVM/motor de FFO e manter a linha do ticker na tabela

#### Scenario: Isolamento entre tickers
- **WHEN** um ticker falha em todas as fontes
- **THEN** os demais tickers DEVEM continuar sendo processados normalmente

### Requirement: Proveniência da origem por campo

O sistema DEVE registrar, para cada campo composto, qual fonte forneceu o valor, permitindo explicar a origem dos dados exibidos.

#### Scenario: Origem registrada
- **WHEN** um campo é resolvido pelo fallback
- **THEN** o sistema DEVE registrar a fonte de fallback como origem daquele campo

#### Scenario: Origem do valor primário
- **WHEN** um campo é resolvido pelo Fundamentus
- **THEN** o sistema DEVE registrar o Fundamentus como origem daquele campo

### Requirement: Integração com a análise fundamentalista

O provider composto DEVE alimentar a análise fundamentalista como caminho primário, mantendo as métricas disponíveis e exibindo `N/A` apenas quando nenhuma fonte fornecer o dado.

#### Scenario: Métricas preenchidas pelo primário
- **WHEN** o Fundamentus fornece FFO Yield, Dividend Yield e P/VP
- **THEN** a análise fundamentalista DEVE exibir essas métricas preenchidas

#### Scenario: Métrica indisponível em todas as fontes
- **WHEN** nenhuma fonte fornece um dado (ex.: última data-com)
- **THEN** a métrica correspondente DEVE ser exibida como `N/A` sem impedir as demais

### Requirement: Configuração da ordem de prioridade

A ordem das fontes de fallback DEVE ser configurável, com o Fundamentus como primário por padrão, permitindo substituir fontes sem alterar a análise fundamentalista.

#### Scenario: Ordem padrão
- **WHEN** nenhuma configuração é informada
- **THEN** o sistema DEVE usar Fundamentus como primário e B3/CVM/motor de FFO como fallback

### Requirement: Prioridade de fonte para cotistas e patrimônio

O sistema DEVE resolver o número de cotistas e o patrimônio líquido de um FII priorizando a fonte cuja informação é mais atual — a B3 (Informe Mensal Estruturado), disponível por ticker assim que o informe é entregue — e usando a CVM como fallback quando a B3 não fornecer o dado, preservando a origem e a data de referência do valor utilizado.

#### Scenario: B3 fornece o dado
- **WHEN** a B3 possui o Informe Mensal Estruturado do ticker até a data de referência
- **THEN** o sistema DEVE usar o número de cotistas e o patrimônio da B3, registrando a origem B3

#### Scenario: B3 indisponível
- **WHEN** a B3 não possui o informe do ticker e a CVM possui o registro
- **THEN** o sistema DEVE usar o número de cotistas e o patrimônio da CVM, registrando a origem CVM

#### Scenario: Nenhuma fonte disponível
- **WHEN** nem a B3 nem a CVM possuem o dado
- **THEN** o sistema DEVE indicar ausência de valor, sem impedir as demais colunas
