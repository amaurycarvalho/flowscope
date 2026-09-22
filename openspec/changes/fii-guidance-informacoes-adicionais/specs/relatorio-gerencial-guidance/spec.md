## Purpose

Manter, por FII, o guidance de distribuição de rendimentos — valor (ou faixa) por cota, período de validade e data do Relatório Gerencial que o apontou — em cache; avaliá-lo ao ler um Relatório Gerencial mais recente que o cache, preferindo a LLM e usando extração determinística quando ela não estiver disponível ou funcional; e alimentar a coluna `Informações adicionais` da análise fundamentalista a partir do cache, sem calcular guidance na carga de dados nem na exibição.

## ADDED Requirements

### Requirement: Cache de guidance por FII

O sistema DEVE persistir o guidance em `~/.cache/flowscope/guidance/<TICKER>.json`, um arquivo por FII, com informação inicialmente vazia, escrita atômica e tolerância a arquivo ausente ou corrompido. O conteúdo DEVE conter valor mínimo, valor máximo, período de validade, data do relatório de origem e caminho do PDF, ou estar vazio quando não houver guidance conhecido.

#### Scenario: FII sem guidance conhecido
- **WHEN** um FII nunca teve guidance avaliado
- **THEN** a leitura DEVE resultar em ausência de guidance, sem erro

#### Scenario: Guidance recuperado entre execuções
- **WHEN** um guidance é gravado no cache e lido novamente
- **THEN** os valores, o período, a data do relatório e o caminho do PDF DEVEM ser recuperados do arquivo do ticker

#### Scenario: Cache corrompido
- **WHEN** o arquivo de cache do ticker contém JSON inválido
- **THEN** a leitura DEVE ser tolerada como ausência de guidance, sem erro

### Requirement: Leitura do guidance pela análise fundamentalista sem cálculo

A análise fundamentalista DEVE ler o guidance do cache e expô-lo em `AnaliseFundamental` apenas para tickers do tipo `FII`. A leitura NÃO DEVE calcular nem disparar extração de guidance: a carga de dados e a exibição da tabela apenas consultam o cache. A ausência de guidance NÃO DEVE impedir o preenchimento das demais métricas nem a exibição da linha do ticker.

#### Scenario: FII com guidance em cache
- **WHEN** o cache do FII contém guidance e a análise é carregada
- **THEN** a análise DEVE expor os valores, o período e a data do relatório, sem reprocessar PDFs

#### Scenario: Cache vazio não dispara cálculo
- **WHEN** o cache do FII está vazio e a análise é carregada
- **THEN** a análise NÃO DEVE expor guidance e NÃO DEVE iniciar extração

#### Scenario: Papel não consulta guidance
- **WHEN** o ticker é do tipo `Papel`
- **THEN** a análise NÃO DEVE expor guidance

#### Scenario: Ausência não impede as demais métricas
- **WHEN** o FII não possui guidance em cache
- **THEN** as demais colunas da análise DEVEM permanecer preenchidas normalmente

### Requirement: Avaliação ao ler um Relatório Gerencial mais recente

Ao ler um documento da categoria `Relatorio` na sub-aba "Documentos", o sistema DEVE avaliar o guidance do relatório somente quando `(ano, mês)` do relatório for posterior à data do guidance em cache, ou quando o cache estiver vazio. Relatório de referência igual ou anterior à do guidance em cache NÃO DEVE disparar avaliação. A avaliação DEVE ocorrer fora da thread da interface, reaproveitando o **texto do documento obtido do cache de texto do documento** (change `cache-texto-documentos`), sem reextrair o arquivo. Documento sem texto extraível NÃO DEVE disparar avaliação.

#### Scenario: Relatório mais recente dispara avaliação
- **WHEN** o cache do FII contém guidance de `2026/07` e o usuário lê um Relatório Gerencial de `2026/08`
- **THEN** o sistema DEVE avaliar o relatório de `2026/08`

#### Scenario: Cache vazio dispara avaliação
- **WHEN** o FII não possui guidance em cache e o usuário lê um Relatório Gerencial
- **THEN** o sistema DEVE avaliar o relatório

#### Scenario: Relatório não mais recente é ignorado
- **WHEN** o cache do FII contém guidance de `2026/08` e o usuário lê um Relatório Gerencial de `2026/07`
- **THEN** o sistema NÃO DEVE avaliar nem alterar o cache

#### Scenario: Documento de outra categoria
- **WHEN** o usuário lê um documento que não é da categoria `Relatorio`
- **THEN** o sistema NÃO DEVE avaliar guidance nem alterar o cache

#### Scenario: Documento sem texto extraível
- **WHEN** o usuário lê um Relatório Gerencial cujo cache de texto do documento registra ausência de texto extraível
- **THEN** o sistema NÃO DEVE avaliar guidance nem alterar o cache, sem interromper a leitura nem a abertura do documento

### Requirement: Avaliação preferencial pela LLM

Quando o recurso de LLM estiver disponível e funcional, o sistema DEVE submeter o texto do relatório a uma avaliação específica, via porta `LLMPort`, para determinar se ele contém guidance de distribuição. Havendo guidance, o resultado DEVE substituir a informação anterior no cache de guidance do FII. Não havendo guidance, o cache DEVE permanecer intacto.

#### Scenario: LLM disponível encontra guidance
- **WHEN** a LLM está configurada e funcional e o relatório contém guidance
- **THEN** o guidance extraído pela LLM DEVE substituir o anterior no cache, com a data do relatório lido

#### Scenario: LLM disponível não encontra guidance
- **WHEN** a LLM está configurada e funcional e o relatório não contém guidance
- **THEN** o cache DEVE permanecer intacto

#### Scenario: LLM funcional determina o caminho
- **WHEN** a chamada à LLM conclui sem erro
- **THEN** o sistema DEVE considerar o recurso funcional e usar o resultado da LLM, sem recorrer à extração determinística

### Requirement: Extração determinística como fallback

Quando o recurso de LLM estiver indisponível ou não funcional, o sistema DEVE extrair o guidance por correspondência de padrões textuais (expressões regulares), sem recorrer a modelos de linguagem. Extraindo guidance, o resultado DEVE substituir a informação anterior no cache; não extraindo, o cache DEVE permanecer intacto. O valor DEVE ser normalizado para um mínimo e um máximo por cota, iguais quando o guidance for um valor único, e o período de validade DEVE ser preservado na forma reconhecida no relatório.

#### Scenario: LLM indisponível usa extração determinística
- **WHEN** nenhum provedor de LLM está configurado e o relatório contém `Guidance 2S26: R$ 0,85/cota`
- **THEN** o sistema DEVE extrair valor mínimo e máximo `0,85`, período `2S26` e gravar no cache

#### Scenario: Falha da LLM recorre à extração determinística
- **WHEN** a chamada à LLM falha e o relatório contém uma faixa `entre R$ 0,74 e R$ 0,78 por cota` para `o restante do ano de 2026`
- **THEN** o sistema DEVE extrair a faixa `0,74` a `0,78`, o período `restante do ano de 2026` e gravar no cache

#### Scenario: Faixa em tabela de bandas
- **WHEN** o relatório apresenta `Banda Superior R$ 0,10` e `Banda Inferior R$ 0,08` sob o título de guidance
- **THEN** o sistema DEVE extrair valor mínimo `0,08` e máximo `0,10`

#### Scenario: Guidance em inglês
- **WHEN** o relatório contém `Guidance for the next 3 months: R$ 0.10 to R$ 0.11/unit`
- **THEN** o sistema DEVE extrair a faixa `0.10` a `0.11` e o período `next 3 months`

#### Scenario: Nada extraído preserva o cache
- **WHEN** o relatório menciona guidance mas o valor está apenas em gráfico sem texto adjacente
- **THEN** o sistema NÃO DEVE alterar o cache, sem interromper a análise

### Requirement: Filtragem de menções não relacionadas ao guidance de distribuição

O sistema DEVE descartar menções que não representem guidance de distribuição, incluindo definições de glossário (`Guidance: Projeção ...`) e referências macroeconômicas (`forward guidance`).

#### Scenario: Definição de glossário
- **WHEN** o relatório define `Guidance: Projeção em relação ao desempenho financeiro futuro`
- **THEN** essa menção NÃO DEVE ser tratada como guidance de distribuição

#### Scenario: Guidance macroeconômico
- **WHEN** o relatório menciona `sem forward guidance` em comentário sobre política monetária
- **THEN** essa menção NÃO DEVE ser tratada como guidance de distribuição

### Requirement: Resultado da avaliação com proveniência

O resultado da avaliação DEVE conter valor mínimo, valor máximo, período de validade, data do relatório e caminho do PDF de origem. A ausência de guidance DEVE ser representada como ausência do item no cache, distinguindo-se de falha de leitura.

#### Scenario: Resultado com proveniência
- **WHEN** o guidance é extraído do relatório de `2026/08`
- **THEN** o cache DEVE conter os valores, o período, a data `2026-08` e o caminho do PDF

#### Scenario: Ausência distinta de falha
- **WHEN** o FII não publica guidance
- **THEN** o cache DEVE permanecer sem item, sem erro

### Requirement: Resiliência a falha de leitura do PDF

Uma falha de leitura ou de extração de texto de um PDF DEVE ser tolerada, resultando em não alteração do cache de guidance, sem interromper a leitura do documento nem a análise dos demais tickers.

#### Scenario: PDF corrompido
- **WHEN** um PDF do relatório não pode ser lido
- **THEN** o sistema DEVE manter o cache intacto, sem propagar a exceção
