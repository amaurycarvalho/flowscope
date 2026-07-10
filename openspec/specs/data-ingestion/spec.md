## ADDED Requirements

### Requirement: Download de arquivos consolidados via API B3 two-step
O sistema DEVE baixar arquivos TradeInformationConsolidated da B3 usando o fluxo two-step: (1) GET para `api/download/requestname?fileName=...&date=...` obtendo token, (2) GET para `api/download/?token=` para download efetivo do CSV.

#### Scenario: Download bem-sucedido de um arquivo
- **WHEN** o sistema solicita o arquivo da data `2026-06-25` com nome `TradeInformationConsolidated`
- **THEN** o CSV correspondente DEVE ser baixado e salvo no diretório de cache local

#### Scenario: Data sem arquivo disponível
- **WHEN** a API B3 retorna erro para uma data solicitada (ex: feriado, fim de semana)
- **THEN** o sistema DEVE registrar o erro e continuar com as demais datas da janela, não interrompendo o processamento

### Requirement: Janela temporal com offsets de Fibonacci

O sistema DEVE calcular as datas de download usando offsets de Fibonacci a partir da data de referência, **parametrizável por período e método de amostragem configurados pelo usuário**. A configuração padrão (período=30, método=Fibonacci) mantém o comportamento atual: d-1, d-2, d-3, d-5, d-8, d-13, d-21. Outras combinações de período e método produzem diferentes conjuntos de datas conforme definido no capability `sampling-strategy`.

#### Scenario: Cálculo da janela a partir de uma data de referência (configuração padrão)
- **WHEN** a data de referência é `2026-06-26` (sexta-feira), período=30 e amostragem=Fibonacci
- **THEN** as datas calculadas DEVEM ser: 2026-06-25, 2026-06-24, 2026-06-23, 2026-06-22, 2026-06-18, 2026-06-15, 2026-06-05 (considerando apenas dias úteis)

#### Scenario: Cálculo com período=60 e Fibonacci
- **WHEN** a data de referência é `2026-06-26`, período=60 e amostragem=Fibonacci
- **THEN** as datas DEVEM incluir também d-34 e d-55 em relação à data de referência (além dos 7 offsets padrão)

#### Scenario: Data calculada cai em fim de semana
- **WHEN** um offset produz uma data que é sábado ou domingo
- **THEN** o sistema DEVE avançar para a próxima data até encontrar um dia útil (segunda a sexta), sem recalcular os demais offsets

### Requirement: Cache-only para períodos acima de 30 dias

O sistema DEVE, quando o período selecionado for maior que 30 dias, utilizar apenas dados do cache local para todas as datas, sem realizar requisições HTTP à B3.

#### Scenario: Período 60 dias sem cache não baixa dados
- **WHEN** período=60 e o cache não contém dados para as datas calculadas
- **THEN** o sistema DEVE pular as datas sem cache e retornar apenas os dados disponíveis, sem fazer download

### Requirement: Ajuste de data para cache disponível

O sistema DEVE, para cada data calculada em modo cache-only (período > 30), buscar no cache a data mais próxima dentro de uma margem de ±7 dias corridos. Se uma data alternativa for encontrada, deve substituir a data original. Se nenhuma data for encontrada dentro da margem, a data DEVE ser pulada.

#### Scenario: Data exata encontrada no cache
- **WHEN** a data calculada ref_date - 55 está presente no cache
- **THEN** o sistema DEVE usar ref_date - 55 sem ajustes

#### Scenario: Data aproximada encontrada no cache
- **WHEN** ref_date - 55 não está no cache, mas ref_date - 52 está (dentro de ±7 dias)
- **THEN** o sistema DEVE usar ref_date - 52 como substituta

#### Scenario: Nenhuma data próxima no cache
- **WHEN** ref_date - 55 não está no cache e nenhuma data dentro de ±7 dias está disponível
- **THEN** o sistema DEVE pular esta data e continuar com as demais

### Requirement: Deduplicação da lista final de datas

O sistema DEVE remover datas duplicadas do conjunto final, mantendo apenas uma ocorrência de cada data na lista ordenada.

#### Scenario: Datas duplicadas removidas
- **WHEN** o ajuste ao próximo dia útil faz duas datas diferentes colapsarem para a mesma data (ex: sábado e domingo ajustam para segunda)
- **THEN** a data DEVE aparecer apenas uma vez na lista final de datas a serem consultadas

### Requirement: Substituição de datas sem trades (pós-resolução ticker-aware)

Após o download dos trades, cada data de amostragem DEVE ser verificada contra os dados reais dos tickers analisados. Se nenhum ticker analisado tiver negociado em uma data de amostragem, a data DEVE ser substituída pela data mais próxima (d±1..d±7, dias úteis não repetidos) onde pelo menos um ticker tenha negociado.

A substituição DEVE ocorrer antes da execução do motor de indicadores, para que gráficos (ex: Evolução da Dominância) exibam todas as datas de amostragem com indicadores computados.

#### Scenario: Data de amostragem sem trades substituída
- **WHEN** uma data de amostragem d não possui trades de nenhum ticker analisado
- **AND** d+1 possui trades de pelo menos um ticker analisado
- **THEN** o sistema DEVE substituir d por d+1 na lista de datas de amostragem
- **AND** o motor de indicadores DEVE computar indicadores para d+1

#### Scenario: Data sem trades mantida se não houver substituta
- **WHEN** uma data de amostragem d não possui trades de nenhum ticker analisado
- **AND** nenhuma data em d±1..d±7 possui trades de nenhum ticker analisado
- **THEN** o sistema DEVE manter d na lista (como fallback, resultando em linha vazia no CSV)

### Requirement: Cache local de CSVs
O sistema DEVE manter cache local dos arquivos CSV baixados no diretório apropriado da plataforma: `~/.cache/flowscope/` (Linux), `%LOCALAPPDATA%/flowscope/cache/` (Windows), `~/Library/Caches/flowscope/` (macOS). Os arquivos DEVEM ser nomeados como `YYYY-MM-DD.csv`.

#### Scenario: Cache hit — arquivo já existe
- **WHEN** o sistema precisa do CSV da data `2026-06-25` e ele já existe no cache
- **THEN** o sistema DEVE usar o arquivo cacheado sem fazer nova requisição HTTP

#### Scenario: Cache miss — data de referência mudou
- **WHEN** a data de referência é alterada e arquivos de novas datas são necessários
- **THEN** o sistema DEVE baixar apenas os arquivos faltantes, mantendo os já existentes no cache

### Requirement: Parsing de CSV TradeInformationConsolidated
O sistema DEVE fazer parsing dos arquivos CSV da B3 utilizando o delimitador `;`, extraindo as colunas: RptDt, TckrSymb, SgmtNm, MinPric, MaxPric, TradAvrgPric, LastPric, TradQty, NtlFinVol, FinInstrmQty.

#### Scenario: Parsing de arquivo CSV válido
- **WHEN** um CSV consolidado é lido
- **THEN** cada linha DEVE produzir uma entidade de domínio com os campos mapeados para tipos Python apropriados (data como `date`, preços como `Decimal` ou `float`, volumes como `int`)

#### Scenario: CSV com linha de cabeçalho inválida ou ausente
- **WHEN** o parser encontra um CSV sem o cabeçalho esperado ou com formato inválido
- **THEN** o sistema DEVE lançar uma exceção específica de parsing com mensagem descritiva em português

### Requirement: Download da carteira de qualquer índice via API B3 (substitui "Download da carteira do IDIV via API B3")

O sistema DEVE baixar a composição da carteira teórica de **qualquer índice da B3** usando o endpoint `GetDownloadPortfolioDay` com token base64 construído a partir de `{"index":"<INDEX>","language":"pt-br"}`. O retorno DEVE ser parseado para extrair a lista de tickers (coluna `Código`), ignorando cabeçalho, rodapé e linhas de totalização, independentemente do nome do índice.

#### Scenario: Download bem-sucedido de IBOV
- **WHEN** o sistema solicita a carteira IBOV
- **THEN** uma lista de strings com os tickers DEVE ser retornada (ex: `["VALE3", "PETR4", "ITUB4", ...]`)

#### Scenario: Download bem-sucedido de IFIX
- **WHEN** o sistema solicita a carteira IFIX
- **THEN** uma lista de strings com os tickers DEVE ser retornada (ex: `["KINP11", "HGLG11", "KNRI11", ...]`)

#### Scenario: Falha no download de índice inexistente
- **WHEN** o sistema solicita um índice que não existe na B3
- **THEN** o sistema DEVE retornar uma lista vazia sem interromper o fluxo principal

### Requirement: Cache da carteira por índice com TTL (substitui "Cache da carteira IDIV com TTL")

O sistema DEVE manter um cache local independente para **cada índice** (IBOV, IDIV, IFIX, etc.) com TTL de 7 dias. A chave de cache DEVE ser `portfolio_{index}`. Cada índice DEVE ter seu próprio timestamp de expiração.

#### Scenario: Cache válido para IBOV
- **WHEN** a carteira IBOV foi baixada há menos de 7 dias
- **THEN** o sistema DEVE retornar os tickers do cache sem fazer nova requisição HTTP

#### Scenario: Cache expirado para IFIX (mas IDIV ainda válido)
- **WHEN** a carteira IFIX foi baixada há mais de 7 dias, mas IDIV foi baixada há 2 dias
- **THEN** o sistema DEVE buscar IFIX novamente da API e usar o cache para IDIV

### Requirement: Filtro por segmento CASH no parser

O sistema DEVE filtrar as linhas do CSV TradeInformationConsolidado para manter apenas aquelas onde `SgmtNm == "CASH"`, descartando linhas de outros segmentos (BMF, FUTURE, etc.). Este filtro DEVE ser aplicado durante o parsing.

#### Scenario: Parsing com filtro CASH
- **WHEN** um CSV contém linhas com `SgmtNm` igual a "CASH", "BMF" e "FUTURE"
- **THEN** apenas as linhas com `SgmtNm == "CASH"` DEVEM ser incluídas no resultado
