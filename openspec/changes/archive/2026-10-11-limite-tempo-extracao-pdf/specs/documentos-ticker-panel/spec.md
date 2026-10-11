## ADDED Requirements

### Requirement: Orçamento de tempo da extração na pré-visualização e no lote

A pré-visualização sob demanda e a fase de preparação de textos do lote DEVEM
estar sujeitas ao orçamento de tempo por documento. Quando a extração de um
documento exceder o orçamento, o sistema NÃO DEVE bloquear a operação: no lote,
o documento DEVE ser tratado como pendente (texto parcial) e o processamento
DEVE prosseguir para o próximo documento, com a fase avançando; na
pré-visualização, o texto parcial DEVE ser exibido com a anotação de extração
parcial, sem manter o estado de carregamento indefinidamente.

#### Scenario: Documento lento não bloqueia a preparação
- **WHEN** a extração de um documento pendente excede o orçamento durante a preparação do lote
- **THEN** o lote DEVE contabilizar o documento e prosseguir para o próximo, avançando a fase, sem interromper a operação

#### Scenario: Documento lento permanece pendente
- **WHEN** um documento pendente tem a extração interrompida pelo orçamento
- **THEN** ele NÃO DEVE ser marcado como ausência definitiva de texto e DEVE continuar elegível para nova tentativa

#### Scenario: Documento lento na pré-visualização
- **WHEN** a extração do documento selecionado excede o orçamento
- **THEN** a pré-visualização DEVE exibir o texto parcial com a anotação de extração parcial, sem permanecer em "Carregando…"

#### Scenario: Extração dentro do orçamento inalterada
- **WHEN** a extração de um documento ocorre dentro do orçamento
- **THEN** a pré-visualização e o lote DEVEM manter o comportamento já existente

#### Scenario: Documento sem texto extraível mantém o comportamento
- **WHEN** um documento pendente é extraído com sucesso e não tem texto extraível
- **THEN** ele DEVE continuar sendo tratado como ausência definitiva de texto — persistido como sem texto, fora dos pendentes e sem resumo — como hoje

#### Scenario: Extração interrompida não é ausência definitiva
- **WHEN** a extração de um documento é interrompida pelo orçamento ou por `LimitReachedError`
- **THEN** o documento NÃO DEVE ser tratado como ausência definitiva de texto e DEVE permanecer pendente
