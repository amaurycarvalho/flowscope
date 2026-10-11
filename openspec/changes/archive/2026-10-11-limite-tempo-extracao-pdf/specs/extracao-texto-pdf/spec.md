## ADDED Requirements

### Requirement: Orçamento de tempo da extração de arquivo

O sistema DEVE limitar a extração de texto de cada arquivo PDF a um orçamento de
tempo por documento de 90 segundos. Ao exceder o orçamento, a extração DEVE ser
interrompida, o texto já produzido DEVE ser preservado e o resultado DEVE ter
estado `PARCIAL` — ou `FALHA`, quando nenhuma página tiver produzido texto —
sem propagar exceção. A extração de HTML NÃO DEVE estar sujeita ao orçamento.

#### Scenario: PDF dentro do orçamento
- **WHEN** um PDF é extraído dentro do orçamento de tempo
- **THEN** o resultado DEVE seguir a classificação por estado já existente (completo, parcial, sem texto, falha ou protegido)

#### Scenario: PDF que excede o orçamento mantém o texto parcial
- **WHEN** a extração de um PDF excede o orçamento de tempo após produzir texto em ao menos uma página
- **THEN** a extração DEVE ser interrompida e o resultado DEVE ter estado parcial, com o texto das páginas já extraídas

#### Scenario: PDF que excede o orçamento sem texto
- **WHEN** a extração de um PDF excede o orçamento de tempo sem que nenhuma página tenha produzido texto
- **THEN** a extração DEVE ser interrompida e o resultado DEVE ter estado de falha, com texto vazio

#### Scenario: HTML não está sujeito ao orçamento
- **WHEN** o arquivo é HTML
- **THEN** a extração DEVE ocorrer sem orçamento de tempo e retornar a classificação por estado já existente

#### Scenario: Tempo limite não propaga exceção
- **WHEN** qualquer extração de arquivo é executada, inclusive com estouro do orçamento
- **THEN** o sistema NÃO DEVE propagar exceção da biblioteca de extração

### Requirement: Tolerância a limite de recursos da biblioteca por página

Quando a extração do texto de uma página falhar com `LimitReachedError`
(subclasse de `PyPdfError`), o sistema NÃO DEVE interromper o documento: DEVE
prosseguir para as páginas seguintes, contabilizar a página como falha e
classificar o resultado como `PARCIAL`. Somente quando nenhuma página produzir
texto o resultado DEVE ser `FALHA`. A exceção NÃO DEVE propagar ao chamador.

#### Scenario: Erro de limite em uma página não descarta as demais
- **WHEN** a extração de uma página falha com `LimitReachedError` e há páginas seguintes legíveis
- **THEN** o sistema DEVE prosseguir para as próximas páginas e o resultado DEVE ser `PARCIAL`, contando a página que falhou

#### Scenario: Erro de limite sem nenhuma página com texto
- **WHEN** todas as páginas falham, inclusive por `LimitReachedError`, sem produzir texto
- **THEN** o resultado DEVE ter estado de falha, com texto vazio e sem propagar a exceção

#### Scenario: Erro de limite em página isolada
- **WHEN** apenas uma página de um PDF legível falha com `LimitReachedError`
- **THEN** o texto das demais páginas DEVE ser preservado e a contagem de páginas com falha DEVE incluir a página afetada

### Requirement: Preservação da classificação de ausência de texto

A classificação de ausência de texto permanece inalterada: um PDF lido com
sucesso cujas páginas não produzem texto DEVE continuar sendo classificado como
`SEM_TEXTO`. Os caminhos de estouro de orçamento e de erro de limite DEVEM
classificar o resultado como `PARCIAL` ou `FALHA`, NUNCA como `SEM_TEXTO`, para
não converter uma extração interrompida em ausência definitiva de texto.

#### Scenario: PDF sem texto permanece sem texto
- **WHEN** um PDF é lido com sucesso e nenhuma página produz texto, dentro do orçamento
- **THEN** o resultado DEVE ter estado `SEM_TEXTO`, como hoje

#### Scenario: Estouro do orçamento não vira ausência definitiva
- **WHEN** a extração de um PDF é interrompida pelo orçamento
- **THEN** o resultado NÃO DEVE ser `SEM_TEXTO` e DEVE ser `PARCIAL` ou `FALHA`

#### Scenario: Falha de limite não vira ausência definitiva
- **WHEN** a extração de um PDF é interrompida por `LimitReachedError` em todas as páginas
- **THEN** o resultado NÃO DEVE ser `SEM_TEXTO` e DEVE ser `FALHA`
