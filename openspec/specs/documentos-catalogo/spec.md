# documentos-catalogo Specification

## Purpose

Fornecer um catálogo unificado dos documentos em cache (PDFs e HTML) organizado por ticker, ano, mês e categoria, para navegação e visualização na interface.

## Requirements

### Requirement: Varredura das raízes de cache

O sistema DEVE varrer as raízes de documentos em cache — `<cache>/bdr/`, `<cache>/informe-mensal/` e `<cache>/documentos-relevantes/` — e consolidar os arquivos encontrados em um único catálogo. Raízes inexistentes DEVEM ser ignoradas sem erro.

#### Scenario: Consolidação de múltiplas fontes
- **WHEN** existem arquivos em mais de uma raiz de cache para o mesmo ticker
- **THEN** o catálogo DEVE conter os arquivos de todas as raízes

#### Scenario: Raiz inexistente
- **WHEN** uma das raízes de cache não existe no disco
- **THEN** a varredura DEVE continuar com as demais raízes, sem erro

### Requirement: Hierarquia por ticker, ano, mês e categoria

O catálogo DEVE organizar os arquivos na hierarquia `ticker → ano → mês → categoria → arquivos`. A categoria DEVE ser derivada da raiz de origem (`bdr` → "Aviso aos Acionistas"; `informe-mensal` → "Informe Mensal") e, para documentos relevantes, da subpasta de categoria existente sob o mês.

#### Scenario: Categoria derivada da raiz
- **WHEN** o arquivo está sob a raiz `bdr/`
- **THEN** a categoria DEVE ser "Aviso aos Acionistas"

#### Scenario: Categoria derivada da subpasta
- **WHEN** o arquivo está sob `documentos-relevantes/<TICKER>/<AAAA>/<MM>/assembleia/`
- **THEN** a categoria DEVE ser "Assembleia"

### Requirement: Classificação de tipo de arquivo

O catálogo DEVE classificar cada arquivo pelo seu tipo, distinguindo `pdf` de `html` pela extensão, para que a abertura e a pré-visualização sejam tratadas conforme o tipo.

#### Scenario: Arquivo PDF
- **WHEN** o arquivo termina em `.pdf`
- **THEN** o tipo DEVE ser `pdf`

#### Scenario: Arquivo HTML
- **WHEN** o arquivo termina em `.html`
- **THEN** o tipo DEVE ser `html`

### Requirement: Ordenação do catálogo

O catálogo DEVE ordenar anos e meses do mais recente para o mais antigo, categorias em ordem alfabética e arquivos do mais recente para o mais antigo.

#### Scenario: Ordenação cronológica decrescente
- **WHEN** um ticker tem documentos em 2025/11 e 2026/02
- **THEN** o ano 2026 DEVE aparecer antes de 2025 e o mês 02 antes de 11

### Requirement: Ticker sem documentos

O catálogo DEVE retornar uma estrutura vazia quando o ticker não tem documentos em cache, sem erro.

#### Scenario: Ticker sem cache
- **WHEN** o catálogo é consultado para um ticker sem arquivos nas raízes
- **THEN** o catálogo DEVE retornar vazio, sem erro
