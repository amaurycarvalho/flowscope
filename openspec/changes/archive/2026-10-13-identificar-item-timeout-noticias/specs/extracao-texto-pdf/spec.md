## ADDED Requirements

### Requirement: Orçamento de tempo da extração de PDF a partir de bytes

O sistema DEVE oferecer a extração orçada de texto de um PDF a partir do conteúdo em memória (bytes), aplicando o mesmo orçamento de tempo por documento e a mesma classificação de estados da extração por arquivo. Ao exceder o orçamento, a extração DEVE ser interrompida, o texto já produzido DEVE ser preservado e o resultado DEVE ter estado `PARCIAL` — ou `FALHA`, quando nenhuma página tiver produzido texto — sem propagar exceção e NUNCA como `SEM_TEXTO`. A extração a partir de bytes DEVE honrar a tentativa de senha vazia e a senha opcional informada.

#### Scenario: PDF em memória dentro do orçamento

- **WHEN** um PDF em memória é extraído dentro do orçamento de tempo
- **THEN** o resultado DEVE seguir a classificação por estado já existente (completo, parcial, sem texto, falha ou protegido)

#### Scenario: PDF em memória que excede o orçamento mantém o texto parcial

- **WHEN** a extração de um PDF em memória excede o orçamento após produzir texto em ao menos uma página
- **THEN** a extração DEVE ser interrompida e o resultado DEVE ter estado parcial, com o texto das páginas já extraídas

#### Scenario: PDF em memória que excede o orçamento sem texto

- **WHEN** a extração de um PDF em memória excede o orçamento sem que nenhuma página tenha produzido texto
- **THEN** a extração DEVE ser interrompida e o resultado DEVE ter estado de falha, com texto vazio

#### Scenario: PDF em memória protegido por senha

- **WHEN** um PDF em memória está criptografado e não abre com senha vazia nem com a senha informada
- **THEN** o resultado DEVE ter estado protegido, sem propagar exceção
