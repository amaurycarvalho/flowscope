## Purpose

Aquisição determinística do Informe Trimestral Estruturado e das Demonstrações Financeiras (DFIN) de FIIs a partir dos dados abertos da CVM, por CNPJ, normalizando os componentes de resultado que alimentam o cálculo do FFO.

## ADDED Requirements

### Requirement: Aquisição do Informe Trimestral por CNPJ

O sistema DEVE obter o Informe Trimestral Estruturado do fundo a partir dos dados abertos anuais da CVM, filtrando por CNPJ normalizado e competência, e DEVE preservar o código/identificador original de cada linha de componente, e não apenas o texto descritivo.

#### Scenario: Componentes do fundo carregados
- **WHEN** existem registros do CNPJ no Informe Trimestral da competência
- **THEN** o sistema DEVE retornar os componentes com valor, código original e descrição

#### Scenario: Código original preservado
- **WHEN** um componente é normalizado
- **THEN** o sistema DEVE manter o identificador original da linha para rastreabilidade

### Requirement: Aquisição das Demonstrações Financeiras (DFIN)

O sistema DEVE obter as DFIN anuais do fundo por CNPJ para servir de fonte de reconciliação de resultado líquido, receitas, despesas e patrimônio líquido.

#### Scenario: DFIN disponível para reconciliação
- **WHEN** o fundo possui DFIN do ano de referência
- **THEN** o sistema DEVE disponibilizar os valores para reconciliação com o resultado calculado

### Requirement: Schema versionado e preservação bruta

O sistema DEVE identificar o schema do Informe Trimestral/DFIN pelo conjunto de colunas, aceitar variações de layout conhecidas e preservar os arquivos brutos com hash e versão do parser, falhando de forma explícita quando colunas obrigatórias estiverem ausentes.

#### Scenario: Schema reconhecido
- **WHEN** o arquivo contém as colunas esperadas de identidade e componentes
- **THEN** o sistema DEVE processar os registros e registrar a versão do parser

#### Scenario: Colunas obrigatórias ausentes
- **WHEN** o arquivo não contém as colunas obrigatórias
- **THEN** o sistema DEVE levantar erro de schema em vez de produzir resultado parcial

### Requirement: Tratamento de reapresentações e competência

Quando existirem múltiplos registros para o mesmo CNPJ e competência, o sistema DEVE selecionar a versão mais recente e preservar as anteriores nos dados brutos, sem assumir a posição física do registro.

#### Scenario: Múltiplas versões de um componente
- **WHEN** há mais de um registro para o mesmo CNPJ e competência
- **THEN** o sistema DEVE selecionar a versão mais recente e registrar a versão de origem
