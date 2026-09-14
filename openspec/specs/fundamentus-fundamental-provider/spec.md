# fundamentus-fundamental-provider Specification

## Purpose
Extração e normalização determinística dos dados fundamentalistas de ações e FIIs a partir do portal Fundamentus, entregando um modelo tipado com indicadores, balanço, demonstrativos e dados específicos de FII para consumo pela análise fundamentalista.

## Requirements

### Requirement: Extração de dados fundamentalistas por ticker

O sistema DEVE obter os dados de um ticker a partir de `detalhes.php?papel={TICKER}` e retornar um modelo tipado com identidade (ticker, nome, discriminador do rótulo de ticker `Papel`/`FII`, espécie `Tipo`, `Setor`, `Subsetor`, `Segmento`, `Gestão`), cotação e data da última cotação, oscilações, indicadores, balanço, demonstrativos de 12 e 3 meses e, para FIIs, dados de imóveis e composição de ativos.

#### Scenario: Dados de uma ação
- **WHEN** o ticker é uma ação válida
- **THEN** o sistema DEVE retornar o modelo com discriminador `Papel`, `Tipo` (espécie), `Setor` e `Subsetor` preenchidos quando presentes

#### Scenario: Dados de um FII
- **WHEN** o ticker é um FII válido
- **THEN** o sistema DEVE retornar o modelo com discriminador `FII`, `Segmento`, `Gestão` e `Qtd imóveis` preenchidos quando presentes

### Requirement: Detecção automática do tipo de ativo

O sistema DEVE identificar automaticamente se o ticker é FII ou ação a partir do rótulo do campo de ticker (`Papel` ou `FII`) presente na página, sem exigir configuração do chamador.

#### Scenario: Layout de FII reconhecido
- **WHEN** o campo do ticker tem rótulo `FII`
- **THEN** o sistema DEVE classificar o ativo como FII

#### Scenario: Layout de ação reconhecido
- **WHEN** o campo do ticker tem rótulo `Papel`
- **THEN** o sistema DEVE classificar o ativo como ação (não-FII)

### Requirement: Balizador Tijolo/Papel por Qtd imóveis

O sistema DEVE expor o campo `Qtd imóveis` do bloco de imóveis para que o consumidor determine se um FII é de tijolo (`Qtd imóveis > 0`) ou de papel (`Qtd imóveis` ausente ou igual a zero).

#### Scenario: FII de tijolo
- **WHEN** o FII possui `Qtd imóveis` maior que zero
- **THEN** o campo DEVE indicar quantidade positiva de imóveis

#### Scenario: FII de papel
- **WHEN** o FII possui `Qtd imóveis` igual a zero ou ausente
- **THEN** o campo DEVE indicar zero ou ausência

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

### Requirement: Revalidação condicional do snapshot do Fundamentus

O sistema DEVE revalidar o snapshot em cache usando a `Data últ cot` como validador primário e validadores HTTP (`ETag`/`Last-Modified`) como secundários, servindo o cache sem reprocessar quando o snapshot não avançou.

#### Scenario: Data de cotação inalterada

- **WHEN** a `Data últ cot` obtida da fonte não é posterior à armazenada
- **THEN** o sistema DEVE servir o cache e atualizar apenas os metadados de revalidação

#### Scenario: Data de cotação nova

- **WHEN** a `Data últ cot` obtida da fonte é posterior à armazenada
- **THEN** o sistema DEVE substituir o snapshot em cache

#### Scenario: Resposta 304 Not Modified

- **WHEN** o servidor responde `304 Not Modified` a uma requisição condicional
- **THEN** o sistema DEVE servir o cache sem reprocessar o HTML

#### Scenario: Ausência de validadores HTTP

- **WHEN** a fonte não fornece `ETag` nem `Last-Modified`
- **THEN** o sistema DEVE realizar a aquisição completa e comparar a `Data últ cot`

### Requirement: Coalescência de requisições e TTL de segurança

O sistema DEVE limitar a frequência de checagens remotas por ticker e DEVE forçar uma atualização completa após um intervalo máximo de segurança, mesmo quando a data de cotação não muda.

#### Scenario: Chamadas repetidas dentro do intervalo

- **WHEN** o mesmo ticker é consultado novamente antes de vencer o intervalo mínimo de revalidação
- **THEN** o sistema DEVE servir o cache sem nova requisição

#### Scenario: TTL de segurança vencido

- **WHEN** o tempo desde a última atualização excede o intervalo máximo de segurança
- **THEN** o sistema DEVE refazer a aquisição completa mesmo com a data inalterada

### Requirement: Cache versionado por parser

O sistema DEVE vincular o cache do Fundamentus à versão do parser, de modo que uma mudança de versão invalide os snapshots anteriores.

#### Scenario: Versão do parser alterada

- **WHEN** a versão do parser difere da versão registrada no cache
- **THEN** o snapshot anterior DEVE ser ignorado e a fonte consultada novamente

### Requirement: Invalidação explícita por ticker

O sistema DEVE permitir forçar a atualização de um ticker, ignorando o cache.

#### Scenario: Atualização forçada

- **WHEN** a atualização é solicitada com `force_refresh`
- **THEN** o sistema DEVE consultar a fonte e substituir o cache, independentemente da validade do snapshot armazenado

### Requirement: Resultado do cache reportado ao consumidor

O sistema DEVE reportar, para cada consulta, se o snapshot foi servido do cache, revalidado ou atualizado, permitindo que a apresentação informe a atualização de dados.

#### Scenario: Atualização de dados sinalizada

- **WHEN** o snapshot de um ticker é atualizado a partir da fonte
- **THEN** o resultado DEVE indicar atualização para que a interface possa exibir "Dados atualizados"

### Requirement: Exposição do campo VP/Cota

O sistema DEVE expor o valor patrimonial por cota/ação na composição de campos fundamentalistas consumida pela análise fundamentalista. Para FIIs, DEVE usar o indicador `VP/Cota`; para ações, DEVE usar o indicador `VPA` (valor patrimonial por ação) quando `VP/Cota` estiver ausente. O campo exposto DEVE ser `vp_cota` com o valor normalizado.

#### Scenario: VP/Cota disponível
- **WHEN** a página do FII contém o indicador `VP/Cota`
- **THEN** o campo `vp_cota` DEVE ser exposto com o valor normalizado

#### Scenario: VPA disponível para ação
- **WHEN** a página da ação contém o indicador `VPA` e não contém `VP/Cota`
- **THEN** o campo `vp_cota` DEVE ser exposto com o valor do `VPA`

#### Scenario: VP/Cota ausente
- **WHEN** a página não contém o indicador `VP/Cota` nem `VPA`
- **THEN** o campo DEVE ser ausente, sem impedir a exposição dos demais campos

### Requirement: Exposição do indicador P/L

O sistema DEVE expor o indicador `P/L` do Fundamentus na composição de campos fundamentalistas consumida pela análise, quando presente na página, sem alterar a exposição dos demais indicadores.

#### Scenario: P/L disponível para ação
- **WHEN** a página de uma ação contém o indicador `P/L`
- **THEN** o campo `p_l` DEVE ser exposto com o valor normalizado

#### Scenario: P/L ausente
- **WHEN** a página não contém o indicador `P/L` (por exemplo, uma página de FII)
- **THEN** o campo DEVE ser ausente, sem impedir a exposição dos demais campos

### Requirement: Histórico de proventos por ticker

O sistema DEVE obter o histórico de proventos de um ticker a partir da página `proventos.php?papel={TICKER}`, normalizando cada linha em um dividendo com data-base (coluna `Data`), valor por unidade (coluna `Valor`) e origem Fundamentus. Linhas sem data ou sem valor DEVEM ser ignoradas. A ausência de proventos DEVE resultar em lista vazia, distinta de falha de aquisição.

#### Scenario: Histórico extraído para ação
- **WHEN** a página de proventos de uma ação contém linhas com `Data`, `Valor` e `Tipo`
- **THEN** o sistema DEVE retornar uma lista de dividendos com data-base e valor, preservando a origem Fundamentus

#### Scenario: Tipos de provento de ação
- **WHEN** uma linha tem `Tipo` igual a `DIVIDENDO`, `DIVIDENDO MENSAL`, `JRS CAP PROPRIO` ou `JUROS`
- **THEN** o provento DEVE ser tratado como dividendo (rendimento), nunca como amortização

#### Scenario: Sem proventos
- **WHEN** a página não contém linhas de proventos
- **THEN** o sistema DEVE retornar lista vazia sem erro

#### Scenario: Falha de rede
- **WHEN** a requisição à página de proventos falha
- **THEN** o sistema DEVE sinalizar indisponibilidade, sem retornar dados parciais como se estivessem completos

### Requirement: Exposição de indicadores adicionais e de imóveis

O sistema DEVE expor na composição de campos fundamentalistas, quando presentes na página, os indicadores `LPA`, `ROE` e `ROIC` e os campos de imóveis `Cap Rate` e `Vacância Média` (além de `Qtd imóveis`), sem alterar a exposição dos demais campos.

#### Scenario: Indicadores de ação disponíveis
- **WHEN** a página de uma ação contém os indicadores `LPA`, `ROE` e `ROIC`
- **THEN** os campos correspondentes DEVEM ser expostos com os valores normalizados

#### Scenario: Indicadores de imóveis disponíveis
- **WHEN** a página de um FII contém `Cap Rate` e `Vacância Média`
- **THEN** os campos correspondentes DEVEM ser expostos com os valores normalizados

#### Scenario: Indicador ausente ou não numérico
- **WHEN** um indicador está ausente ou contém `-`
- **THEN** o campo correspondente DEVE ser ausência de valor, sem impedir os demais

### Requirement: Exposição dos demonstrativos de Receita e Rend. Distribuído

O sistema DEVE expor, na composição de campos fundamentalistas consumida pela análise, a `Receita` e o `Rend. Distribuído` dos demonstrativos de 12 e 3 meses, normalizados em `Decimal`. A `Receita` DEVE usar o rótulo `Receita` e, na sua ausência, `Receita Líquida`. O `Rend. Distribuído` DEVE ser tratado como Dividendos no cálculo das métricas. Campos ausentes DEVEM ser omitidos sem impedir a exposição dos demais.

#### Scenario: Receita disponível
- **WHEN** a página contém `Receita` nos demonstrativos de 12 e 3 meses
- **THEN** os campos de receita de 12m e 3m DEVEM ser expostos com os valores normalizados

#### Scenario: Receita Líquida como alternativa
- **WHEN** a página não contém `Receita` mas contém `Receita Líquida`
- **THEN** o campo de receita DEVE ser exposto com o valor de `Receita Líquida`

#### Scenario: Rend. Distribuído disponível
- **WHEN** a página contém `Rend. Distribuído` nos demonstrativos de 12 e 3 meses
- **THEN** os campos de rendimento distribuído de 12m e 3m DEVEM ser expostos com os valores normalizados

#### Scenario: Campo ausente
- **WHEN** a página não contém `Receita`, `Receita Líquida` nem `Rend. Distribuído`
- **THEN** os campos correspondentes DEVEM ser ausentes, sem impedir a exposição dos demais
