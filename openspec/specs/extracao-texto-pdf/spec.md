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
