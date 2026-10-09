## ADDED Requirements

### Requirement: Exposição somente-leitura das avaliações de guidance para a árvore e o chat

O sistema DEVE expor, em modo somente-leitura, as entradas do ledger de guidance de um ticker que possuam resultado de guidance (valor), com a data do relatório e a identidade do Relatório Gerencial associado, para montar o ramo Guidance da sub-aba "Documentos" e o ramo de guidance da árvore de conhecimento do chat. A exposição NÃO DEVE avaliar, alterar o ledger, reextrair arquivos nem consultar a B3/CVM. Entradas cujo resultado seja ausência de guidance NÃO DEVEM integrar a exposição.

#### Scenario: Entradas com guidance são disponibilizadas
- **WHEN** o ledger do FII contém uma avaliação com valor de guidance
- **THEN** o sistema DEVE disponibilizar essa entrada com a data do relatório e a identidade do Relatório Gerencial associado

#### Scenario: Ausências não integram a exposição
- **WHEN** o ledger do FII contém apenas entradas cujo resultado é ausência de guidance
- **THEN** o sistema NÃO DEVE disponibilizar nenhuma entrada

#### Scenario: Leitura sem efeitos colaterais
- **WHEN** a exposição é consultada
- **THEN** o ledger DEVE permanecer inalterado e nenhum PDF DEVE ser relido ou reextraído
