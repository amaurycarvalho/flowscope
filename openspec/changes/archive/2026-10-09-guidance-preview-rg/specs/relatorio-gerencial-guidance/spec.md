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

## MODIFIED Requirements

### Requirement: Avaliação de guidance no processamento em lote dos pendentes

Ao processar documentos pelo botão "Resumir pendentes" da sub-aba "Documentos", o sistema DEVE avaliar o guidance dos documentos da categoria `Relatorio`, aplicando o controle de avaliação uma vez por método e a cascata de fontes, reaproveitando os resumos e o texto já preparado, sem reextrair o arquivo. Para os Relatórios Gerenciais pendentes de resumo, a avaliação DEVE ocorrer após a geração do resumo de cada item. Com a IA ativa, o lote DEVE também mirar os Relatórios Gerenciais (documentos da categoria `Relatorio`, própria de FII) já resumidos cuja entrada no ledger esteja ausente ou não marcada como `ia`; para esses, a geração de resumo DEVE ser pulada e somente a avaliação de guidance DEVE executar. A avaliação NÃO DEVE interromper o processamento em lote nem marcar a entrada quando a interação com a IA falhar. O lote NÃO DEVE avaliar guidance de documentos de outra categoria.

#### Scenario: Relatório pendente de resumo dispara avaliação
- **WHEN** o usuário aciona "Resumir pendentes" e um Relatório Gerencial pendente de resumo ainda não foi avaliado
- **THEN** o sistema DEVE avaliá-lo pela cascata após gerar o resumo, reaproveitando os resumos e o texto preparado

#### Scenario: Relatório já resumido pendente de guidance dispara avaliação
- **WHEN** o usuário aciona "Resumir pendentes", a IA está ativa, e um Relatório Gerencial já resumido tem entrada de guidance ausente ou não marcada como `ia`
- **THEN** o sistema DEVE avaliá-lo pela IA sem regerar o resumo, reaproveitando os resumos e o texto em cache

#### Scenario: Documento não pendente é ignorado
- **WHEN** um Relatório Gerencial já possui resumo e entrada de guidance marcada como `ia`
- **THEN** o lote NÃO DEVE avaliar seu guidance

#### Scenario: Sem IA, RG já resumido não é alvo por guidance
- **WHEN** um Relatório Gerencial já resumido não possui entrada de guidance e a IA não está disponível
- **THEN** o lote NÃO DEVE mirá-lo por guidance

#### Scenario: Documento de outra categoria é ignorado
- **WHEN** um documento pendente de resumo não é da categoria `Relatorio`
- **THEN** o lote NÃO DEVE avaliar guidance

#### Scenario: Documento sem texto extraível é ignorado
- **WHEN** um Relatório pendente de resumo não possui resumos nem texto extraível
- **THEN** o lote NÃO DEVE avaliar guidance nem alterar o ledger

#### Scenario: Falha na avaliação não interrompe o lote
- **WHEN** a avaliação de guidance de um Relatório falha
- **THEN** o processamento em lote DEVE continuar, sem propagar a exceção
