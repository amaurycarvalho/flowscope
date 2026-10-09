## ADDED Requirements

### Requirement: Exposure do guidance do RG para exibição na leitura

Ao ler um Relatório Gerencial na sub-aba "Documentos", o resultado da avaliação daquele RG — o guidance ou a ausência — DEVE ser disponibilizado ao fluxo de leitura para exibição, sem nova consulta ao ledger na thread da interface e sem reavaliar o RG. O guidance disponibilizado DEVE corresponder à entrada do ledger identificada pela chave de conteúdo do documento selecionado, e não ao guidance corrente derivado do FII. Quando o RG já possui entrada no ledger por um método que dispensa reavaliação, a entrada existente DEVE ser a fonte do guidance disponibilizado. O lote de resumos DEVE propagar o resultado da avaliação de cada RG junto do resumo, para a recomposição da pré-visualização.

#### Scenario: RG com guidance é disponibilizado na leitura
- **WHEN** o usuário lê um Relatório Gerencial cuja entrada no ledger registra guidance
- **THEN** o sistema DEVE disponibilizar esse guidance ao fluxo de leitura para exibição

#### Scenario: RG com ausência registrada não expõe guidance
- **WHEN** o usuário lê um Relatório Gerencial cuja entrada no ledger registra ausência de guidance
- **THEN** o sistema NÃO DEVE disponibilizar item de guidance para exibição

#### Scenario: Guidance exposto é o do RG lido, não o corrente
- **WHEN** o ledger tem guidance de um RG mais recente e o usuário lê um RG anterior com guidance registrado
- **THEN** o guidance disponibilizado DEVE ser o do RG lido

#### Scenario: RG avaliado não é reavaliado para exibição
- **WHEN** o usuário lê um Relatório Gerencial já avaliado pelo mesmo método
- **THEN** o sistema NÃO DEVE reavaliar nem alterar o ledger, reutilizando a entrada existente para exibição

#### Scenario: Lote propaga a avaliação para a recomposição
- **WHEN** o lote de resumos avalia o guidance de um Relatório Gerencial pendente
- **THEN** o resultado daquela avaliação DEVE ser propagado junto do resumo para a recomposição da pré-visualização
