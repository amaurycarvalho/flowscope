## Purpose

Extrair dividendos de BDRs a partir do Plantão de Notícias da B3 e dos PDFs de `Aviso aos Acionistas` da CVM, para preencher data-com, último dividendo, dividendo anterior, tendência, P/L, Dividend Yield, caminho de cache e identidade fiscal na tabela de Fundamentos quando o Fundamentus não cobre o ativo.

## ADDED Requirements

### Requirement: Listagem de avisos aos acionistas de BDR por período

O sistema DEVE obter os avisos aos acionistas de um BDR consultando o Plantão de Notícias da B3 por janelas mensais (no máximo um mês por requisição) ao longo dos últimos 12 meses, usando a raiz do ticker (dígitos removidos) como palavra-chave. O sistema DEVE considerar apenas os itens cujo título contenha a raiz do ticker entre parênteses e o termo `Aviso aos Acionistas`. A ausência de avisos no período DEVE resultar em lista vazia, distinta de falha de aquisição.

#### Scenario: Avisos encontrados no mês
- **WHEN** o Plantão de Notícias retorna itens com título `EXXON MOBIL (EXXO) - Aviso aos Acionistas - 11/09/26` para a raiz `EXXO`
- **THEN** o sistema DEVE retornar esses itens como avisos aos acionistas do BDR

#### Scenario: Item de outra empresa com a mesma raiz
- **WHEN** o Plantão retorna `DEXXOS PAR (DEXP-N1) - Fato Relevante` para a palavra-chave `EXXO`
- **THEN** o item NÃO DEVE ser considerado um aviso do BDR `EXXO34`

#### Scenario: Mês sem avisos
- **WHEN** a janela mensal não retorna itens de `Aviso aos Acionistas` para o BDR
- **THEN** o sistema DEVE continuar para a janela seguinte, sem erro

#### Scenario: Falha de aquisição em uma janela
- **WHEN** a consulta de uma janela mensal falha por indisponibilidade
- **THEN** o sistema DEVE registrar a falha e continuar as demais janelas, sem interromper a análise de outros tickers

### Requirement: Download e cache dos PDFs de aviso

O sistema DEVE, para cada aviso, resolver o documento vinculado na página de detalhe e baixá-lo como PDF a partir do visualizador da CVM, validando que o conteúdo começa com `%PDF`. O PDF DEVE ser cacheado em disco em uma pasta por ticker, com subpasta de ano e subpasta de mês (`<cache>/bdr/<TICKER>/<AAAA>/<MM>/<id>.pdf`). O cache NÃO DEVE expirar; quando o arquivo já existir, o sistema DEVE reutilizá-lo sem novo download. Quando o download falhar e existir arquivo em cache, o sistema DEVE usar o cache; sem cache, DEVE sinalizar indisponibilidade para aquele aviso.

#### Scenario: PDF novo é baixado e cacheado
- **WHEN** um aviso ainda não tem PDF em cache e o download retorna conteúdo iniciado por `%PDF`
- **THEN** o sistema DEVE gravar o arquivo em `<cache>/bdr/<TICKER>/<AAAA>/<MM>/<id>.pdf`

#### Scenario: PDF já em cache
- **WHEN** o arquivo do aviso já existe no cache
- **THEN** o sistema DEVE reutilizá-lo sem realizar novo download

#### Scenario: Conteúdo não é PDF
- **WHEN** o download não retorna conteúdo iniciado por `%PDF`
- **THEN** o aviso DEVE ser ignorado, sem interromper os demais

#### Scenario: Falha de rede com cache disponível
- **WHEN** o download falha e existe arquivo em cache para o aviso
- **THEN** o sistema DEVE usar o conteúdo armazenado

### Requirement: Extração de dividendos do texto do PDF

O sistema DEVE extrair do texto do PDF do aviso, quando presentes, o valor do dividendo por BDR em reais, a data-com, a data de pagamento e o tipo do evento (dividendo ou juros sobre capital próprio), além do código ISIN, do nome do depositário e do nome da empresa. Cada aviso extraído DEVE ser normalizado em um dividendo com data-base e valor por unidade e origem BDR. Avisos cujo texto não permita extrair valor e data-com DEVEM ser ignorados.

#### Scenario: Aviso de dividendo com valor por BDR
- **WHEN** o texto informa `pagamento do(a) Dividendos no valor de USD 1,030000000 ... corresponde a um valor prévio de R$ 0,455484428 por BDR` e `titulares de BDRs em 10/02/2026`
- **THEN** o sistema DEVE extrair valor por BDR `0,455484428` e data-com `10/02/2026`

#### Scenario: Tipo do evento
- **WHEN** o texto informa `Juros sobre Capital Próprio` ou `Dividendos`
- **THEN** o sistema DEVE registrar o tipo do evento correspondente

#### Scenario: Aviso sem valor extraível
- **WHEN** o texto não contém valor por BDR nem data-com reconhecíveis
- **THEN** o aviso DEVE ser ignorado, sem impedir os demais

### Requirement: P/L e Dividend Yield de BDR com anualização trimestral

O sistema DEVE calcular o P/L de um BDR como `Cotação / (último dividendo × 4)` e o Dividend Yield como `(último dividendo × 4) / Cotação`, anualizando o dividendo trimestral. O sistema DEVE exibir `N/A` quando o último dividendo ou a cotação estiverem ausentes ou quando a cotação for zero. Para BDR, o sistema NÃO DEVE aplicar a anualização mensal (×12) usada para FIIs.

#### Scenario: P/L de BDR calculado
- **WHEN** a cotação é `10,00` e o último dividendo trimestral é `0,50`
- **THEN** o P/L DEVE ser `10,00 / (0,50 × 4) = 5,00`

#### Scenario: Dividend Yield de BDR calculado
- **WHEN** a cotação é `10,00` e o último dividendo trimestral é `0,50`
- **THEN** o Dividend Yield DEVE ser `(0,50 × 4) / 10,00 = 0,20` (20,0%)

#### Scenario: Insumo ausente
- **WHEN** o último dividendo ou a cotação do BDR não está disponível
- **THEN** o P/L e o Dividend Yield DEVEM ser `N/A`

#### Scenario: Cotação zero
- **WHEN** a cotação do BDR é zero
- **THEN** o P/L e o Dividend Yield DEVEM ser `N/A`

### Requirement: Exposição do caminho de cache e da identidade fiscal de BDR

O sistema DEVE expor, para BDRs, o caminho da pasta de cache dos PDFs em `Informações adicionais`. Quando `Dados fiscais` não tiver CNPJ nem administrador/gestor, o sistema DEVE exibir o nome do depositário, o nome da empresa e o código ISIN extraídos dos avisos, omitindo os itens que não puderem ser obtidos.

#### Scenario: Caminho de cache exibido
- **WHEN** um BDR possui PDFs de aviso em cache
- **THEN** a coluna `Informações adicionais` DEVE exibir o caminho da pasta de cache do ticker

#### Scenario: Identidade fiscal de BDR a partir dos avisos
- **WHEN** o BDR não possui CNPJ/administrador/gestor nas fontes primárias e o aviso informa `Banco B3 S.A.`, `Exxon Mobil Corporation` e `BREXXOBDR006`
- **THEN** `Dados fiscais` DEVE exibir depositário, empresa e ISIN

#### Scenario: Item indisponível
- **WHEN** um dos itens de identidade fiscal do BDR não está disponível
- **THEN** o item DEVE ser omitido, sem impedir os demais

### Requirement: Isolamento e não interferência em ativos não-BDR

A fonte de dividendos de BDR DEVE ser acionada apenas para ativos classificados como BDR. Para os demais ativos, o comportamento existente DEVE ser preservado. A falha da fonte de BDR para um ticker NÃO DEVE interromper a análise dos demais tickers.

#### Scenario: Ativo não-BDR não aciona a fonte
- **WHEN** um FII ou uma ação é analisado
- **THEN** a fonte de dividendos de BDR NÃO DEVE ser consultada

#### Scenario: Falha isolada por ticker
- **WHEN** a extração de dividendos de um BDR falha
- **THEN** os demais tickers DEVEM continuar sendo processados normalmente
