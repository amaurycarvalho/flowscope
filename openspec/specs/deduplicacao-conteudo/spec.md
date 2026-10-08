# deduplicacao-conteudo Specification

## Purpose
Evitar que o mesmo conteúdo de documento ou notícia seja baixado e registrado mais de uma vez em datas, ids ou URLs diferentes, mantendo apenas um registro por conteúdo.

## Requirements

### Requirement: Registro de hash do conteúdo por escopo

O sistema DEVE calcular o hash SHA-256 do conteúdo bruto de cada documento e notícia persistido e manter um registro de hashes. Para documentos, o registro DEVE ser por ticker e compartilhado entre as raízes de cache de documentos (`bdr/`, `informe-mensal/` e `documentos-relevantes/`). Para notícias, o registro DEVE ser único e global (escopo `NOTICIAS`), deduplicando inclusive entre as categorias de topo. O registro DEVE ser gravado de forma atômica e a leitura DEVE tolerar ausência e corrupção.

#### Scenario: Documento registrado por ticker
- **WHEN** um documento de um ticker é persistido com sucesso
- **THEN** o hash do seu conteúdo DEVE ser registrado para aquele ticker

#### Scenario: Raízes de documentos compartilham o registro
- **WHEN** dois documentos do mesmo ticker, em raízes diferentes, têm o mesmo conteúdo
- **THEN** o segundo DEVE ser tratado como duplicata do primeiro

#### Scenario: Notícias em escopo global
- **WHEN** o mesmo conteúdo aparece em categorias de topo diferentes das notícias
- **THEN** o segundo DEVE ser tratado como duplicata do primeiro

#### Scenario: Registro ausente ou corrompido
- **WHEN** o arquivo do registro não existe ou contém JSON inválido
- **THEN** a leitura DEVE resultar em registro vazio, sem erro

### Requirement: Descarte de duplicata exata na aquisição

Ao baixar um documento ou notícia, o sistema DEVE calcular o hash do conteúdo bruto antes de registrar. Se o hash já estiver registrado no escopo, o sistema NÃO DEVE persistir o novo arquivo nem manter o seu registro, devendo remover qualquer registro parcial já criado para o novo item. Quando o hash ainda não estiver registrado, o sistema DEVE persistir o arquivo e registrar o hash. A regra é "o primeiro hash registrado vence": não há reordenação por data no download.

#### Scenario: Duplicata exata é descartada
- **WHEN** um documento ou notícia é baixado e o hash do seu conteúdo já está registrado no escopo
- **THEN** o novo arquivo NÃO DEVE ser gravado e o seu registro NÃO DEVE permanecer

#### Scenario: Conteúdo novo é registrado
- **WHEN** um documento ou notícia é baixado e o hash do seu conteúdo ainda não está registrado
- **THEN** o arquivo DEVE ser gravado e o hash DEVE ser registrado

#### Scenario: Duplicata entre datas diferentes
- **WHEN** o mesmo conteúdo é servido em datas diferentes, gerando caminhos diferentes no cache
- **THEN** apenas o primeiro caminho registrado DEVE permanecer

#### Scenario: BDR reutiliza os bytes para extração
- **WHEN** o download de um aviso de BDR é identificado como duplicata exata
- **THEN** o arquivo NÃO DEVE ser gravado, mas o conteúdo baixado DEVE continuar disponível para a extração do dividendo

### Requirement: Validação do registro canônico

O sistema DEVE considerar o arquivo associado a um hash como o seu canônico. Se o arquivo canônico não existir mais no disco, o hash correspondente DEVE ser removido do registro e um novo arquivo com aquele conteúdo DEVE poder ser registrado normalmente.

#### Scenario: Canônico removido manualmente
- **WHEN** o hash está registrado, mas o arquivo canônico não existe mais no disco
- **THEN** o hash DEVE ser descartado e o novo arquivo DEVE ser registrado

#### Scenario: Canônico ainda existe
- **WHEN** o hash está registrado e o arquivo canônico existe no disco
- **THEN** o novo conteúdo idêntico DEVE ser considerado duplicata

### Requirement: Poda dos derivados do item descartado

Ao remover um arquivo por deduplicação, o sistema DEVE remover também os registros derivados daquele item: a entrada de resumo, a entrada de texto e, para notícias, a entrada correspondente no índice de metadados. Para documentos, o resumo e o texto DEVEM ser removidos do escopo do ticker; para notícias, do shard de ano e mês correspondente. A remoção NÃO DEVE afetar os derivados de outros itens.

#### Scenario: Resumo e texto removidos
- **WHEN** um arquivo é descartado por duplicação e possui resumo ou texto em cache
- **THEN** as entradas correspondentes DEVEM ser removidas dos stores

#### Scenario: Entrada de índice de notícia removida
- **WHEN** uma notícia é descartada por duplicação
- **THEN** a entrada correspondente DEVE ser removida do índice de metadados de notícias

#### Scenario: Demais itens preservados
- **WHEN** os derivados de um item descartado são removidos
- **THEN** os resumos e textos dos demais itens DEVEM permanecer inalterados

### Requirement: Guarda de conteúdo

O sistema NÃO DEVE registrar o hash de conteúdos vazios, compostos apenas por espaços ou abaixo de um piso mínimo de tamanho, para evitar que conteúdos genéricos curtos provoquem o descarte indevido de arquivos distintos.

#### Scenario: Conteúdo vazio não registra
- **WHEN** o conteúdo baixado é vazio ou composto apenas por espaços
- **THEN** o hash NÃO DEVE ser registrado

#### Scenario: Conteúdo abaixo do piso não registra
- **WHEN** o conteúdo baixado tem tamanho abaixo do piso mínimo
- **THEN** o hash NÃO DEVE ser registrado

### Requirement: Housekeeping de deduplicação por "Atualizar"

Ao acionar "Atualizar" na sub-aba "Documentos" (por ticker) ou "Notícias" (global), o sistema DEVE localizar os arquivos em cache que ainda não possuem hash, calcular o hash do conteúdo de cada um e aplicar a mesma regra de descarte. A varredura DEVE percorrer os arquivos em ordem cronológica, do mais antigo para o mais recente, de modo que o sobrevivente da deduplicação de duplicatas legadas seja o mais antigo. A falha ao processar um arquivo NÃO DEVE interromper o housekeeping dos demais.

#### Scenario: Arquivo legado sem hash é calculado
- **WHEN** "Atualizar" é acionado e há arquivos em cache sem hash registrado
- **THEN** o hash de cada arquivo DEVE ser calculado e aplicado à regra de deduplicação

#### Scenario: Duplicatas legadas mantêm o mais antigo
- **WHEN** há dois arquivos legados com o mesmo conteúdo e nenhum hash registrado
- **THEN** o mais antigo DEVE permanecer e o mais recente DEVE ser removido, junto com seus derivados

#### Scenario: Falha isolada não interrompe
- **WHEN** o cálculo do hash ou a remoção de um arquivo falha
- **THEN** o housekeeping DEVE continuar com os demais arquivos, sem erro fatal

#### Scenario: Atualizar de documentos por ticker
- **WHEN** "Atualizar" é acionado na sub-aba "Documentos"
- **THEN** o housekeeping DEVE varrer apenas os documentos do ticker apresentado

#### Scenario: Atualizar de notícias global
- **WHEN** "Atualizar" é acionado na sub-aba "Notícias"
- **THEN** o housekeeping DEVE varrer todas as notícias em cache
