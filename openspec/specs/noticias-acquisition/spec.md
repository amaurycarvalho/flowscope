# noticias-acquisition Specification

## Purpose

Lista as notícias do Plantão B3 e as informações regulatórias e de mercado da RFC-004 (censuras públicas, condições excepcionais e programas de aquisição de ações), baixa o corpo de cada item quando houver URL e mantém um cache local do conteúdo para exibição e resumo.

## Requirements

### Requirement: Listagem das notícias

O sistema DEVE listar as notícias do Plantão B3 do **último ano** e com o filtro de palavra informado, mantendo somente casos excepcionais de mercado, e retornando título, data de publicação, agência e URL. A leitura DEVE ser feita **um dia por vez**. A listagem DEVE tolerar indisponibilidade sem interromper a interface.

#### Scenario: Notícias do período
- **WHEN** a listagem é solicitada para um período com notícias
- **THEN** as notícias DEVEM ser retornadas com título, data, agência e URL

#### Scenario: Período de um ano
- **WHEN** a listagem é solicitada a partir de uma data de referência
- **THEN** apenas as notícias do último ano DEVEM ser consideradas

#### Scenario: Consulta dia a dia
- **WHEN** o último ano é lido
- **THEN** a leitura DEVE consultar um dia por vez e os resultados DEVEM ser acumulados e deduplicados

### Requirement: Carga incremental da "Geral"

A carga da "Geral" DEVE ser feita **dia a dia**, do mais recente ao mais antigo, e DEVE persistir a **data mais antiga já processada** e a **referência da última carga**. O dia mais recente DEVE ser sempre recarregado; os dias mais antigos SÓ DEVEM ser lidos a partir da data mais antiga processada; e a lacuna entre a referência anterior e o dia mais recente DEVE ser preenchida. Os marcadores DEVEM ser atualizados a cada dia concluído, inclusive quando o dia não tiver notícia excepcional, de modo que dias já baixados com sucesso sejam pulados individualmente.

#### Scenario: Dia mais recente sempre recarregado
- **WHEN** a "Geral" é carregada novamente
- **THEN** o dia mais recente DEVE ser relido

#### Scenario: Dias antigos já processados são pulados
- **WHEN** a data mais antiga processada já cobre o período de um ano
- **THEN** nenhum dia antigo DEVE ser relido

#### Scenario: Data de referência avançou
- **WHEN** a data de referência avançou desde a última carga
- **THEN** a lacuna entre a referência anterior e o dia mais recente DEVE ser preenchida dia a dia

#### Scenario: Dia sem notícia excepcional
- **WHEN** um dia é processado e nenhuma notícia excepcional é encontrada
- **THEN** o marcador DEVE registrar o dia como processado, evitando relê-lo

#### Scenario: Falha em um dia
- **WHEN** a listagem de um dia falha
- **THEN** o dia NÃO DEVE ser marcado como processado e a carga DEVE ser retomada dele na próxima vez

#### Scenario: Falha de listagem
- **WHEN** a listagem falha por indisponibilidade de rede
- **THEN** uma lista vazia DEVE ser retornada sem erro fatal

### Requirement: Inclusão de casos excepcionais

O sistema DEVE carregar apenas notícias cujo título corresponda a um evento de mercado excepcional (fora da curva), com correspondência insensível a caixa e acentos e com fronteira de palavra. Os eventos incluem: suspensão/reabertura/retirada de negociação, negociação não contínua, início/prorrogação/adiamento de negociação, incorporação, fusão, cisão, reorganização, recuperação judicial/extrajudicial, falência, liquidação, intervenção, grupamento, desdobramento, bonificação, redução/aumento de capital, amortização, deslistagem/cancelamento de listagem/cancelamento de registro, conversão de categoria, oferta pública, OPA, modificação de oferta, aquisição/alienação de participação, direito de preferência, mudança de auditor, ato homologatório, transação entre partes relacionadas, esclarecimentos (CVM/B3) e oscilação atípica. NÃO DEVEM ser incluídos: os anúncios de distribuição, a liberação de negociação das cotas, a subscrição privada, os boletins diários de situação especial/alterações do pregão e o fato relevante. A lista de termos vigente é mantida (sem ampliação nem restrição nesta change).

#### Scenario: Notícia rotineira ignorada
- **WHEN** uma notícia do período tem título que não corresponde a um evento excepcional (por exemplo, informe mensal, ata de assembleia, comunicado ao mercado, relatório gerencial, anúncio de distribuição, liberação de negociação das cotas, subscrição privada, boletim de situação especial, alterações do pregão ou fato relevante)
- **THEN** ela NÃO DEVE ser baixada nem exibida

#### Scenario: Notícia excepcional carregada
- **WHEN** uma notícia do período tem título que corresponde a um evento excepcional (por exemplo, "Suspensão de negociação", "Incorporação" ou "Aquisição de participação acionária")
- **THEN** ela DEVE ser carregada

#### Scenario: Correspondência tolerante e com fronteira de palavra
- **WHEN** o título varia em caixa ou acentuação (por exemplo, "SUSPENSAO DE NEGOCIACAO") ou contém a sigla `OPA` isolada
- **THEN** a inclusão DEVE ser aplicada, sem casar `OPA` dentro de outras palavras como "administração para"

### Requirement: Categorias de topo da sub-aba

O sistema DEVE organizar a sub-aba em quatro categorias de topo, na ordem: **"Censuras Públicas"**, **"Condições Excepcionais"**, **"Programas de Aquisição de Ações"** e, por último, **"Geral"**. A categoria "Geral" reúne as notícias do Plantão B3 no último ano (12 meses); as demais são as fontes regulatórias da RFC-004 e DEVEM ser carregadas com o **histórico completo** da fonte, sem corte de 12 meses.

#### Scenario: Categorias presentes
- **WHEN** a sub-aba é exibida com itens em cache
- **THEN** cada categoria com itens DEVE aparecer como nó de topo sob a raiz "Notícias"

#### Scenario: "Geral" por último
- **WHEN** os itens das quatro fontes são listados para carga e exibição
- **THEN** a categoria "Geral" DEVE ser processada e exibida depois das categorias regulatórias, pois é a carga mais pesada

#### Scenario: Histórico completo das fontes regulatórias
- **WHEN** as censuras, condições excepcionais e programas de aquisição são carregados
- **THEN** todos os itens retornados pela fonte DEVEM ser considerados, independentemente da data de publicação

#### Scenario: Categoria vazia
- **WHEN** uma das categorias não tem itens
- **THEN** ela NÃO DEVE ser exibida, sem erro

### Requirement: Aquisição das fontes regulatórias

O sistema DEVE carregar as censuras públicas, as condições excepcionais e os programas de aquisição de ações por meio do `RegulacaoRepository` e tolerar a indisponibilidade de cada fonte sem interromper as demais nem a categoria "Geral". A leitura dos programas DEVE usar retry, pois o endpoint responde 404 de forma intermitente.

#### Scenario: Fontes carregadas
- **WHEN** as páginas e o endpoint das fontes regulatórias estão acessíveis
- **THEN** censuras, condições excepcionais e programas DEVEM ser convertidos em itens da sub-aba

#### Scenario: Falha de uma fonte
- **WHEN** uma das fontes regulatórias falha
- **THEN** as demais fontes e a categoria "Geral" DEVEM continuar

#### Scenario: Retry dos programas
- **WHEN** o endpoint de programas responde 404 numa tentativa
- **THEN** a leitura DEVE tentar novamente antes de desistir

### Requirement: Aquisição do corpo do item

O sistema DEVE baixar o corpo de cada notícia a partir da sua URL quando ela existir e, quando NÃO houver URL, usar o próprio item como conteúdo. A aquisição DEVE tolerar falha por item (sem conteúdo ou erro de rede) sem interromper os demais, reportar progresso e respeitar cancelamento.

#### Scenario: Item com URL baixado
- **WHEN** uma notícia do Plantão B3 tem URL acessível
- **THEN** o corpo do artigo DEVE ser baixado e gravado no cache

#### Scenario: Item sem URL usa o próprio conteúdo
- **WHEN** uma censura, condição excepcional ou programa de aquisição não tem URL
- **THEN** o próprio item DEVE ser gravado como conteúdo no cache

#### Scenario: Falha em um item
- **WHEN** o download de um artigo falha
- **THEN** os demais itens DEVEM continuar e o erro DEVE ser registrado no log

#### Scenario: Notícia do Plantão sem URL
- **WHEN** uma notícia do Plantão B3 não tem URL
- **THEN** ela DEVE ser ignorada na aquisição, sem erro

### Requirement: Cache das notícias

O sistema DEVE manter um cache próprio do HTML dos itens, independente do cache de listagem, com uma chave estável derivada de URL ou, na ausência desta, de uma identidade estável do item (seção, data, categoria e título). O cache NÃO DEVE ser sobrescrito quando já existir conteúdo para a mesma chave.

#### Scenario: Reexecução sem rebaixar
- **WHEN** a aquisição é executada novamente para o mesmo item já em cache
- **THEN** o corpo já cacheado NÃO DEVE ser baixado de novo

#### Scenario: Chave estável sem URL
- **WHEN** o item não tem URL
- **THEN** a chave DEVE ser derivada da identidade estável do item

### Requirement: Cache das fontes regulatórias

As páginas de listagem das fontes regulatórias ("Censuras Públicas", "Condições Excepcionais" e "Programas de Aquisição de Ações") DEVEM usar o cache HTTP com validade própria, de modo que um novo "Atualizar" dentro do período de validade NÃO rebaixe a listagem. O corpo dos itens regulatórios (sem URL, gerado localmente) NÃO DEVE ser reescrito quando já existir em cache. O sistema PODE reler a listagem do cache e reindexar os itens a cada carga, sem novo download.

#### Scenario: Listagem servida do cache
- **WHEN** "Atualizar" é acionado dentro do período de validade do cache da listagem
- **THEN** as páginas das fontes regulatórias NÃO DEVEM ser baixadas novamente

#### Scenario: Corpo regulatório não reescrito
- **WHEN** um item regulatório já tem HTML em cache
- **THEN** o HTML NÃO DEVE ser regravado

#### Scenario: Cache expirado
- **WHEN** o período de validade da listagem expira
- **THEN** a listagem DEVE ser baixada novamente para captar itens novos

### Requirement: Índice de metadados para exibição sem rede

A aquisição DEVE gravar, em um índice sob a raiz de cache, os metadados de exibição de cada item com corpo em cache — seção, título, data de publicação, categoria e URL — indexados pelo caminho relativo do HTML. O índice DEVE ser gravado de forma atômica e lido de forma tolerante a ausência e corrupção. Os metadados DEVEM ser registrados também quando o corpo já existe em cache, de modo que uma reexecução repare um índice ausente sem rebaixar o conteúdo.

#### Scenario: Índice gravado na aquisição
- **WHEN** um item é adquirido com sucesso
- **THEN** os seus metadados DEVEM constar do índice

#### Scenario: Reexecução repara o índice
- **WHEN** o índice é apagado e a aquisição é executada novamente
- **THEN** o corpo já em cache NÃO DEVE ser rebaixado e o índice DEVE ser reconstruído

#### Scenario: Cancelamento preserva o que foi processado
- **WHEN** a aquisição é cancelada após processar alguns itens
- **THEN** os metadados de cada item já processado DEVEM estar gravados no índice, permitindo exibir a carga parcial

### Requirement: Gravação do índice em lotes

A aquisição DEVE agrupar as escritas do índice em vez de regravá-lo a cada item ou dia. As fontes regulatórias e a "Geral" DEVEM acumular os registros e gravar o índice periodicamente e ao final da carga. Em cancelamento, os registros já acumulados DEVEM ser gravados; na "Geral", sem marcar o dia em andamento, para que ele seja retomado.

#### Scenario: Escritas agrupadas
- **WHEN** uma fonte regulatória ou a "Geral" é carregada
- **THEN** o índice DEVE ser gravado em intervalos (lotes de itens/dias) e ao final, e não a cada unidade

#### Scenario: Cancelamento preserva o lote acumulado
- **WHEN** a carga é cancelada com registros acumulados
- **THEN** esses registros DEVEM ser gravados, preservando a carga parcial

### Requirement: Progresso por categoria

A aquisição DEVE anunciar, na barra de status, cada categoria antes de consultá-la ("Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição de Ações" e "Geral") e DEVE reportar o progresso por item identificando a categoria em carga. Os metadados dos itens DEVEM ser indexados à medida que são processados, para que a interrupção preserve a carga parcial.

#### Scenario: Status da categoria ao carregar
- **WHEN** a aquisição inicia a carga de uma categoria
- **THEN** a barra de status DEVE exibir o nome da categoria antes da listagem

#### Scenario: Progresso por item identificando a categoria
- **WHEN** os itens de uma categoria são processados
- **THEN** o progresso DEVE indicar o nome da categoria e a contagem de itens

#### Scenario: Índice à medida do processamento
- **WHEN** um item é processado
- **THEN** os seus metadados DEVEM ser gravados no índice antes do item seguinte
