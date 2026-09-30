## REMOVED Requirements

### Requirement: Orquestração da cascata em até três chamadas

**Reason**: A cascata de até três chamadas (resumos → recursos → texto integral) é substituída por um loop de navegação da árvore de conhecimento.

**Migration**: Substituído por "Loop de navegação sobre a árvore", que executa ciclos de navegação até a resposta conclusiva.

## MODIFIED Requirements

### Requirement: Contrato de resposta estruturada tolerante

O sistema DEVE solicitar à LLM uma resposta em JSON estrito no formato `{"resposta": <texto|null>, "solicitacoes": [{"op": ..., ...}]}` e interpretá-la de forma tolerante: quando o formato não for reconhecido, o texto inteiro DEVE ser tratado como resposta final e o loop DEVE encerrar. Quando a lista de solicitações estiver vazia, o campo `resposta` DEVE ser considerado final.

#### Scenario: Formato reconhecido
- **WHEN** a LLM responde no formato com `resposta`/`solicitacoes`
- **THEN** o sistema DEVE extrair a resposta e as solicitações, tratando `resposta` como final quando `solicitacoes` estiver vazia

#### Scenario: Formato não reconhecido
- **WHEN** a resposta não segue o formato esperado
- **THEN** o texto inteiro DEVE ser tratado como resposta, sem nova rodada

### Requirement: Prefixo estável para cache de prompt

O prompt enviado à LLM DEVE ser composto por um **prefixo estável** (instruções e manifesto da árvore) seguido do histórico de diálogo, da navegação acumulada e do turno de navegação corrente. O prefixo estável DEVE ser idêntico byte-a-byte entre turnos e ciclos enquanto a assinatura do estado não mudar, de modo a ser reaproveitado pelo cache de prompt do provedor. Conteúdo volátil (resultados de navegação e a pergunta) NÃO DEVE integrar o prefixo. Todos os ciclos do loop DEVEM compartilhar o mesmo prefixo.

#### Scenario: Prefixo idêntico entre turnos
- **WHEN** duas perguntas consecutivas são feitas sem mudança de estado
- **THEN** o prefixo estável enviado ao provedor DEVE ser byte-a-byte idêntico entre os turnos

#### Scenario: Conteúdo volátil no sufixo
- **WHEN** a pergunta atual e as fontes adicionais são montadas
- **THEN** elas DEVEM ficar após o histórico, sem compor o prefixo estável

#### Scenario: Prefixo compartilhado pelas duas chamadas
- **WHEN** o loop executa múltiplos ciclos de navegação
- **THEN** todos os ciclos DEVEM compartilhar o prefixo estável e o histórico, e diferir apenas no sufixo

#### Scenario: Contexto alterado reconstrói o prefixo
- **WHEN** a assinatura do estado muda entre turnos
- **THEN** o prefixo DEVE ser reconstruído com o novo manifesto, aceitando o cache-miss correspondente

#### Scenario: Histórico continua antecedendo o turno atual
- **WHEN** o prompt é montado com histórico
- **THEN** os turnos anteriores DEVEM permanecer entre o prefixo estável e o sufixo volátil

## ADDED Requirements

### Requirement: Loop de navegação sobre a árvore

O sistema DEVE resolver cada pergunta por um loop de navegação de até 10 ciclos sobre a porta `LLMPort`. Em cada ciclo, o sistema DEVE enviar a completion, extrair o JSON da resposta, encerrar quando a resposta for conclusiva (lista de solicitações vazia) e, caso contrário, validar e executar as solicitações, devolvendo o resultado à LLM no ciclo seguinte. Todas as chamadas DEVEM compartilhar o mesmo prefixo estável (manifesto), o mesmo histórico de diálogo e a navegação acumulada, diferindo apenas no turno corrente. Erros de protocolo e negativas NÃO DEVEM encerrar o loop e DEVEM contabilizar a iteração. Ao esgotar as iterações, o sistema DEVE exigir um resumo final do que já foi navegado.

#### Scenario: Resposta no primeiro ciclo
- **WHEN** a LLM devolve uma resposta conclusiva sem solicitações
- **THEN** apenas uma chamada de completion DEVE ter sido feita

#### Scenario: Navegação antes de responder
- **WHEN** a LLM devolve solicitações sem resposta conclusiva
- **THEN** o sistema DEVE executá-las e devolver o resultado no ciclo seguinte

#### Scenario: Erro de protocolo continua o loop
- **WHEN** a LLM emite uma operação inválida
- **THEN** o sistema DEVE devolver erro estruturado e contabilizar a iteração, sem encerrar o loop

#### Scenario: Limite de iterações exige resumo
- **WHEN** o loop atinge 10 ciclos sem resposta conclusiva
- **THEN** o sistema DEVE exigir o resumo final do que já foi navegado

#### Scenario: Resposta conclusiva encerra
- **WHEN** uma chamada intermediária já responde de forma conclusiva
- **THEN** nenhuma chamada adicional DEVE ocorrer

### Requirement: Gates de tokens e iterações do loop

O sistema DEVE aplicar gates explícitos ao loop: tokens de navegação por turno acima de 64.000 DEVEM pedir autorização ao usuário; a cota acumulada de navegação acima de 32.000 DEVE descartar os pares mais antigos; ao exceder 10 iterações DEVE pedir autorização; mais de 8 operações em um turno DEVEM ser recusadas com erro estruturado; quando a janela total (manifesto + diálogo + navegação) exceder 80% da janela do modelo, o display DEVE destacar alerta. Os limiares DEVEM ser parametrizáveis.

#### Scenario: Teto por turno pede autorização
- **WHEN** um turno de navegação excede 64.000 tokens
- **THEN** o sistema DEVE pedir autorização ao usuário antes de prosseguir

#### Scenario: Cota acumulada descarta em pares
- **WHEN** a navegação acumulada excede 32.000 tokens
- **THEN** os pares mais antigos DEVEM ser descartados em conjunto

#### Scenario: Janela total alerta
- **WHEN** o prompt total excede 80% da janela do modelo
- **THEN** o display DEVE destacar a condição em cor de alerta

### Requirement: Negativa estruturada de navegação

Quando um gate recusar uma solicitação, o sistema DEVE devolver à LLM uma mensagem estruturada `{"negado": true, "motivo": <motivo>, "tokens_solicitados": <n>}` com motivo canônico (`custo`, `limite_iteracoes`, `timeout_regex`, `resultado_truncado`). Quando a LLM repetir o mesmo pedido já negado, o worker NÃO DEVE executá-lo e DEVE devolver erro estruturado, forçando o resumo. O diálogo de confirmação DEVE informar apenas o número adicional de tokens do turno.

#### Scenario: Negativa com motivo
- **WHEN** um gate recusa uma solicitação de navegação
- **THEN** o worker DEVE devolver a negativa estruturada com o motivo canônico e os tokens solicitados

#### Scenario: Repetição do pedido negado
- **WHEN** a LLM repete um pedido já negado
- **THEN** o worker NÃO DEVE executá-lo e DEVE devolver erro estruturado forçando o resumo

#### Scenario: Confirmação informa somente tokens
- **WHEN** o sistema pede autorização ao usuário
- **THEN** o diálogo DEVE informar apenas o número adicional de tokens do turno
