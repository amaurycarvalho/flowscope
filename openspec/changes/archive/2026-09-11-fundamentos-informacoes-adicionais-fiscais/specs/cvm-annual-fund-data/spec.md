## Purpose

Aquisição e normalização do Informe Anual Estruturado de FIIs da CVM (INF_ANUAL) por CNPJ, expondo gestor, administrador, custodiante e auditor independente com proveniência, para alimentar a identidade fiscal da análise fundamentalista.

## ADDED Requirements

### Requirement: Aquisição do Informe Anual por CNPJ

O sistema DEVE obter o Informe Anual Estruturado do fundo a partir dos dados abertos anuais da CVM (`FII/DOC/INF_ANUAL`), filtrando por CNPJ normalizado e competência, selecionando o registro mais recente cuja data de referência não seja posterior à data de referência consultada, e DEVE distinguir ausência de registro de falha de aquisição.

#### Scenario: Registro do fundo carregado
- **WHEN** existem registros do CNPJ no Informe Anual até a data de referência
- **THEN** o sistema DEVE retornar o registro mais recente com a data de competência

#### Scenario: Sem registro para o CNPJ
- **WHEN** o CNPJ não possui registro no Informe Anual consultado
- **THEN** o sistema DEVE retornar ausência de dados, sem erro

#### Scenario: Falha de aquisição
- **WHEN** o download ou a leitura do arquivo anual falha
- **THEN** o sistema DEVE registrar a indisponibilidade, distinta de ausência de dados

### Requirement: Normalização de gestor, administrador e prestadores

O sistema DEVE normalizar, por CNPJ, o gestor (nome e CNPJ) e o administrador (nome e CNPJ) a partir dos arquivos `geral` e `complemento` do Informe Anual, tratando campos vazios como ausência de valor.

#### Scenario: Gestor e administrador normalizados
- **WHEN** o registro do fundo contém `Nome_Gestor`, `CNPJ_Gestor`, `Nome_Administrador` e `CNPJ_Administrador`
- **THEN** o sistema DEVE expor gestor e administrador com seus CNPJs

#### Scenario: Prestador ausente
- **WHEN** o registro não contém o nome ou o CNPJ de um prestador
- **THEN** o campo correspondente DEVE ser ausência de valor, sem impedir os demais

### Requirement: Cache e versionamento do Informe Anual

O sistema DEVE persistir o arquivo anual bruto com hash e versão do parser e reutilizar o arquivo local quando válido, de modo que consultas subsequentes do mesmo ano não exijam novo download.

#### Scenario: Arquivo reutilizado
- **WHEN** o arquivo anual já está em cache e continua válido
- **THEN** o sistema DEVE servir o arquivo local sem novo download

#### Scenario: Hash e versão registrados
- **WHEN** o arquivo anual é obtido
- **THEN** o sistema DEVE registrar o hash e a versão do parser nos metadados
