## Purpose

Persistir o documento HTML do Informe Mensal Estruturado da B3 em uma árvore de arquivos por ticker/ano/mês, para inspeção e visualização dos documentos em cache, reutilizando a aquisição e as entidades de leitura já existentes.

## ADDED Requirements

### Requirement: Persistência do HTML do informe mensal em arquivo

O sistema DEVE gravar o HTML do documento de Informe Mensal Estruturado (type=40) de um ticker em disco, no caminho `<cache>/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`, sem expiração. Quando o arquivo já existir, o sistema DEVE reutilizá-lo sem novo download. Uma falha de download DEVE ser sinalizada sem criar arquivo e sem interromper o processamento de outros tickers.

#### Scenario: Documento novo é gravado
- **WHEN** o informe mensal de um ticker ainda não tem arquivo em cache e o download do HTML é bem-sucedido
- **THEN** o sistema DEVE gravar o arquivo em `<cache>/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`

#### Scenario: Documento já em cache
- **WHEN** o arquivo do informe mensal já existe no cache
- **THEN** o sistema DEVE reutilizá-lo sem realizar novo download

#### Scenario: Falha de download
- **WHEN** o download do HTML do informe mensal falha
- **THEN** o sistema DEVE sinalizar a falha para aquele documento, sem criar arquivo e sem interromper outros tickers

### Requirement: Organização por ano e mês de referência

O sistema DEVE derivar as subpastas de ano e mês da data de referência do informe mensal. Na ausência da data de referência, o sistema DEVE usar a data de entrega do documento e, se esta também estiver ausente, a data corrente.

#### Scenario: Data de referência disponível
- **WHEN** o informe mensal tem data de referência `2026-07-01`
- **THEN** o arquivo DEVE ser gravado sob `<AAAA>=2026` e `<MM>=07`

#### Scenario: Data de referência ausente
- **WHEN** o informe mensal não tem data de referência nem de entrega
- **THEN** o sistema DEVE usar a data corrente para compor as subpastas de ano e mês

### Requirement: Leitura da árvore pelo catálogo de documentos

O sistema DEVE expor a leitura do cache de informes mensais de um ticker, retornando os documentos existentes com seus caminhos, de forma ordenada do mais recente para o mais antigo. Um ticker sem informes em cache DEVE resultar em lista vazia, sem erro.

#### Scenario: Documentos existentes
- **WHEN** um ticker possui arquivos em `<cache>/informe-mensal/<TICKER>/`
- **THEN** o sistema DEVE retornar os documentos encontrados com seus caminhos, do mais recente para o mais antigo

#### Scenario: Ticker sem documentos
- **WHEN** um ticker não possui arquivos no cache de informes mensais
- **THEN** o sistema DEVE retornar lista vazia sem erro
