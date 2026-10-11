## MODIFIED Requirements

### Requirement: Avaliação de guidance no processamento em lote dos pendentes

Ao processar documentos pelo botão "Resumir pendentes" da sub-aba "Documentos", o sistema DEVE avaliar o guidance dos documentos da categoria `Relatorio`, aplicando o controle de avaliação uma vez por método e a cascata de fontes, reaproveitando os resumos e o texto já preparado, sem reextrair o arquivo. Para os Relatórios Gerenciais pendentes de resumo, a avaliação DEVE ocorrer após a geração do resumo de cada item. Com a IA ativa, o lote DEVE também mirar os Relatórios Gerenciais (documentos da categoria `Relatorio`, própria de FII) já resumidos cuja avaliação de guidance seja acionável: entrada ausente no ledger, ou marcada como `deterministico` com a IA funcional e sem falha de interação registrada; para esses, a geração de resumo DEVE ser pulada e somente a avaliação de guidance DEVE executar. A avaliação NÃO DEVE interromper o processamento em lote nem marcar a entrada como `ia` quando a interação com a IA falhar, mas a falha DEVE ser registrada de modo que a decisão de pendência seguinte distinga "IA tentou e falhou" de "IA nunca tentou", e DEVE ser reportada no desfecho do lote. O lote NÃO DEVE avaliar guidance de documentos de outra categoria.

#### Scenario: Relatório pendente de resumo dispara avaliação
- **WHEN** o usuário aciona "Resumir pendentes" e um Relatório Gerencial pendente de resumo ainda não foi avaliado
- **THEN** o sistema DEVE avaliá-lo pela cascata após gerar o resumo, reaproveitando os resumos e o texto preparado

#### Scenario: Relatório já resumido pendente de guidance dispara avaliação
- **WHEN** o usuário aciona "Resumir pendentes", a IA está ativa, e um Relatório Gerencial já resumido tem avaliação de guidance acionável
- **THEN** o sistema DEVE avaliá-lo pela IA sem regerar o resumo, reaproveitando os resumos e o texto em cache

#### Scenario: Documento não pendente é ignorado
- **WHEN** um Relatório Gerencial já possui resumo e entrada de guidance marcada como `ia`
- **THEN** o lote NÃO DEVE avaliar seu guidance

#### Scenario: RG com falha de IA registrada não é alvo enquanto não reabilitado
- **WHEN** um Relatório Gerencial já resumido tem entrada `deterministico` com falha de interação de IA registrada
- **THEN** o lote NÃO DEVE mirá-lo por guidance até que a avaliação seja reabilitada

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

#### Scenario: Falha de avaliação é reportada no desfecho
- **WHEN** a avaliação de guidance de um Relatório falha durante o lote
- **THEN** a falha DEVE ser registrada e reportada no desfecho do lote

### Requirement: Avaliação uma vez por método

Para cada Relatório Gerencial, o sistema DEVE avaliar no máximo uma vez por método. Quando a entrada do RG no ledger estiver marcada como `ia`, nenhuma nova avaliação DEVE ocorrer. Quando estiver marcada como `deterministico` e a IA estiver disponível, o sistema DEVE avaliar pela IA e substituir a entrada (a IA prevalece sobre o determinístico). Quando estiver marcada como `deterministico` e a IA não estiver disponível, nenhuma nova avaliação DEVE ocorrer. Uma falha na interação com a IA NÃO DEVE marcar a entrada como `ia`, DEVE preservar o resultado determinístico existente e DEVE ser registrada de modo que a decisão de pendência seguinte distinga "IA tentou e falhou" de "IA nunca tentou". Uma entrada determinística com falha de interação registrada NÃO DEVE manter o botão "Resumir pendentes" habilitado indefinidamente; o RG volta a ser acionável quando a avaliação for autorizada novamente (por reconfiguração da IA, por uma nova sessão de uso, ou quando uma nova avaliação por IA concluir com sucesso).

#### Scenario: RG já avaliado por IA não é reavaliado
- **WHEN** a entrada do RG já está marcada como `ia` e o documento é processado novamente
- **THEN** o sistema NÃO DEVE avaliar nem alterar o ledger do RG

#### Scenario: RG determinístico é reavaliado pela IA quando disponível
- **WHEN** a entrada do RG está marcada como `deterministico`, a IA está funcional e não há falha de interação registrada
- **THEN** o sistema DEVE avaliar pela IA e substituir a entrada do RG, prevalecendo a IA

#### Scenario: RG determinístico não é reavaliado sem IA
- **WHEN** a entrada do RG está marcada como `deterministico` e a IA não está disponível
- **THEN** o sistema NÃO DEVE avaliar nem alterar o ledger do RG

#### Scenario: Falha da IA preserva a entrada e permite nova tentativa
- **WHEN** a interação com a IA falha ao avaliar um RG
- **THEN** a entrada NÃO DEVE ser marcada como `ia`, DEVE manter o resultado determinístico e DEVE registrar a falha da interação, distinguindo-a de "IA nunca tentou"

#### Scenario: Falha repetida não mantém a pendência acionável
- **WHEN** a avalição por IA de um RG determinístico falhou e o usuário reexecuta "Resumir pendentes" sem que a IA tenha se recuperado
- **THEN** o RG NÃO DEVE contar como pendência acionável que mantenha o botão habilitado

#### Scenario: RG volta a ser acionável quando a IA se recupera
- **WHEN** a IA volta a responder com sucesso para um RG cuja entrada estava determinística com falha registrada
- **THEN** o sistema DEVE substituir a entrada pela avaliação por IA

#### Scenario: Reconfiguração da IA reabilita a avaliação
- **WHEN** o usuário reconfigura o provedor de IA e há RG determinístico com falha registrada
- **THEN** o RG DEVE voltar a ser acionável para nova avaliação por IA
