# conditional-data-cache Specification

## Purpose
Mecanismo genérico de cache condicional que revalida dados de fontes externas por validadores plugáveis, separa as políticas de frescor, revalidação e retenção, e reporta o resultado de cada consulta para as camadas consumidoras.

## Requirements

### Requirement: Revalidação condicional por validador plugável

O sistema DEVE permitir associar a cada chave de cache um validador que decide, contra a fonte remota, se o valor armazenado permanece válido, se foi alterado ou se não pôde ser verificado.

#### Scenario: Valor inalterado na fonte

- **WHEN** o validador indica que o valor remoto é igual ao armazenado
- **THEN** o sistema DEVE servir o valor em cache sem reprocessá-lo e registrar o resultado como "inalterado"

#### Scenario: Valor alterado na fonte

- **WHEN** o validador indica que o valor remoto mudou
- **THEN** o sistema DEVE buscar, processar e substituir o valor em cache

#### Scenario: Verificação indisponível

- **WHEN** o validador não consegue determinar o estado remoto
- **THEN** o sistema DEVE aplicar a política de frescor e, se expirada, realizar a aquisição completa

### Requirement: Separação entre frescor, revalidação e retenção

O sistema DEVE tratar como políticas independentes o frescor (idade máxima para considerar o valor válido sem rede), o intervalo de revalidação (tempo mínimo entre checagens remotas) e a retenção (quando remover o registro do armazenamento).

#### Scenario: Serve sem rede enquanto fresco

- **WHEN** o valor em cache é considerado fresco
- **THEN** o sistema DEVE servi-lo sem realizar requisição à fonte remota

#### Scenario: Coalescência de checagens

- **WHEN** o valor não é fresco, mas o intervalo mínimo entre revalidações ainda não venceu
- **THEN** o sistema DEVE servir o cache sem nova checagem remota

#### Scenario: Retenção vencida

- **WHEN** o prazo de retenção de um registro vence
- **THEN** o sistema DEVE remover o registro do armazenamento

### Requirement: Chave de cache versionada

O sistema DEVE vincular cada registro à versão do parser ou schema que o produziu, de modo que uma mudança de versão invalide valores gerados por versões anteriores.

#### Scenario: Versão do parser alterada

- **WHEN** a versão atual do parser difere da versão registrada no cache
- **THEN** o registro DEVE ser tratado como ausente e a fonte DEVE ser reprocessada

### Requirement: Persistência atômica e tolerância a corrupção

O sistema DEVE gravar os registros de cache de forma atômica e DEVE tratar registro ausente, expirado ou corrompido como ausência de cache.

#### Scenario: Registro corrompido

- **WHEN** o registro em disco não puder ser interpretado
- **THEN** o sistema DEVE tratá-lo como ausente e refazer a aquisição

#### Scenario: Escrita atômica

- **WHEN** um registro é gravado
- **THEN** o sistema DEVE escrever em arquivo temporário e renomeá-lo para o destino

### Requirement: Resultado do cache reportado ao chamador

O sistema DEVE devolver, junto ao valor, o resultado da consulta, distinguindo ao menos cache servido, valor revalidado e valor atualizado, para que as camadas consumidoras reajam sem acoplar infraestrutura à apresentação.

#### Scenario: Valor atualizado

- **WHEN** a fonte remota forneceu um valor novo
- **THEN** o resultado reportado DEVE indicar atualização

#### Scenario: Cache servido

- **WHEN** o valor foi servido do armazenamento sem atualização
- **THEN** o resultado reportado DEVE indicar cache

### Requirement: Revalidação tolerante a falha

O sistema DEVE servir o valor armazenado quando a revalidação remota falhar por indisponibilidade, desde que exista um valor em cache.

#### Scenario: Falha de rede na revalidação

- **WHEN** a checagem remota falha e existe valor em cache
- **THEN** o sistema DEVE servir o valor armazenado e registrar o aviso
