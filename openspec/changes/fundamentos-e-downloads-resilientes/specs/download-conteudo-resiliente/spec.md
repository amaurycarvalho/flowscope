## Purpose

Aquisição compartilhada de arquivos (PDF e HTML) de hosts externos com validação de conteúdo, orçamento total por item e sessão/token renovável, tolerando indisponibilidade sem interromper a aquisição das demais unidades.

## ADDED Requirements

### Requirement: Validação de conteúdo no download

O sistema DEVE validar o conteúdo baixado antes de persisti-lo: um PDF DEVE começar com a assinatura `%PDF` e um HTML esperado DEVE ser reconhecido como tal. Uma resposta HTTP de sucesso (`2xx`) cujo conteúdo não corresponda ao esperado NÃO DEVE ser aceita como válida; o item DEVE ser repetido enquanto houver tentativas no orçamento e, ao esgotá-las, a falha DEVE ser sinalizada para aquele item, sem gravar arquivo inválido.

#### Scenario: PDF válido é aceito
- **WHEN** o download de um PDF conclui com `2xx` e o conteúdo começa com `%PDF`
- **THEN** o conteúdo DEVE ser aceito para persistência

#### Scenario: Resposta 2xx não-PDF é repetida
- **WHEN** uma resposta `2xx` de um endpoint de PDF traz conteúdo que não começa com `%PDF`
- **THEN** o sistema DEVE repetir a aquisição e, se o orçamento se esgotar sem PDF válido, sinalizar a falha sem gravar arquivo

#### Scenario: HTML esperado é aceito
- **WHEN** o download de um documento HTML conclui com `2xx` e o conteúdo é um HTML reconhecível
- **THEN** o conteúdo DEVE ser aceito para persistência

### Requirement: Orçamento total por item no download

O download de um item DEVE respeitar um orçamento total que cobre conexão, tentativas e esperas entre tentativas, independentemente do número de tentativas. Ao esgotar o orçamento, o sistema DEVE interromper a aquisição daquele item, sinalizar a falha sem criar arquivo e NÃO DEVE propagar a falha para os demais itens. O orçamento DEVE observar o pedido de cancelamento da operação.

#### Scenario: Conclusão dentro do orçamento
- **WHEN** o download conclui dentro do orçamento total do item
- **THEN** o conteúdo DEVE ser entregue normalmente

#### Scenario: Orçamento esgotado mantém o item ausente
- **WHEN** o host fica indisponível até o orçamento total se esgotar
- **THEN** o item DEVE ficar ausente, a falha DEVE ser sinalizada e os demais itens DEVEM prosseguir

#### Scenario: Cancelamento interrompe o orçamento
- **WHEN** há um pedido de cancelamento durante o download de um item
- **THEN** a aquisição daquele item DEVE ser interrompida

### Requirement: Repetição de status intermitente por ponto de chamada

O motor de repetição DEVE permitir que um ponto de chamada marque códigos normalmente permanentes como repetíveis quando comprovadamente intermitentes naquele endpoint. O host do FNET, que responde `403` de forma intermitente ao visualizador, DEVE declarar esse override no ponto de chamada; fora desse ponto, o `403` permanece permanente.

#### Scenario: 403 intermitente do FNET é repetido
- **WHEN** o visualizador do FNET responde `403` no ponto de chamada que declara o override e uma tentativa seguinte sucede
- **THEN** o conteúdo DEVE ser obtido sem propagar a falha

#### Scenario: 403 sem override não é repetido
- **WHEN** um ponto de chamada sem override recebe `403`
- **THEN** a requisição NÃO DEVE ser repetida

### Requirement: Renovação de sessão no visualizador da CVM

A resolução de um documento no visualizador da CVM RAD obtém um token/sessão a partir da página do documento e então solicita o PDF. Quando a solicitação do PDF falhar repetidamente, o sistema DEVE re-obter a página (renovando token/sessão) antes de nova tentativa do PDF, respeitando o orçamento do item.

#### Scenario: Falha repetida renova a sessão
- **WHEN** o pedido do PDF ao visualizador da CVM falha com erro transitório
- **THEN** o sistema DEVE re-obter a página do documento e repetir o pedido do PDF
