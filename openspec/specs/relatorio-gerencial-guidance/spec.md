# relatorio-gerencial-guidance Specification

## Purpose

Manter, por FII, o guidance de distribuição de rendimentos — valor (ou faixa) por cota, período de validade e data do Relatório Gerencial que o apontou — em cache; avaliá-lo ao ler um Relatório Gerencial mais recente que o cache, preferindo a LLM e usando extração determinística quando ela não estiver disponível ou funcional; e alimentar a coluna `Informações adicionais` da análise fundamentalista a partir do cache, sem calcular guidance na carga de dados nem na exibição.

## Requirements

### Requirement: Ledger de avaliação de guidance por RG

O sistema DEVE persistir, por FII, um ledger em `~/.cache/flowscope/guidance/<TICKER>.json` com uma entrada por Relatório Gerencial avaliado, identificada pelo hash SHA-256 do conteúdo do PDF. Cada entrada DEVE registrar o método da avaliação (`ia` ou `deterministico`), a data do relatório de origem, o caminho do PDF e o resultado — um guidance com valor mínimo, valor máximo e período, ou a ausência de guidance. A escrita DEVE ser atômica e a leitura DEVE tolerar arquivo ausente, corrompido ou no formato v1 (guidance único, sem hash nem origem), tratando o formato v1 como uma entrada `deterministico`. Documento sem hash disponível DEVE usar o caminho relativo do arquivo como identidade substituta.

#### Scenario: FII sem guidance conhecido
- **WHEN** um FII nunca teve nenhuma entrada de guidance avaliada
- **THEN** a leitura DEVE resultar em ledger vazio, sem erro

#### Scenario: Guidance recuperado entre execuções
- **WHEN** uma avaliação é gravada no ledger e lida novamente
- **THEN** o método, a data do relatório, o caminho do PDF e o resultado DEVEM ser recuperados da entrada do RG

#### Scenario: Cache corrompido
- **WHEN** o arquivo de ledger do ticker contém JSON inválido
- **THEN** a leitura DEVE ser tolerada como ledger vazio, sem erro

#### Scenario: Migração do formato v1
- **WHEN** o arquivo do ticker está no formato v1, com um guidance único sem hash nem origem
- **THEN** o sistema DEVE lê-lo como uma entrada `deterministico`, preservando o guidance exposto até a próxima avaliação

#### Scenario: Documento sem hash
- **WHEN** o documento avaliado ainda não possui hash de conteúdo registrado
- **THEN** o sistema DEVE usar o caminho relativo do arquivo como identidade da entrada

### Requirement: Leitura do guidance pela análise fundamentalista sem cálculo

A análise fundamentalista DEVE ler o guidance corrente derivado do ledger e expô-lo em `AnaliseFundamental` apenas para tickers do tipo `FII`. A leitura NÃO DEVE calcular nem disparar extração de guidance: a carga de dados e a exibição da tabela apenas consultam o ledger. A ausência de guidance NÃO DEVE impedir o preenchimento das demais métricas nem a exibição da linha do ticker.

#### Scenario: FII com guidance em cache
- **WHEN** o ledger do FII contém alguma entrada com guidance e a análise é carregada
- **THEN** a análise DEVE expor o guidance corrente derivado, sem reprocessar PDFs

#### Scenario: Cache vazio não dispara cálculo
- **WHEN** o ledger do FII não contém nenhuma entrada com guidance e a análise é carregada
- **THEN** a análise NÃO DEVE expor guidance e NÃO DEVE iniciar extração

#### Scenario: Papel não consulta guidance
- **WHEN** o ticker é do tipo `Papel`
- **THEN** a análise NÃO DEVE expor guidance

#### Scenario: Ausência não impede as demais métricas
- **WHEN** o FII não possui guidance no ledger
- **THEN** as demais colunas da análise DEVEM permanecer preenchidas normalmente

### Requirement: Avaliação de guidance no processamento em lote dos pendentes

Ao processar documentos pelo botão "Resumir pendentes" da sub-aba "Documentos", o sistema DEVE avaliar o guidance dos documentos da categoria `Relatorio`, aplicando o controle de avaliação uma vez por método e a cascata de fontes, reaproveitando os resumos e o texto já preparado, sem reextrair o arquivo. Para os Relatórios Gerenciais pendentes de resumo, a avaliação DEVE ocorrer após a geração do resumo de cada item. Com a IA ativa, o lote DEVE também mirar os Relatórios Gerenciais (documentos da categoria `Relatorio`, própria de FII) já resumidos cuja entrada no ledger esteja ausente ou não marcada como `ia`; para esses, a geração de resumo DEVE ser pulada e somente a avaliação de guidance DEVE executar. A avaliação NÃO DEVE interromper o processamento em lote nem marcar a entrada quando a interação com a IA falhar. O lote NÃO DEVE avaliar guidance de documentos de outra categoria.

#### Scenario: Relatório pendente de resumo dispara avaliação
- **WHEN** o usuário aciona "Resumir pendentes" e um Relatório Gerencial pendente de resumo ainda não foi avaliado
- **THEN** o sistema DEVE avaliá-lo pela cascata após gerar o resumo, reaproveitando os resumos e o texto preparado

#### Scenario: Relatório já resumido pendente de guidance dispara avaliação
- **WHEN** o usuário aciona "Resumir pendentes", a IA está ativa, e um Relatório Gerencial já resumido tem entrada de guidance ausente ou não marcada como `ia`
- **THEN** o sistema DEVE avaliá-lo pela IA sem regerar o resumo, reaproveitando os resumos e o texto em cache

#### Scenario: Documento não pendente é ignorado
- **WHEN** um Relatório Gerencial já possui resumo e entrada de guidance marcada como `ia`
- **THEN** o lote NÃO DEVE avaliar seu guidance

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

### Requirement: Filtragem de menções não relacionadas ao guidance de distribuição

O sistema DEVE descartar menções que não representem guidance de distribuição, incluindo definições de glossário (`Guidance: Projeção ...`) e referências macroeconômicas (`forward guidance`).

#### Scenario: Definição de glossário
- **WHEN** o relatório define `Guidance: Projeção em relação ao desempenho financeiro futuro`
- **THEN** essa menção NÃO DEVE ser tratada como guidance de distribuição

#### Scenario: Guidance macroeconômico
- **WHEN** o relatório menciona `sem forward guidance` em comentário sobre política monetária
- **THEN** essa menção NÃO DEVE ser tratada como guidance de distribuição

### Requirement: Resultado da avaliação com proveniência

O resultado da avaliação DEVE conter valor mínimo, valor máximo, período de validade, data do relatório, caminho do PDF e o método (`ia` ou `deterministico`). A ausência de guidance DEVE ser registrada como resultado vazio daquele RG, distinguindo-se de falha de leitura, que não registra entrada.

#### Scenario: Resultado com proveniência
- **WHEN** o guidance é extraído do relatório de `2026/08`
- **THEN** a entrada do ledger DEVE conter os valores, o período, a data `2026-08`, o caminho do PDF e o método usado

#### Scenario: Ausência distinta de falha
- **WHEN** o FII não publica guidance e a avaliação conclui sem encontrar
- **THEN** a entrada do RG DEVE registrar a ausência, sem erro

### Requirement: Resiliência a falha de leitura do PDF

Uma falha de leitura ou de extração de texto de um PDF DEVE ser tolerada, resultando em não alteração do ledger e não interrompendo a leitura do documento nem a análise dos demais tickers.

#### Scenario: PDF corrompido
- **WHEN** um PDF do relatório não pode ser lido
- **THEN** o sistema DEVE manter o ledger intacto, sem propagar a exceção

### Requirement: Avaliação uma vez por método

Para cada Relatório Gerencial, o sistema DEVE avaliar no máximo uma vez por método. Quando a entrada do RG no ledger estiver marcada como `ia`, nenhuma nova avaliação DEVE ocorrer. Quando estiver marcada como `deterministico` e a IA estiver disponível, o sistema DEVE avaliar pela IA e substituir a entrada (a IA prevalece sobre o determinístico). Quando estiver marcada como `deterministico` e a IA não estiver disponível, nenhuma nova avaliação DEVE ocorrer. Uma falha na interação com a IA NÃO DEVE marcar a entrada como `ia`, mantendo o RG elegível a nova avaliação por IA e preservando o resultado determinístico existente.

#### Scenario: RG já avaliado por IA não é reavaliado
- **WHEN** a entrada do RG já está marcada como `ia` e o documento é processado novamente
- **THEN** o sistema NÃO DEVE avaliar nem alterar o ledger do RG

#### Scenario: RG determinístico é reavaliado pela IA quando disponível
- **WHEN** a entrada do RG está marcada como `deterministico` e a IA está disponível
- **THEN** o sistema DEVE avaliar pela IA e substituir a entrada do RG, prevalecendo a IA

#### Scenario: RG determinístico não é reavaliado sem IA
- **WHEN** a entrada do RG está marcada como `deterministico` e a IA não está disponível
- **THEN** o sistema NÃO DEVE avaliar nem alterar o ledger do RG

#### Scenario: Falha da IA preserva a entrada e permite nova tentativa
- **WHEN** a interação com a IA falha ao avaliar um RG
- **THEN** a entrada NÃO DEVE ser marcada como `ia` e o RG DEVE permanecer elegível a nova avaliação por IA

### Requirement: Cascata de fontes de avaliação

A avaliação de um RG DEVE consultar as fontes na ordem: resumo curto, resumo longo e texto extraído, interrompendo na primeira que contiver guidance. Fontes ausentes DEVEM ser puladas. Quando nenhuma fonte contiver guidance, o sistema DEVE registrar a ausência de guidance para aquele RG.

#### Scenario: Guidance no resumo curto interrompe a cascata
- **WHEN** o resumo curto do RG contém guidance
- **THEN** o sistema DEVE registrar esse resultado sem consultar o resumo longo nem o texto

#### Scenario: Guidance apenas no resumo longo
- **WHEN** o resumo curto não contém guidance e o resumo longo contém
- **THEN** o sistema DEVE registrar o resultado do resumo longo sem consultar o texto

#### Scenario: Guidance apenas no texto extraído
- **WHEN** nem o resumo curto nem o resumo longo contêm guidance e o texto extraído contém
- **THEN** o sistema DEVE registrar o guidance extraído do texto

#### Scenario: Nenhuma fonte contém guidance
- **WHEN** o resumo curto, o resumo longo e o texto extraído não contêm guidance
- **THEN** o sistema DEVE registrar a ausência de guidance para o RG

#### Scenario: Resumos ausentes usam o texto
- **WHEN** o RG não possui resumo curto nem longo e possui texto extraído
- **THEN** o sistema DEVE avaliar apenas o texto extraído

### Requirement: Derivação do guidance corrente

O guidance exposto à análise fundamentalista DEVE ser derivado do ledger, selecionando a entrada com resultado de guidance e maior `data_relatorio`. Entradas cujo resultado seja ausência de guidance NÃO DEVEM remover o guidance corrente apontado por outro RG. Sem nenhuma entrada com resultado de guidance, o FII DEVE ser tratado como sem guidance.

#### Scenario: Entrada mais recente vence
- **WHEN** o ledger possui guidance em `2026/07` e em `2026/08`
- **THEN** o guidance derivado DEVE ser o de `2026/08`

#### Scenario: Ausência recente não apaga guidance anterior
- **WHEN** a entrada mais recente do ledger registra ausência de guidance e uma entrada anterior registra guidance
- **THEN** o guidance derivado DEVE ser o da entrada anterior

#### Scenario: Ledger sem guidance
- **WHEN** nenhuma entrada do ledger registra guidance
- **THEN** o FII DEVE ser tratado como sem guidance

### Requirement: Avaliação de guidance ao ler um Relatório Gerencial

Ao ler um documento da categoria `Relatorio` na sub-aba "Documentos", o sistema DEVE aplicar o controle de avaliação uma vez por método e a cascata de fontes, reaproveitando os resumos curto e longo do documento e o texto extraído obtido do cache de texto, sem reextrair o arquivo. A avaliação DEVE ocorrer fora da thread da interface e após a geração do resumo. Documento cujas fontes (resumos e texto) estejam todas ausentes NÃO DEVE disparar avaliação. NÃO há portão de data: um RG ainda não avaliado DEVE ser avaliado mesmo que seja anterior ao guidance corrente, e um RG já avaliado pelo mesmo método NÃO DEVE ser reavaliado.

#### Scenario: RG ainda não avaliado dispara avaliação
- **WHEN** o usuário lê um Relatório Gerencial cuja entrada ainda não existe no ledger
- **THEN** o sistema DEVE avaliá-lo pela cascata e registrar o resultado

#### Scenario: RG já avaliado por IA é ignorado
- **WHEN** o usuário lê um Relatório Gerencial cuja entrada está marcada como `ia`
- **THEN** o sistema NÃO DEVE avaliar nem alterar o ledger

#### Scenario: RG anterior ainda não avaliado é avaliado
- **WHEN** o ledger contém guidance de `2026/08` e o usuário lê um Relatório Gerencial de `2026/07` ainda não avaliado
- **THEN** o sistema DEVE avaliar o relatório de `2026/07`

#### Scenario: Documento de outra categoria
- **WHEN** o usuário lê um documento que não é da categoria `Relatorio`
- **THEN** o sistema NÃO DEVE avaliar guidance nem alterar o ledger

#### Scenario: Documento sem fontes
- **WHEN** o usuário lê um Relatório Gerencial sem resumos e sem texto extraível
- **THEN** o sistema NÃO DEVE avaliar guidance nem alterar o ledger, sem interromper a leitura nem a abertura do documento

### Requirement: Exposure do guidance do RG para exibição na leitura

Ao ler um Relatório Gerencial na sub-aba "Documentos", o resultado da avaliação daquele RG — o guidance ou a ausência — DEVE ser disponibilizado ao fluxo de leitura para exibição, sem nova consulta ao ledger na thread da interface e sem reavaliar o RG. O guidance disponibilizado DEVE corresponder à entrada do ledger identificada pela chave de conteúdo do documento selecionado, e não ao guidance corrente derivado do FII. Quando o RG já possui entrada no ledger por um método que dispensa reavaliação, a entrada existente DEVE ser a fonte do guidance disponibilizado. O lote de resumos DEVE propagar o resultado da avaliação de cada RG junto do resumo, para a recomposição da pré-visualização.

#### Scenario: RG com guidance é disponibilizado na leitura
- **WHEN** o usuário lê um Relatório Gerencial cuja entrada no ledger registra guidance
- **THEN** o sistema DEVE disponibilizar esse guidance ao fluxo de leitura para exibição

#### Scenario: RG com ausência registrada não expõe guidance
- **WHEN** o usuário lê um Relatório Gerencial cuja entrada no ledger registra ausência de guidance
- **THEN** o sistema NÃO DEVE disponibilizar item de guidance para exibição

#### Scenario: Guidance exposto é o do RG lido, não o corrente
- **WHEN** o ledger tem guidance de um RG mais recente e o usuário lê um RG anterior com guidance registrado
- **THEN** o guidance disponibilizado DEVE ser o do RG lido

#### Scenario: RG avaliado não é reavaliado para exibição
- **WHEN** o usuário lê um Relatório Gerencial já avaliado pelo mesmo método
- **THEN** o sistema NÃO DEVE reavaliar nem alterar o ledger, reutilizando a entrada existente para exibição

#### Scenario: Lote propaga a avaliação para a recomposição
- **WHEN** o lote de resumos avalia o guidance de um Relatório Gerencial pendente
- **THEN** o resultado daquela avaliação DEVE ser propagado junto do resumo para a recomposição da pré-visualização

### Requirement: Avaliação preferencial pela IA

Quando o provedor de chat estiver configurado, o sistema DEVE submeter cada fonte da cascata à avaliação pela IA via porta `LLMPort`, para determinar se ela contém guidance de distribuição. Havendo guidance, o resultado DEVE ser registrado com método `ia`, substituindo a entrada anterior do mesmo RG. Não havendo guidance em nenhuma fonte, o sistema DEVE registrar a ausência com método `ia`. O flag `llm.guidance.enabled` NÃO DEVE mais existir; a disponibilidade da IA corresponde a haver provedor de chat configurado. Uma falha na interação com a IA DEVE recorrer à extração determinística.

#### Scenario: IA disponível encontra guidance
- **WHEN** o provedor de chat está configurado e alguma fonte da cascata contém guidance
- **THEN** o guidance extraído pela IA DEVE ser registrado com método `ia`, substituindo a entrada anterior do RG

#### Scenario: IA disponível não encontra guidance
- **WHEN** o provedor de chat está configurado e nenhuma fonte da cascata contém guidance
- **THEN** o sistema DEVE registrar a ausência de guidance com método `ia` para o RG

#### Scenario: IA indisponível usa extração determinística
- **WHEN** nenhum provedor de chat está configurado
- **THEN** o sistema NÃO DEVE chamar a IA e DEVE avaliar pela extração determinística

#### Scenario: Flag de guidance removido
- **WHEN** a configuração da aplicação é lida
- **THEN** o sistema NÃO DEVE consultar nem exigir o flag `llm.guidance.enabled`

### Requirement: Extração determinística como reserva

Quando a IA não estiver disponível ou a interação com ela falhar, o sistema DEVE extrair o guidance por correspondência de padrões textuais (expressões regulares), percorrendo a cascata. Extraindo guidance, o resultado DEVE ser registrado com método `deterministico`, substituindo a entrada determinística anterior do mesmo RG; não extraindo, DEVE registrar a ausência com método `deterministico`. O valor DEVE ser normalizado para um mínimo e um máximo por cota, iguais quando o guidance for um valor único, e o período de validade DEVE ser preservado na forma reconhecida no relatório.

#### Scenario: Guidance determinístico gravado
- **WHEN** a IA está indisponível e o texto do relatório contém `Guidance 2S26: R$ 0,85/cota`
- **THEN** o sistema DEVE extrair valor mínimo e máximo `0,85`, período `2S26` e registrar a entrada com método `deterministico`

#### Scenario: Faixa determinística em tabela de bandas
- **WHEN** o relatório apresenta `Banda Superior R$ 0,10` e `Banda Inferior R$ 0,08` sob o título de guidance e a IA está indisponível
- **THEN** o sistema DEVE extrair valor mínimo `0,08` e máximo `0,10`

#### Scenario: Guidance em inglês
- **WHEN** o relatório contém `Guidance for the next 3 months: R$ 0.10 to R$ 0.11/unit` e a IA está indisponível
- **THEN** o sistema DEVE extrair a faixa `0.10` a `0.11` e o período `next 3 months`

#### Scenario: Nada extraído registra ausência
- **WHEN** o relatório menciona guidance mas o valor está apenas em gráfico sem texto adjacente
- **THEN** o sistema DEVE registrar a ausência de guidance para o RG, sem interromper a análise
