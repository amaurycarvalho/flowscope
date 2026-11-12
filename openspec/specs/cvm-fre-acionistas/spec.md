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

O sistema DEVE resolver o CNPJ de uma companhia aberta a partir do ticker usando duas fontes: primeiro o dataset anual do Formulário Cadastral (FCA), casando `Codigo_Negociacao` com o ticker; se não houver correspondência, DEVE resolver o `codeCVM` do ticker na B3 e consultar o cadastro de companhias abertas da CVM, casando `CD_CVM` com o `codeCVM` e lendo `CNPJ_CIA`. A ausência de ambas as correspondências DEVE resultar em ausência de valor, sem exceção.

#### Scenario: Ticker presente no FCA
- **WHEN** o ticker aparece como `Codigo_Negociacao` no `valor_mobiliario`
- **THEN** o sistema DEVE obter o `CNPJ_Companhia` correspondente

#### Scenario: Ticker ausente no FCA
- **WHEN** o ticker não aparece no `valor_mobiliario`
- **THEN** o sistema DEVE tentar o `codeCVM` no cadastro de companhias e, sem correspondência nas duas fontes, retornar ausência de valor sem lançar exceção

#### Scenario: Código de negociação não literal resolve por codeCVM
- **WHEN** o FCA traz `Codigo_Negociacao` diferente do ticker (ex.: `000000`, `ADR` ou o próprio codeCVM) e o `codeCVM` do ticker existe no cadastro de companhias
- **THEN** o sistema DEVE obter o `CNPJ_CIA` correspondente ao `CD_CVM`

#### Scenario: CodeCVM ausente
- **WHEN** o ticker não tem correspondência no FCA e o B3 não resolve um `codeCVM`
- **THEN** o sistema DEVE retornar ausência de valor, sem consultar o cadastro ou interromper os demais tickers

#### Scenario: Falha no cadastro de companhias
- **WHEN** a aquisição ou leitura do cadastro de companhias falha
- **THEN** o sistema DEVE retornar ausência de valor, preservando a análise dos demais tickers

### Requirement: Preservação e cache dos arquivos anuais

O sistema DEVE baixar, extrair e cachear os arquivos anuais do FRE e do FCA, preservando o conteúdo bruto, o hash e os metadados de revalidação, reutilizando o arquivo local quando a fonte remota não tiver avançado.

#### Scenario: Arquivo anual já cacheado
- **WHEN** o arquivo anual do dataset já está no cache e a fonte remota não avançou
- **THEN** o sistema DEVE reutilizar o arquivo local sem novo processamento

#### Scenario: Falha de rede tolerada
- **WHEN** a aquisição de um dataset falha
- **THEN** o sistema DEVE sinalizar ausência de valor sem interromper a análise dos demais tickers

### Requirement: Cache das informações normalizadas

O sistema DEVE cachear as informações normalizadas derivadas dos datasets — o mapa ticker→CNPJ do FCA, o mapa codeCVM→identidade (CNPJ e razão social) do cadastro de companhias e a quantidade de acionistas por CNPJ —, associando cada entrada ao arquivo bruto de origem e à versão do parser, de modo que análises repetidas reutilizem os valores sem reprocessar os CSVs.

#### Scenario: Mapa ticker→CNPJ reaproveitado
- **WHEN** o mapa ticker→CNPJ já foi construído a partir do FCA e o arquivo bruto não mudou
- **THEN** o sistema DEVE reutilizar o mapa em cache sem reprocessar o CSV

#### Scenario: Mapa codeCVM→identidade reaproveitado
- **WHEN** o mapa codeCVM→identidade já foi construído a partir do cadastro de companhias e o arquivo bruto não mudou
- **THEN** o sistema DEVE reutilizar o mapa em cache sem reprocessar o CSV

#### Scenario: Quantidade por CNPJ reaproveitada
- **WHEN** a quantidade de acionistas de um CNPJ já foi resolvida e o arquivo bruto não mudou
- **THEN** o sistema DEVE reutilizar o valor em cache sem reprocessar o CSV

#### Scenario: Invalidação por versão do parser
- **WHEN** a versão do parser do dataset muda
- **THEN** o cache das informações normalizadas DEVE ser invalidado

#### Scenario: Cache legado em formato anterior
- **WHEN** o cache normalizado do cadastro está no formato anterior (`CD_CVM → string`) e a versão do parser mudou
- **THEN** o sistema DEVE ignorar o cache anterior e reprocessar o CSV; um valor legado tolerado NÃO DEVE fazer o CNPJ desaparecer

### Requirement: Aquisição e cache do cadastro de companhias abertas

O sistema DEVE baixar e cachear o cadastro de companhias abertas da CVM (`CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv`), preservando o arquivo bruto, o hash e os metadados de revalidação, e DEVE normalizar um mapa `CD_CVM → identidade` com código CVM sem zeros à esquerda, CNPJ sem pontuação e razão social de `DENOM_SOCIAL`. Arquivo cacheado e não alterado na origem DEVE ser reutilizado sem novo processamento.

#### Scenario: Cadastro carregado e normalizado
- **WHEN** o cadastro contém um registro com `CD_CVM`, `CNPJ_CIA` e `DENOM_SOCIAL`
- **THEN** o sistema DEVE expor o CNPJ normalizado e a razão social sob o código CVM sem zeros à esquerda

#### Scenario: Cadastro reaproveitado
- **WHEN** o arquivo do cadastro está em cache e a fonte remota não avançou
- **THEN** o sistema DEVE reutilizar o arquivo local sem novo download

#### Scenario: Falha de rede tolerada
- **WHEN** o download do cadastro falha
- **THEN** o sistema DEVE sinalizar ausência de valor sem interromper a análise dos demais tickers

### Requirement: Identidade de Papel com razão social

O sistema DEVE expor, para Papel, o CNPJ e a razão social quando disponíveis, obtendo a razão social de `DENOM_SOCIAL` no cadastro de companhias pelo `codeCVM`. A ausência de razão social NÃO DEVE impedir a exposição do CNPJ nem a análise dos demais tickers.

#### Scenario: Identidade com CNPJ e razão social
- **WHEN** o cadastro possui a companhia com `codeCVM`, CNPJ e `DENOM_SOCIAL`
- **THEN** o sistema DEVE expor o CNPJ e a razão social do Papel

#### Scenario: Razão social ausente
- **WHEN** o CNPJ do Papel é resolvido e a razão social não está disponível
- **THEN** o sistema DEVE expor apenas o CNPJ, sem erro

#### Scenario: Falha na razão social preserva o CNPJ
- **WHEN** a consulta da razão social falha, mas o CNPJ foi resolvido
- **THEN** o sistema DEVE manter o CNPJ e omitir a razão social
