## Purpose

Adquirir sob demanda os documentos de um ticker e populá-los nas raízes de cache consumidas pela sub-aba "Documentos", escolhendo a fonte pelo tipo do ativo e tolerando indisponibilidade.

## ADDED Requirements

### Requirement: Seleção da fonte pelo tipo do ticker

O sistema DEVE resolver a identidade do ticker e escolher a fonte de documentos pelo tipo do ativo: FIIs usam documentos relevantes e informe mensal; ações e BDRs usam material facts. Um ticker sem identidade resolvida DEVE resultar em nenhuma aquisição, sem erro.

#### Scenario: Ticker de FII
- **WHEN** o ticker é um FII com `idFNET` resolvido
- **THEN** o sistema DEVE adquirir documentos relevantes e o informe mensal

#### Scenario: Ticker de ação
- **WHEN** o ticker é uma ação com `codeCVM` resolvido
- **THEN** o sistema DEVE adquirir os material facts (fatos relevantes e assembleias)

#### Scenario: Ticker não resolvido
- **WHEN** o ticker não tem identidade resolvida
- **THEN** o sistema NÃO DEVE realizar download e DEVE retornar sem erro

### Requirement: Aquisição de material facts de ações e BDRs

Para ações e BDRs, o sistema DEVE listar os material facts das categorias fatos relevantes e assembleias no período de referência, baixar o PDF de cada documento no visualizador da CVM, validar a assinatura `%PDF` e gravar em `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`. Conteúdo que não começa com `%PDF` DEVE ser rejeitado para aquele documento, sem interromper os demais.

#### Scenario: PDF válido é gravado
- **WHEN** o PDF de um material fact é baixado e começa com `%PDF`
- **THEN** o sistema DEVE gravar o arquivo na subpasta da categoria correspondente sob o ano e mês de referência

#### Scenario: Conteúdo não é PDF
- **WHEN** o conteúdo baixado de um material fact não começa com `%PDF`
- **THEN** o documento DEVE ser rejeitado, sem criar arquivo e sem interromper os demais

#### Scenario: Categoria mapeada para slug de pasta
- **WHEN** o material fact é da categoria fatos relevantes
- **THEN** o arquivo DEVE ser gravado sob a subpasta `fato-relevante`

### Requirement: Aquisição de documentos relevantes de FIIs

Para FIIs, o sistema DEVE listar os documentos relevantes das quatro categorias (fatos relevantes, assembleias, comunicados e relatórios) no período de referência, baixar os PDFs com validação `%PDF` e gravá-los na árvore `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`. Falhas por categoria DEVEM ser toleradas sem interromper as demais.

#### Scenario: Documentos de FII são cacheados
- **WHEN** um FII tem documentos relevantes no período
- **THEN** os PDFs DEVEM ser gravados na árvore por ticker/ano/mês/categoria

#### Scenario: Falha em uma categoria
- **WHEN** a listagem de uma categoria falha
- **THEN** as demais categorias DEVEM continuar e o cache DEVE conter os documentos disponíveis

### Requirement: Aquisição do informe mensal de FIIs

Para FIIs, o sistema DEVE persistir o HTML do informe mensal estruturado mais recente em `<cache>/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`, com ano e mês derivados da data de referência e reuso de arquivo já existente sem novo download.

#### Scenario: Informe mensal é gravado
- **WHEN** um FII tem informe mensal aplicável e ainda não há arquivo em cache
- **THEN** o HTML DEVE ser gravado sob o ano e mês de referência

#### Scenario: Informe já em cache
- **WHEN** o arquivo do informe mensal já existe no cache
- **THEN** o sistema DEVE reutilizá-lo sem novo download

### Requirement: Janela de aquisição de 12 meses

Toda aquisição DEVE consultar e baixar apenas os documentos do ticker dentro da janela de 12 meses até a data de referência — para documentos relevantes, material facts e informe mensal — reutilizando sem novo download os arquivos já existentes em cache.

#### Scenario: Início da janela
- **WHEN** a aquisição é acionada para uma data de referência
- **THEN** o sistema DEVE usar como início a data de referência menos 12 meses

#### Scenario: Documento anterior à janela
- **WHEN** um documento existe antes do início da janela de 12 meses
- **THEN** o sistema NÃO DEVE baixá-lo

### Requirement: Reuso de cache e tolerância a falhas

O sistema DEVE reutilizar arquivos já existentes em cache sem novo download. Uma falha de rede ou de um documento individual DEVE ser sinalizada sem criar arquivo e sem interromper a aquisição dos demais documentos nem de outros tickers.

#### Scenario: Documento já em cache
- **WHEN** o arquivo de um documento já existe no cache
- **THEN** o sistema DEVE reutilizá-lo sem realizar novo download

#### Scenario: Falha de rede isolada
- **WHEN** o download de um documento falha
- **THEN** o sistema DEVE sinalizar a falha para aquele documento, sem criar arquivo e sem interromper os demais
