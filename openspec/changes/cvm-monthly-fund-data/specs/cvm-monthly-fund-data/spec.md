## Purpose

Aquisição determinística do Informe Mensal Estruturado de FIIs a partir dos dados abertos anuais da CVM, por CNPJ, com versionamento de schema, tratamento de reapresentações, hash/metadados e normalização de patrimônio, cotas e cotistas para as métricas fundamentalistas.

## ADDED Requirements

### Requirement: Resolução de identidade CVM por ticker

O sistema DEVE resolver um ticker para a identidade regulatória (`CNPJ_Fundo_Classe` normalizado, `idFNET` e `Codigo_CVM`), combinando a identidade B3 com o cadastro da CVM, e NÃO DEVE usar o ticker diretamente como chave de filtro do dataset da CVM. O CNPJ DEVE ser armazenado sem pontuação.

#### Scenario: Identidade resolvida a partir do ticker
- **WHEN** o ticker resolve para um CNPJ no cadastro CVM
- **THEN** o sistema DEVE retornar a identidade com CNPJ sem pontuação, `idFNET` e nome do fundo

#### Scenario: Ticker sem identidade CVM
- **WHEN** o ticker não resolve para um CNPJ
- **THEN** o sistema DEVE indicar ausência de identidade sem lançar exceção

### Requirement: Download e cache do arquivo anual com hash

O sistema DEVE baixar o arquivo anual do Informe Mensal (`inf_mensal_fii_<ano>.zip`) correspondente à competência consultada, preservar o arquivo bruto e registrar hash SHA-256 e metadados (dataset, ano, URL, data de download, versão do parser). O arquivo NÃO DEVE ser baixado novamente quando o hash/metadados em cache indicarem que a fonte não mudou.

#### Scenario: Download único por ano
- **WHEN** o mesmo ano é consultado para vários tickers
- **THEN** o sistema DEVE baixar o arquivo anual uma única vez e reutilizá-lo do cache

#### Scenario: Metadados e hash registrados
- **WHEN** um arquivo anual é baixado
- **THEN** o sistema DEVE registrar o hash SHA-256 e os metadados de aquisição junto ao arquivo bruto

### Requirement: Descoberta e versionamento de schema

O sistema DEVE identificar a estrutura do CSV pelo conjunto de colunas, sem assumir a posição física dos registros nem usar apenas o ano como critério de versão, e DEVE aceitar aliases legados (`CNPJ_Fundo`, `Nome_Fundo`, `Tipo_Fundo`, `QUANT_COTA`) além dos nomes atuais (`CNPJ_Fundo_Classe`, `Nome_Fundo_Classe`, `Tipo_Fundo_Classe`, `QT_COTA`). A ausência de colunas obrigatórias DEVE levantar erro de schema.

#### Scenario: Schema 2025+ reconhecido
- **WHEN** o CSV contém `CNPJ_Fundo_Classe` e `QT_COTA`
- **THEN** o sistema DEVE resolver essas colunas e processar os registros

#### Scenario: Schema legado reconhecido
- **WHEN** o CSV contém `CNPJ_Fundo` e `QUANT_COTA`
- **THEN** o sistema DEVE resolver pelos aliases e processar os registros

#### Scenario: Colunas obrigatórias ausentes
- **WHEN** o CSV não contém as colunas de identidade e competência esperadas
- **THEN** o sistema DEVE levantar erro de schema em vez de produzir dados parcialmente incorretos

### Requirement: Filtro por CNPJ e competência

O sistema DEVE filtrar os registros do fundo pelo CNPJ normalizado e pela competência de referência, validando a identidade (`CNPJ`, nome e tipo) contra a identidade previamente resolvida.

#### Scenario: Registros do fundo na competência
- **WHEN** existem registros do CNPJ na competência de referência
- **THEN** o sistema DEVE retornar apenas esses registros

#### Scenario: Fundo sem registros na competência
- **WHEN** não há registros do CNPJ na competência de referência
- **THEN** o sistema DEVE indicar ausência de dados, distinta de falha de aquisição

### Requirement: Tratamento de reapresentações

Quando existirem múltiplos registros para o mesmo CNPJ e competência, o sistema DEVE selecionar a versão mais recente conforme os campos de versão/data de recebimento, registrar a versão selecionada e preservar os registros anteriores nos dados brutos.

#### Scenario: Múltiplas versões
- **WHEN** há dois registros para o mesmo CNPJ e competência com versões distintas
- **THEN** o sistema DEVE selecionar o mais recente e marcar a seleção com `is_latest` e a versão de origem

### Requirement: Normalização de patrimônio, cotas e cotistas

O sistema DEVE normalizar os campos de patrimônio líquido (`VL_PATRIM_LIQ`), quantidade de cotas (`QT_COTA`) e número de cotistas (`NR_COTST`) em uma observação de patrimônio com data de referência e fonte CVM.

#### Scenario: Patrimônio normalizado
- **WHEN** um registro do fundo é selecionado
- **THEN** o sistema DEVE retornar patrimônio líquido, cotas e cotistas com a data de competência e fonte CVM

### Requirement: Patrimônio CVM alimenta P/VP

O patrimônio normalizado DEVE alimentar o cálculo de `P/VP` da análise fundamentalista como fallback, permitindo preencher a coluna quando o Fundamentus não fornecer o dado, sem exigir dados de FFO.

#### Scenario: P/VP preenchido com patrimônio disponível
- **WHEN** a análise fundamentalista recebe patrimônio da CVM e preço de fechamento
- **THEN** a coluna `P/VP` DEVE ser calculada e exibida

#### Scenario: P/VP indisponível
- **WHEN** o patrimônio não está disponível para o ticker
- **THEN** a coluna `P/VP` DEVE ser exibida como `N/A` sem impedir as demais colunas
