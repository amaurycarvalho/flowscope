## Purpose

Interromper o lote de resumo de documentos e notícias de forma imediata e legível quando o provedor de IA esgota a cota ou o limite de requisições, preservando o trabalho já gravado e mantendo os itens restantes pendentes.

## ADDED Requirements

### Requirement: Interrupção do lote por cota esgotada

Quando a geração de resumo em lote encontra `LLMRateLimitError` (limite/cota do provedor de IA excedido), o sistema DEVE interromper o lote imediatamente, independentemente da política de continuidade por item, sem iniciar a geração para os itens seguintes. Os resumos já gravados DEVEM ser preservados e os itens não processados DEVEM permanecer pendentes para nova tentativa. O desfecho DEVE ser reportado uma única vez, com mensagem que distinga a cota/limite da IA das demais falhas.

#### Scenario: Lote contínuo interrompe em cota esgotada
- **WHEN** o lote contínuo de Notícias encontra `LLMRateLimitError` em um item
- **THEN** o lote NÃO DEVE processar os itens seguintes e DEVE encerrar reportando a cota esgotada

#### Scenario: Resumos já gerados são preservados
- **WHEN** o lote é interrompido por cota esgotada após gerar resumos de alguns itens
- **THEN** os resumos já gravados DEVEM permanecer no cache persistente

#### Scenario: Itens não processados permanecem pendentes
- **WHEN** o lote é interrompido por cota esgotada
- **THEN** os itens não processados DEVEM continuar pendentes e elegíveis a um novo lote quando a cota for restabelecida

#### Scenario: Desfecho único
- **WHEN** o lote é interrompido por cota esgotada
- **THEN** a barra de status DEVE reportar a cota esgotada uma única vez, sem um reporte por item

### Requirement: Registro conciso da cota esgotada

A cota esgotada durante o lote DEVE ser registrada em log uma única vez, em nível de aviso e sem traceback por item. As demais falhas mantêm o comportamento de registro vigente.

#### Scenario: Sem traceback por item
- **WHEN** o lote encontra `LLMRateLimitError`
- **THEN** o log DEVE conter um único aviso de cota esgotada, sem o traceback repetido de cada item

### Requirement: Mensagem de cota orienta a espera ou a reconfiguração

A mensagem apresentada ao usuário para `LLMRateLimitError` DEVE indicar que a cota/limite da IA foi atingido e orientar aguardar a renovação ou reconfigurar o provedor de IA, distinguindo-se da mensagem de erro genérico do provedor.

#### Scenario: Mensagem distinta de erro de provedor
- **WHEN** a falha do lote é `LLMRateLimitError`
- **THEN** a mensagem exibida DEVE mencionar o limite de uso da IA e a possibilidade de aguardar a renovação ou reconfigurar o provedor
