## MODIFIED Requirements

### Requirement: Extração da identidade fiscal do Informe Mensal Estruturado

O sistema DEVE extrair, por rótulo, o CNPJ do fundo, o administrador (nome e CNPJ) e o gestor (nome e CNPJ) do HTML do Informe Mensal Estruturado do FundosNet, tolerando rótulos ausentes sem invalidar os demais campos do informe. O CNPJ DEVE ser reconhecido tanto no rótulo `CNPJ do Fundo/Classe` quanto na variante `CNPJ do Fundo`.

#### Scenario: CNPJ do fundo extraído
- **WHEN** o informe ativo contém o rótulo `CNPJ do Fundo/Classe`
- **THEN** o sistema DEVE expor o CNPJ do fundo normalizado

#### Scenario: CNPJ do fundo extraído na variante FIAGRO
- **WHEN** o informe ativo contém o rótulo `CNPJ do Fundo` (sem `/Classe`)
- **THEN** o sistema DEVE expor o CNPJ do fundo normalizado, sem impedir a extração dos demais campos

#### Scenario: Administrador e CNPJ extraídos
- **WHEN** o informe ativo contém os rótulos `Nome do Administrador` e `CNPJ do Administrador`
- **THEN** o sistema DEVE expor o nome e o CNPJ do administrador

#### Scenario: Gestor e CNPJ extraídos
- **WHEN** o informe ativo contém os rótulos `Nome do Gestor` e `CNPJ do Gestor`
- **THEN** o sistema DEVE expor o nome e o CNPJ do gestor

#### Scenario: Rótulo ausente
- **WHEN** um dos rótulos de identidade fiscal está ausente
- **THEN** o campo correspondente DEVE ser ausência de valor, sem impedir a extração dos demais

## ADDED Requirements

### Requirement: Uso da identidade persistida de idFNET e CNPJ como fallback fiscal

O sistema DEVE reutilizar a identidade persistida por ticker (`idFNET` e CNPJ, gravada pela resolução de fundos) na leitura do Informe Mensal e como fallback do CNPJ fiscal, sem criar um segundo cache nem alterar o schema do registro existente. O CNPJ do informe DEVE prevalecer quando disponível.

#### Scenario: idFNET persistido usado na leitura do informe
- **WHEN** a listagem de fundos da B3 está incompleta ou indisponível e existe identidade persistida com `idFNET` para o ticker
- **THEN** o sistema DEVE usar o `idFNET` persistido para listar e extrair o Informe Mensal

#### Scenario: CNPJ fiscal a partir da identidade persistida
- **WHEN** o informe não fornece o CNPJ e a identidade persistida do ticker possui CNPJ
- **THEN** o sistema DEVE expor o CNPJ persistido como CNPJ fiscal, registrando a origem B3

#### Scenario: Informe prevalece sobre a identidade persistida
- **WHEN** o informe fornece um CNPJ e a identidade persistida possui outro valor
- **THEN** o sistema DEVE usar o CNPJ do informe, sem sobrescrever o valor persistido com ausência

#### Scenario: Sem identidade persistida
- **WHEN** a B3 está indisponível e não existe identidade persistida para o ticker
- **THEN** o CNPJ DEVE permanecer ausente, sem erro e sem gravação de resultado negativo

### Requirement: Listagem de documentos resistente a respostas vazias intermitentes

O sistema DEVE tratar uma primeira página vazia do `GetStructuredReports` como suspeita, repetindo a consulta uma vez e descartando a chave de cache antes da repetição. Um vazio que persista após a repetição NÃO DEVE ser mantido no cache. A chave de cache da listagem DEVE ser versionada pela versão de aquisição.

#### Scenario: Vazio intermitente repetido
- **WHEN** a primeira consulta da listagem de documentos retorna lista vazia e a repetição retorna documentos
- **THEN** o sistema DEVE usar os documentos da repetição e manter o resultado em cache

#### Scenario: Vazio persistente não é cacheado
- **WHEN** a listagem permanece vazia após a repetição
- **THEN** o sistema DEVE descartar a chave de cache, permitindo nova consulta em execução futura

#### Scenario: Chave versionada descarta cache envenenado
- **WHEN** existir uma listagem vazia gravada por versão anterior da aquisição
- **THEN** o sistema DEVE ignorá-la e consultar a fonte novamente
