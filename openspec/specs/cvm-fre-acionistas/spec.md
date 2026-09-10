# cvm-fre-acionistas Specification

## Purpose
Resolver a quantidade de acionistas de companhias abertas (Papel) a partir dos dados abertos da CVM, alimentando a coluna "Nº de cotistas" da tabela de Fundamentos.

## Requirements

### Requirement: Aquisição da quantidade de acionistas do FRE

O sistema DEVE obter a quantidade de acionistas de uma companhia aberta a partir do dataset anual do Formulário de Referência (FRE), arquivo `fre_cia_aberta_distribuicao_capital_<ano>.csv`, filtrando pelo CNPJ da companhia e somando as quantidades de acionistas pessoa física, pessoa jurídica e investidores institucionais.

#### Scenario: Companhia com registros no FRE
- **WHEN** o CNPJ da companhia possui registro em `distribuicao_capital`
- **THEN** a quantidade total de acionistas DEVE ser a soma de `Quantidade_Acionistas_PF`, `Quantidade_Acionistas_PJ` e `Quantidade_Acionistas_Investidores_Institucionais`

#### Scenario: Companhia sem registros no FRE
- **WHEN** o CNPJ não possui registro em `distribuicao_capital`
- **THEN** a quantidade de acionistas DEVE ser ausência de valor, sem impedir a análise dos demais tickers

### Requirement: Vigência por versão mais recente

O sistema DEVE selecionar, para cada CNPJ, o registro de `distribuicao_capital` com a versão mais recente, sem descartar registros cuja data de referência seja posterior à data corrente.

#### Scenario: Múltiplas versões para o mesmo CNPJ
- **WHEN** existem vários registros para o mesmo CNPJ com versões distintas
- **THEN** o sistema DEVE usar o registro de maior versão

#### Scenario: Data de referência futura
- **WHEN** a data de referência do registro é posterior à data corrente
- **THEN** o sistema DEVE ainda assim usar o registro da versão mais recente

### Requirement: Ponte ticker para CNPJ

O sistema DEVE resolver o CNPJ de uma companhia aberta a partir do ticker usando o dataset anual do Formulário Cadastral (FCA), arquivo `fca_cia_aberta_valor_mobiliario_<ano>.csv`, casando `Codigo_Negociacao` com o ticker e lendo `CNPJ_Companhia`.

#### Scenario: Ticker presente no FCA
- **WHEN** o ticker aparece como `Codigo_Negociacao` no `valor_mobiliario`
- **THEN** o sistema DEVE obter o `CNPJ_Companhia` correspondente

#### Scenario: Ticker ausente no FCA
- **WHEN** o ticker não aparece no `valor_mobiliario`
- **THEN** o sistema DEVE retornar ausência de valor sem lançar exceção

### Requirement: Preservação e cache dos arquivos anuais

O sistema DEVE baixar, extrair e cachear os arquivos anuais do FRE e do FCA, preservando o conteúdo bruto, o hash e os metadados de revalidação, reutilizando o arquivo local quando a fonte remota não tiver avançado.

#### Scenario: Arquivo anual já cacheado
- **WHEN** o arquivo anual do dataset já está no cache e a fonte remota não avançou
- **THEN** o sistema DEVE reutilizar o arquivo local sem novo processamento

#### Scenario: Falha de rede tolerada
- **WHEN** a aquisição de um dataset falha
- **THEN** o sistema DEVE sinalizar ausência de valor sem interromper a análise dos demais tickers

### Requirement: Cache das informações normalizadas

O sistema DEVE cachear as informações normalizadas derivadas dos datasets — o mapa ticker→CNPJ e a quantidade de acionistas por CNPJ —, associando cada entrada ao arquivo bruto de origem e à versão do parser, de modo que análises repetidas reutilizem os valores sem reprocessar os CSVs anuais.

#### Scenario: Mapa ticker→CNPJ reaproveitado
- **WHEN** o mapa ticker→CNPJ já foi construído a partir do FCA e o arquivo bruto não mudou
- **THEN** o sistema DEVE reutilizar o mapa em cache sem reprocessar o CSV

#### Scenario: Quantidade por CNPJ reaproveitada
- **WHEN** a quantidade de acionistas de um CNPJ já foi resolvida e o arquivo bruto não mudou
- **THEN** o sistema DEVE reutilizar o valor em cache sem reprocessar o CSV

#### Scenario: Invalidação por versão do parser
- **WHEN** a versão do parser do dataset muda
- **THEN** o cache das informações normalizadas DEVE ser invalidado
