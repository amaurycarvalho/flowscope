# llm-chat-llm Specification

## Purpose

Orquestra a cascata de recuperação sobre a porta `LLMPort` da `llm-core`, mantendo o número de chamadas baixo e tratando a resposta do modelo de forma tolerante.

## Requirements

### Requirement: Consumo do LLMPort do llm-core

O sistema DEVE consumir a porta `LLMPort`, a factory `create_llm_provider` e `load_llm_config` fornecidas pela change `llm-core`, sem definir cliente, porta ou factory de LLM próprios. A configuração de completion DEVE vir do bloco `llm.chat`.

#### Scenario: Consulta usa o LLMPort
- **WHEN** o caso de uso do chat envia um prompt
- **THEN** a chamada DEVE usar um `LLMPort` criado por `create_llm_provider` a partir de `llm.chat`

#### Scenario: LLM indisponível
- **WHEN** o provedor é `none` ou as dependências `[llm]` estão ausentes
- **THEN** o sistema DEVE propagar `LLMUnavailableError` para a GUI exibir o estado não configurado

### Requirement: Contrato de resposta estruturada tolerante

O sistema DEVE solicitar à LLM uma resposta em JSON estrito no formato `{"resposta": <texto|null>, "solicitacoes": [{"op": ..., ...}]}` e interpretá-la de forma tolerante: quando o formato não for reconhecido, o texto inteiro DEVE ser tratado como resposta final e o loop DEVE encerrar. Quando a lista de solicitações estiver vazia, o campo `resposta` DEVE ser considerado final.

#### Scenario: Formato reconhecido
- **WHEN** a LLM responde no formato com `resposta`/`solicitacoes`
- **THEN** o sistema DEVE extrair a resposta e as solicitações, tratando `resposta` como final quando `solicitacoes` estiver vazia

#### Scenario: Formato não reconhecido
- **WHEN** a resposta não segue o formato esperado
- **THEN** o texto inteiro DEVE ser tratado como resposta, sem nova rodada

### Requirement: Prompt de sistema

O prompt DEVE instruir a LLM a responder apenas com base no contexto fornecido, a citar as fontes usadas, a identificar o ticker referido na pergunta e a admitir quando não houver informação suficiente.

#### Scenario: Instruções no prompt
- **WHEN** o prompt é construído
- **THEN** ele DEVE conter as instruções de restringir-se ao contexto, citar fontes, identificar o ticker e admitir insuficiência

### Requirement: Histórico da conversa no prompt

O sistema DEVE enviar à LLM os turnos anteriores bem-sucedidos da sessão (`user` e `assistant`) em ordem cronológica, como mensagens separadas, antecedendo a mensagem do turno atual. As duas chamadas da cascata DEVEM compartilhar o mesmo histórico. Mensagens marcadas como fora do histórico (erros e avisos) NÃO DEVEM ser enviadas. O envelope JSON e as chaves de documentos da resposta NÃO DEVEM integrar o histórico — apenas o texto final exibido. O histórico DEVE respeitar um teto de 10 mensagens e 8.000 caracteres, descartando os turnos mais antigos quando excedido.

#### Scenario: Histórico enviado
- **WHEN** há turnos anteriores na sessão e uma nova pergunta é feita
- **THEN** as mensagens anteriores DEVEM ser enviadas em ordem, antes da pergunta atual

#### Scenario: Ambos os níveis da cascata herdam o histórico
- **WHEN** a cascata escala para a segunda chamada com o texto integral dos alvos
- **THEN** a segunda chamada DEVE receber o mesmo histórico da primeira

#### Scenario: Erros fora do histórico
- **WHEN** uma mensagem de erro ou aviso da LLM está registrada na sessão
- **THEN** ela NÃO DEVE ser enviada ao modelo

#### Scenario: Teto do histórico
- **WHEN** o histórico ultrapassa 10 mensagens ou 8.000 caracteres
- **THEN** os turnos mais antigos DEVEM ser descartados, preservando os mais recentes

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

### Requirement: Estimativa determinística de cache de prompt

Quando o provedor não reportar tokens de cache-hit em uma completion, o sistema DEVE estimar de forma determinística os tokens servidos por cache e preencher `LLMUsage.entrada_cache` antes de contabilizar o uso. A estimativa DEVE ocorrer somente quando (a) o provedor suportar cache de prompt e (b) o prefixo estável enviado for idêntico byte-a-byte ao de uma completion anterior. O valor estimado DEVE ser a contagem de tokens do prefixo estável (prompt de sistema, instrução de formato e bloco estável) e DEVE ser reutilizado por assinatura, sem recontagem a cada turno. A estimativa NÃO DEVE ser aplicada sobre tokens de cache-write.

#### Scenario: Prefixo inalterado estima o cache

- **WHEN** o prefixo estável é idêntico ao de uma completion anterior, o provedor suporta cache e não reporta cache-hit
- **THEN** `entrada_cache` DEVE ser preenchido com a contagem de tokens do prefixo estável

#### Scenario: Primeira completion não estima

- **WHEN** não há completion anterior com o mesmo prefixo estável na sessão
- **THEN** nenhuma estimativa de cache DEVE ser aplicada

#### Scenario: Prefixo alterado não estima

- **WHEN** o contexto estável mudou e o prefixo foi reconstruído
- **THEN** nenhuma estimativa de cache DEVE ser aplicada nessa completion

#### Scenario: Provedor sem suporte não estima

- **WHEN** o provedor não suporta cache de prompt e não reporta cache-hit
- **THEN** nenhuma estimativa DEVE ser aplicada e `entrada_cache` DEVE permanecer zero

#### Scenario: Cache reportado pelo provedor tem precedência

- **WHEN** o provedor reporta tokens de cache-hit
- **THEN** o valor reportado DEVE ser usado e nenhuma estimativa DEVE substituí-lo

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
