## MODIFIED Requirements

### Requirement: Descarte de duplicata exata na aquisição

Ao baixar um documento ou notícia, o sistema DEVE calcular o hash do conteúdo bruto antes de registrar. Se o hash já estiver registrado no escopo, o sistema NÃO DEVE persistir o novo arquivo nem manter o seu registro, devendo remover qualquer registro parcial já criado para o novo item. Quando o hash ainda não estiver registrado, o sistema DEVE persistir o arquivo e registrar o hash. A regra é "o primeiro hash registrado vence": não há reordenação por data no download. Ao descartar uma duplicata, o sistema DEVE informar ao chamador o caminho relativo canônico do conteúdo já registrado, de modo que a URL de origem possa ser associada ao arquivo existente.

#### Scenario: Duplicata exata é descartada
- **WHEN** um documento ou notícia é baixado e o hash do seu conteúdo já está registrado no escopo
- **THEN** o novo arquivo NÃO DEVE ser gravado e o seu registro NÃO DEVE permanecer

#### Scenario: Caminho canônico exposto no descarte
- **WHEN** um conteúdo é descartado por duplicidade
- **THEN** o caminho relativo canônico do conteúdo já registrado DEVE ser devolvido ao chamador

#### Scenario: Conteúdo novo é registrado
- **WHEN** um documento ou notícia é baixado e o hash do seu conteúdo ainda não está registrado
- **THEN** o arquivo DEVE ser gravado e o hash DEVE ser registrado

#### Scenario: Duplicata entre datas diferentes
- **WHEN** o mesmo conteúdo é servido em datas diferentes, gerando caminhos diferentes no cache
- **THEN** apenas o primeiro caminho registrado DEVE permanecer

#### Scenario: BDR reutiliza os bytes para extração
- **WHEN** o download de um aviso de BDR é identificado como duplicata exata
- **THEN** o arquivo NÃO DEVE ser gravado, mas o conteúdo baixado DEVE continuar disponível para a extração do dividendo
