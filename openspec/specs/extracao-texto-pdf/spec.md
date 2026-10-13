# extracao-texto-pdf Specification

## Purpose
Extrair texto de arquivos PDF de forma resiliente, distinguindo ausência real de
texto de extração parcial, falha de leitura e documento protegido, para que os
consumidores decidam corretamente exibir, cachear ou reprocessar.

## Requirements

### Requirement: Resultado de extração com status

O sistema DEVE classificar o resultado da extração de texto de cada PDF em um de
cinco estados observáveis: completo (`OK`), parcial (`PARCIAL`), sem texto
(`SEM_TEXTO`), falha de leitura (`FALHA`) e protegido por senha (`PROTEGIDO`).
`PARCIAL` DEVE indicar que ao menos uma página produziu texto e ao menos uma
falhou, registrando a contagem de páginas com falha.

#### Scenario: PDF com texto completo
- **WHEN** um PDF legível é extraído e todas as páginas produzem texto
- **THEN** o resultado DEVE ter estado completo e o texto concatenado das páginas

#### Scenario: PDF parcial
- **WHEN** um PDF tem páginas legíveis e ao menos uma página ilegível
- **THEN** o resultado DEVE ter estado parcial, com o texto das páginas legíveis e a contagem de falhas

#### Scenario: PDF sem texto
- **WHEN** um PDF é lido com sucesso, mas nenhuma página produz texto
- **THEN** o resultado DEVE ter estado sem texto, com texto vazio

#### Scenario: Falha de leitura
- **WHEN** a abertura do PDF ou a leitura de todas as páginas falha
- **THEN** o resultado DEVE ter estado de falha, com texto vazio, sem propagar exceção

#### Scenario: PDF protegido
- **WHEN** um PDF está criptografado e não pode ser aberto com senha vazia nem com a senha informada
- **THEN** o resultado DEVE ter estado protegido, com texto vazio, sem propagar exceção

### Requirement: Tolerância por página

A extração DEVE tratar falhas por página de forma isolada: uma página ilegível
NÃO DEVE descartar o texto das demais. Quando ao menos uma página produzir texto e
outra falhar, o resultado DEVE ser `PARCIAL` com a contagem de páginas com falha.

#### Scenario: Página ilegível não descarta as demais
- **WHEN** um PDF tem uma página cujo texto não pode ser extraído e outras páginas legíveis
- **THEN** o texto das páginas legíveis DEVE ser retornado com estado parcial e contagem de falhas maior que zero

#### Scenario: Todas as páginas falham
- **WHEN** todas as páginas de um PDF falham na extração e nenhuma produz texto
- **THEN** o resultado DEVE ter estado de falha, com texto vazio

### Requirement: Tentativa de senha vazia

Antes de classificar um PDF criptografado como protegido, o sistema DEVE tentar
abri-lo com senha vazia. Se a tentativa vazia for bem-sucedida, a extração DEVE
prosseguir normalmente.

#### Scenario: Criptografia com senha vazia
- **WHEN** um PDF está criptografado, mas abre com senha vazia
- **THEN** o texto DEVE ser extraído com estado completo

#### Scenario: Criptografia sem senha vazia
- **WHEN** um PDF está criptografado e não abre com senha vazia nem com a senha informada
- **THEN** o resultado DEVE ter estado protegido

### Requirement: Extração autenticada por senha

A extração de um PDF DEVE aceitar uma senha opcional. Quando uma senha for
informada, o sistema DEVE tentar abrir o PDF com ela; em caso de sucesso, a
extração DEVE prosseguir normalmente; em caso de falha, o resultado DEVE ser
protegido. A senha NÃO DEVE ser persistida.

#### Scenario: Senha correta
- **WHEN** um PDF protegido é extraído com a senha correta
- **THEN** o texto DEVE ser extraído com estado completo

#### Scenario: Senha incorreta
- **WHEN** um PDF protegido é extraído com uma senha incorreta
- **THEN** o resultado DEVE ter estado protegido, sem texto

#### Scenario: Senha não persistida
- **WHEN** a extração autenticada obtém texto com sucesso
- **THEN** apenas o texto DEVE ser disponibilizado, sem armazenar a senha

### Requirement: Interface de texto compatível

Para consumidores que dependem apenas do texto, o sistema DEVE oferecer uma
interface que devolve somente a string extraída (vazia em qualquer estado
diferente de completo ou parcial), preservando o comportamento anterior desses
consumidores.

#### Scenario: Consumidor recebe apenas texto
- **WHEN** a interface de texto é chamada para um PDF
- **THEN** ela DEVE devolver o texto extraído ou string vazia, sem lançar exceção

### Requirement: Ruído de log da biblioteca não vaza do processo de extração

A extração de PDF DEVE aplicar o controle de log da biblioteca (`logging`)
tanto no processo corrente quanto no processo separado do orçamento de tempo.
Como o worker separado não herda a configuração de logging do processo
principal, ele DEVE configurar o logger `pypdf` por conta própria: suprimir
`WARNING`/`INFO`/`DEBUG` e gravar `ERROR` ou acima no arquivo de log da
aplicação, sem escrever no `stderr`/console.

#### Scenario: PDF malformado não inunda o terminal

- **WHEN** o worker separado da extração lê um PDF cujo `xref` é inválido e o `pypdf` emite avisos de autorreparo
- **THEN** o worker NÃO DEVE escrever esses avisos no `stderr`/console herdado

#### Scenario: Erro da biblioteca fica auditável

- **WHEN** o `pypdf` emite um `ERROR` no worker separado da extração
- **THEN** o registro DEVE ser gravado no arquivo de log da aplicação, preservando a auditoria

#### Scenario: Extração normal inalterada

- **WHEN** um PDF legível é extraído
- **THEN** o resultado da extração e o tempo de processamento DEVEM permanecer inalterados pelo controle de log

### Requirement: Orçamento de tempo da extração de arquivo

O sistema DEVE limitar a extração de texto de cada arquivo PDF a um orçamento de
tempo por documento de 90 segundos. Ao exceder o orçamento, a extração DEVE ser
interrompida, o texto já produzido DEVE ser preservado e o resultado DEVE ter
estado `PARCIAL` — ou `FALHA`, quando nenhuma página tiver produzido texto —
sem propagar exceção. A extração de HTML NÃO DEVE estar sujeita ao orçamento.

#### Scenario: PDF dentro do orçamento
- **WHEN** um PDF é extraído dentro do orçamento de tempo
- **THEN** o resultado DEVE seguir a classificação por estado já existente (completo, parcial, sem texto, falha ou protegido)

#### Scenario: PDF que excede o orçamento mantém o texto parcial
- **WHEN** a extração de um PDF excede o orçamento de tempo após produzir texto em ao menos uma página
- **THEN** a extração DEVE ser interrompida e o resultado DEVE ter estado parcial, com o texto das páginas já extraídas

#### Scenario: PDF que excede o orçamento sem texto
- **WHEN** a extração de um PDF excede o orçamento de tempo sem que nenhuma página tenha produzido texto
- **THEN** a extração DEVE ser interrompida e o resultado DEVE ter estado de falha, com texto vazio

#### Scenario: HTML não está sujeito ao orçamento
- **WHEN** o arquivo é HTML
- **THEN** a extração DEVE ocorrer sem orçamento de tempo e retornar a classificação por estado já existente

#### Scenario: Tempo limite não propaga exceção
- **WHEN** qualquer extração de arquivo é executada, inclusive com estouro do orçamento
- **THEN** o sistema NÃO DEVE propagar exceção da biblioteca de extração

### Requirement: Orçamento de tempo da extração de PDF a partir de bytes

O sistema DEVE oferecer a extração orçada de texto de um PDF a partir do conteúdo em memória (bytes), aplicando o mesmo orçamento de tempo por documento e a mesma classificação de estados da extração por arquivo. Ao exceder o orçamento, a extração DEVE ser interrompida, o texto já produzido DEVE ser preservado e o resultado DEVE ter estado `PARCIAL` — ou `FALHA`, quando nenhuma página tiver produzido texto — sem propagar exceção e NUNCA como `SEM_TEXTO`. A extração a partir de bytes DEVE honrar a tentativa de senha vazia e a senha opcional informada.

#### Scenario: PDF em memória dentro do orçamento

- **WHEN** um PDF em memória é extraído dentro do orçamento de tempo
- **THEN** o resultado DEVE seguir a classificação por estado já existente (completo, parcial, sem texto, falha ou protegido)

#### Scenario: PDF em memória que excede o orçamento mantém o texto parcial

- **WHEN** a extração de um PDF em memória excede o orçamento após produzir texto em ao menos uma página
- **THEN** a extração DEVE ser interrompida e o resultado DEVE ter estado parcial, com o texto das páginas já extraídas

#### Scenario: PDF em memória que excede o orçamento sem texto

- **WHEN** a extração de um PDF em memória excede o orçamento sem que nenhuma página tenha produzido texto
- **THEN** a extração DEVE ser interrompida e o resultado DEVE ter estado de falha, com texto vazio

#### Scenario: PDF em memória protegido por senha

- **WHEN** um PDF em memória está criptografado e não abre com senha vazia nem com a senha informada
- **THEN** o resultado DEVE ter estado protegido, sem propagar exceção

### Requirement: Tolerância a limite de recursos da biblioteca por página

Quando a extração do texto de uma página falhar com `LimitReachedError`
(subclasse de `PyPdfError`), o sistema NÃO DEVE interromper o documento: DEVE
prosseguir para as páginas seguintes, contabilizar a página como falha e
classificar o resultado como `PARCIAL`. Somente quando nenhuma página produzir
texto o resultado DEVE ser `FALHA`. A exceção NÃO DEVE propagar ao chamador.

#### Scenario: Erro de limite em uma página não descarta as demais
- **WHEN** a extração de uma página falha com `LimitReachedError` e há páginas seguintes legíveis
- **THEN** o sistema DEVE prosseguir para as próximas páginas e o resultado DEVE ser `PARCIAL`, contando a página que falhou

#### Scenario: Erro de limite sem nenhuma página com texto
- **WHEN** todas as páginas falham, inclusive por `LimitReachedError`, sem produzir texto
- **THEN** o resultado DEVE ter estado de falha, com texto vazio e sem propagar a exceção

#### Scenario: Erro de limite em página isolada
- **WHEN** apenas uma página de um PDF legível falha com `LimitReachedError`
- **THEN** o texto das demais páginas DEVE ser preservado e a contagem de páginas com falha DEVE incluir a página afetada

### Requirement: Preservação da classificação de ausência de texto

A classificação de ausência de texto permanece inalterada: um PDF lido com
sucesso cujas páginas não produzem texto DEVE continuar sendo classificado como
`SEM_TEXTO`. Os caminhos de estouro de orçamento e de erro de limite DEVEM
classificar o resultado como `PARCIAL` ou `FALHA`, NUNCA como `SEM_TEXTO`, para
não converter uma extração interrompida em ausência definitiva de texto.

#### Scenario: PDF sem texto permanece sem texto
- **WHEN** um PDF é lido com sucesso e nenhuma página produz texto, dentro do orçamento
- **THEN** o resultado DEVE ter estado `SEM_TEXTO`, como hoje

#### Scenario: Estouro do orçamento não vira ausência definitiva
- **WHEN** a extração de um PDF é interrompida pelo orçamento
- **THEN** o resultado NÃO DEVE ser `SEM_TEXTO` e DEVE ser `PARCIAL` ou `FALHA`

#### Scenario: Falha de limite não vira ausência definitiva
- **WHEN** a extração de um PDF é interrompida por `LimitReachedError` em todas as páginas
- **THEN** o resultado NÃO DEVE ser `SEM_TEXTO` e DEVE ser `FALHA`
