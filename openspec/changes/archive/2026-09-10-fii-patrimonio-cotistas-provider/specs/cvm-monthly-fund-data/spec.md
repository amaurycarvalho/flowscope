## MODIFIED Requirements

### Requirement: Descoberta e versionamento de schema

O sistema DEVE identificar a estrutura de cada CSV do arquivo anual pelo conjunto de colunas, sem assumir a posição física dos registros nem usar apenas o ano como critério de versão. O arquivo anual DEVE ser tratado como multi-arquivo (`geral`, `complemento`, `ativo_passivo`), e cada arquivo DEVE ser processado de forma independente: um arquivo sem as colunas obrigatórias de patrimônio e cotas DEVE ser ignorado, sem abortar a leitura dos demais. O sistema DEVE aceitar os nomes atuais (`CNPJ_Fundo_Classe`, `Data_Referencia`, `Patrimonio_Liquido`, `Cotas_Emitidas`, `Total_Numero_Cotistas`) e aliases legados (`CNPJ_Fundo`, `Nome_Fundo`, `Tipo_Fundo`, `QUANT_COTA`).

#### Scenario: Schema 2025+ reconhecido
- **WHEN** o arquivo `complemento` contém `CNPJ_Fundo_Classe`, `Data_Referencia`, `Patrimonio_Liquido`, `Cotas_Emitidas` e `Total_Numero_Cotistas`
- **THEN** o sistema DEVE resolver essas colunas e processar os registros de patrimônio e cotistas

#### Scenario: Schema legado reconhecido
- **WHEN** o CSV contém `CNPJ_Fundo` e `QUANT_COTA`
- **THEN** o sistema DEVE resolver pelos aliases e processar os registros

#### Scenario: Colunas obrigatórias ausentes
- **WHEN** um CSV do arquivo anual não contém as colunas obrigatórias de patrimônio e cotas
- **THEN** o sistema DEVE ignorar esse arquivo sem produzir dados parcialmente incorretos, continuando a processar os demais

### Requirement: Normalização de patrimônio, cotas e cotistas

O sistema DEVE normalizar os campos de patrimônio líquido (`Patrimonio_Liquido`), quantidade de cotas (`Cotas_Emitidas`) e número de cotistas (`Total_Numero_Cotistas`) do arquivo `complemento` em uma observação de patrimônio com data de referência e fonte CVM.

#### Scenario: Patrimônio normalizado
- **WHEN** um registro do fundo é selecionado no arquivo `complemento`
- **THEN** o sistema DEVE retornar patrimônio líquido, cotas e cotistas com a data de competência e fonte CVM
