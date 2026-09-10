# cvm-monthly-fund-data Specification

## Purpose
Aquisição determinística do Informe Mensal Estruturado de FIIs a partir dos dados abertos anuais da CVM, por CNPJ, com versionamento de schema, tratamento de reapresentações, hash/metadados e normalização de patrimônio, cotas e cotistas para as métricas fundamentalistas.

## Requirements

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

O sistema DEVE identificar a estrutura de cada CSV do arquivo anual pelo conjunto de colunas, sem assumir a posição física dos registros nem usar apenas o ano como critério de versão. O arquivo anual DEVE ser tratado como multi-arquivo (`geral`, `complemento`, `ativo_passivo`), e cada arquivo DEVE ser processado de forma independente: um arquivo sem as colunas obrigatórias de patrimônio e cotas DEVE ser ignorado, sem abortar a leitura dos demais. O sistema DEVE aceitar os nomes atuais (`CNPJ_Fundo_Classe`, `Data_Referencia`, `Patrimonio_Liquido`, `Cotas_Emitidas`, `Total_Numero_Cotistas`) e aliases legados (`CNPJ_Fundo`, `Nome_Fundo`, `Tipo_Fundo`, `QUANT_COTA`).

#### Scenario: Schema 2025+ reconhecido
- **WHEN** o arquivo `complemento` contém `CNPJ_Fundo_Classe`, `Data_Referencia`, `Patrimonio_Liquido`, `Cotas_Emitidas` e `Total_Numero_Cotistas`
- **THEN** o sistema DEVE resolver essas colunas e processar os registros de patrimônio e cotistas

#### Scenario: Schema legado reconhecido
- **WHEN** o CSV contém `CNPJ_Fundo` e `QUANT_COTA`
- **THEN** o sistema DEVE resolver pelos aliases e processar os registros

#### Scenario: Colunas obrigatórias ausentes
- **WHEN** um CSV do arquivo anual não contém as colunas obrigatórias de patrimônio e cotas
- **THEN** o sistema DEVE ignorar esse arquivo sem produzir dados parcialmente incorretos, continuando a processar os demais

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

O sistema DEVE normalizar os campos de patrimônio líquido (`Patrimonio_Liquido`), quantidade de cotas (`Cotas_Emitidas`) e número de cotistas (`Total_Numero_Cotistas`) do arquivo `complemento` em uma observação de patrimônio com data de referência e fonte CVM.

#### Scenario: Patrimônio normalizado
- **WHEN** um registro do fundo é selecionado no arquivo `complemento`
- **THEN** o sistema DEVE retornar patrimônio líquido, cotas e cotistas com a data de competência e fonte CVM

### Requirement: Patrimônio CVM alimenta P/VP

O patrimônio normalizado DEVE alimentar o cálculo de `P/VP` da análise fundamentalista como fallback, permitindo preencher a coluna quando o Fundamentus não fornecer o dado, sem exigir dados de FFO.

#### Scenario: P/VP preenchido com patrimônio disponível
- **WHEN** a análise fundamentalista recebe patrimônio da CVM e preço de fechamento
- **THEN** a coluna `P/VP` DEVE ser calculada e exibida

#### Scenario: P/VP indisponível
- **WHEN** o patrimônio não está disponível para o ticker
- **THEN** a coluna `P/VP` DEVE ser exibida como `N/A` sem impedir as demais colunas

### Requirement: Revalidação remota do arquivo anual da CVM

O sistema DEVE revalidar o arquivo anual da CVM contra a fonte remota antes de reutilizar o ZIP local, rebaixando-o apenas quando a fonte indicar alteração, de modo que o ano corrente reflita meses e reapresentações publicados após o primeiro download.

#### Scenario: Fonte inalterada

- **WHEN** os validadores remotos indicam que o arquivo anual não mudou
- **THEN** o sistema DEVE reutilizar o ZIP local sem baixá-lo novamente

#### Scenario: Fonte alterada

- **WHEN** os validadores remotos indicam que o arquivo anual mudou
- **THEN** o sistema DEVE baixar o arquivo novamente e atualizar o hash e os metadados

#### Scenario: Novo mês no ano corrente

- **WHEN** um novo mês é publicado no ZIP do ano corrente
- **THEN** o sistema DEVE rebaixar o arquivo e passar a considerar o novo mês nas consultas

### Requirement: Comportamento stale-on-failure na revalidação da CVM

O sistema DEVE servir o arquivo anual local quando a revalidação remota falhar por indisponibilidade, mantendo a análise funcional e registrando o aviso.

#### Scenario: Falha de rede durante a revalidação

- **WHEN** a checagem remota falha e existe ZIP local
- **THEN** o sistema DEVE utilizar o ZIP local e registrar o aviso, sem interromper a análise

### Requirement: Metadados de revalidação registrados

O sistema DEVE registrar os validadores remotos e o instante da última revalidação junto aos metadados do arquivo anual, permitindo auditoria e decisões futuras de revalidação.

#### Scenario: Metadados atualizados após revalidação

- **WHEN** o arquivo anual é revalidado
- **THEN** os metadados DEVEM registrar os validadores remotos e o instante da revalidação
