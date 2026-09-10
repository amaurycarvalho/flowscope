## Purpose

Extração e normalização determinística dos dados fundamentalistas de ações e FIIs a partir do portal Fundamentus, entregando um modelo tipado com indicadores, balanço, demonstrativos e dados específicos de FII para consumo pela análise fundamentalista.

## ADDED Requirements

### Requirement: Extração de dados fundamentalistas por ticker

O sistema DEVE obter os dados de um ticker a partir de `detalhes.php?papel={TICKER}` e retornar um modelo tipado com identidade (ticker, tipo, nome), cotação e data da última cotação, oscilações, indicadores, balanço, demonstrativos de 12 e 3 meses e, para FIIs, dados de imóveis e composição de ativos.

#### Scenario: Dados de uma ação
- **WHEN** o ticker é uma ação válida
- **THEN** o sistema DEVE retornar o modelo com `tipo` de ação, cotação, indicadores e demonstrativos preenchidos

#### Scenario: Dados de um FII
- **WHEN** o ticker é um FII válido
- **THEN** o sistema DEVE retornar o modelo com `tipo` de FII, indicadores de FII (FFO Yield, FFO/Cota, Dividendo/cota, VP/Cota) e dados de imóveis/composição quando disponíveis

### Requirement: Detecção automática do tipo de ativo

O sistema DEVE identificar automaticamente se o ticker é FII ou ação a partir do layout da página, sem exigir configuração do chamador.

#### Scenario: Layout de FII reconhecido
- **WHEN** a página contém os rótulos característicos de FII
- **THEN** o sistema DEVE classificar o ativo como FII

#### Scenario: Layout de ação reconhecido
- **WHEN** a página não contém os rótulos característicos de FII
- **THEN** o sistema DEVE classificar o ativo como ação

### Requirement: Normalização de números, percentuais e datas

O sistema DEVE normalizar valores textuais no formato brasileiro (ex.: `R$ 1.234,56`, `7,3%`, `-0,08%`) para tipos numéricos em `Decimal`, e datas para `date`, tratando células vazias ou `-` como ausência de valor.

#### Scenario: Valor monetário normalizado
- **WHEN** a célula contém `R$ 691.996.000.000`
- **THEN** o sistema DEVE retornar o valor decimal correspondente

#### Scenario: Percentual normalizado
- **WHEN** a célula contém `-0,08%`
- **THEN** o sistema DEVE retornar o valor decimal negativo correspondente

#### Scenario: Célula vazia
- **WHEN** a célula está vazia ou contém `-`
- **THEN** o sistema DEVE retornar ausência de valor (`None`)

### Requirement: Campos ausentes e fallback bruto

Campos não encontrados DEVEM ser retornados como ausência de valor, e o modelo DEVE preservar o mapeamento bruto rótulo→valor da página para diagnóstico e evolução do parser.

#### Scenario: Campo opcional ausente
- **WHEN** um FII não possui dados de imóveis
- **THEN** o campo correspondente DEVE ser ausência de valor sem impedir o restante do modelo

#### Scenario: Mapa bruto preservado
- **WHEN** uma página é parseada
- **THEN** o modelo DEVE expor o mapeamento bruto dos rótulos e valores coletados

### Requirement: Tratamento de erros de aquisição e layout

O sistema DEVE distinguir e sinalizar explicitamente: ticker inexistente, layout alterado (campos obrigatórios ausentes) e falha de rede, sem retornar dados parcialmente incorretos como se fossem válidos.

#### Scenario: Ticker inexistente
- **WHEN** a página indica que nenhum papel foi encontrado
- **THEN** o sistema DEVE sinalizar ticker não encontrado

#### Scenario: Layout alterado
- **WHEN** nome e cotação estão ambos ausentes
- **THEN** o sistema DEVE sinalizar layout alterado

#### Scenario: Falha de rede
- **WHEN** a requisição falha ou retorna status de erro
- **THEN** o sistema DEVE sinalizar erro de rede sem produzir um modelo inválido

### Requirement: Rate-limit e respeito ao robots.txt

O sistema DEVE limitar as requisições ao Fundamentus a no máximo uma por segundo por padrão e respeitar o `robots.txt` do portal.

#### Scenario: Requisições serializadas
- **WHEN** múltiplos tickers são consultados em sequência
- **THEN** o sistema DEVE espaçar as requisições respeitando o limite configurado

### Requirement: Testes de contrato com fixtures

O sistema DEVE manter fixtures HTML estáticas de ações e FIIs e testes de contrato que detectem quebras de layout, além de testes unitários dos normalizadores.

#### Scenario: Fixture de FII valida o parsing
- **WHEN** o parser é executado sobre a fixture de um FII
- **THEN** os valores esperados de cotação, indicadores e demonstrativos DEVEM ser extraídos

#### Scenario: Mudança de layout detectada
- **WHEN** a fixture perde um rótulo obrigatório
- **THEN** o teste de contrato DEVE falhar explicitamente
