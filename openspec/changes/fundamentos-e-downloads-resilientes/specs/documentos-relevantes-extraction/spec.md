## MODIFIED Requirements

### Requirement: Download de PDF com validação
O sistema DEVE baixar PDFs dos documentos relevantes no visualizador do FNET por meio do download resiliente compartilhado (`download-conteudo-resiliente`), validando que o conteúdo começa com `%PDF` e cacheando em `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`, sem expiração. Quando o arquivo já existir, o sistema DEVE reutilizá-lo sem novo download. Uma resposta de sucesso com conteúdo que não começa com `%PDF` DEVE ser repetida dentro do orçamento do item e, esgotado o orçamento, o documento DEVE ser descartado sem criar arquivo e sem interromper os demais.

#### Scenario: Download bem-sucedido de PDF válido
- **WHEN** um PDF é baixado e os primeiros 4 bytes são `%PDF`
- **THEN** o conteúdo binário DEVE ser gravado no caminho da árvore por ticker/ano/mês/categoria

#### Scenario: Conteúdo não é PDF
- **WHEN** o conteúdo baixado de um documento relevante não começa com `%PDF`
- **THEN** o sistema DEVE repetir dentro do orçamento e, esgotado, descartar o documento sem criar arquivo e sem interromper os demais

#### Scenario: Orçamento esgotado não interrompe os demais
- **WHEN** o host do FNET fica indisponível até o orçamento do item se esgotar
- **THEN** o documento DEVE ficar ausente e a aquisição dos demais documentos DEVE prosseguir

#### Scenario: PDF já em cache
- **WHEN** o arquivo do documento já existe no cache
- **THEN** o sistema DEVE retornar o conteúdo do cache sem realizar download
