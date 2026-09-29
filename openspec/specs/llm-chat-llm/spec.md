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

### Requirement: Orquestração da cascata em até três chamadas

O sistema DEVE resolver cada pergunta em no máximo duas chamadas de completion por padrão: a primeira com os resumos curtos e longos do escopo; a segunda, quando necessária, com o texto integral dos documentos-alvo. Quando o parâmetro `input_limitado` estiver ativo, o sistema DEVE admitir até três chamadas: a primeira com o manifesto de recursos no lugar dos resumos; a segunda com os recursos iniciais solicitados pela LLM (conhecimento, fundamentos e/ou resumos); e a terceira, quando necessária, com o texto integral dos documentos-alvo. Quando uma chamada já responder de forma conclusiva, as chamadas seguintes NÃO DEVEM ocorrer. Todas as chamadas DEVEM compartilhar o mesmo prefixo estável e o mesmo histórico, diferindo apenas no sufixo.

#### Scenario: Resposta nos resumos
- **WHEN** a primeira chamada devolve uma resposta suficiente
- **THEN** apenas uma chamada de completion DEVE ter sido feita

#### Scenario: Necessidade do texto integral
- **WHEN** a primeira chamada devolve documentos-alvo sem resposta conclusiva
- **THEN** uma segunda chamada DEVE ler o texto integral desses alvos

#### Scenario: Recursos iniciais sob demanda com janela limitada
- **WHEN** `input_limitado` está ativo e a primeira chamada devolve recursos iniciais solicitados
- **THEN** uma segunda chamada DEVE carregar esses recursos, e uma terceira chamada DEVE ler o texto integral dos documentos-alvo quando solicitados

#### Scenario: Resposta conclusiva encerra a cascata
- **WHEN** uma chamada intermediária já responde de forma conclusiva
- **THEN** nenhuma chamada adicional DEVE ocorrer

### Requirement: Contrato de resposta estruturada tolerante

O sistema DEVE solicitar à LLM uma resposta em formato delimitado/JSON contendo a resposta e a lista de chaves de documentos-alvo, e DEVE interpretar a saída de forma tolerante: quando o formato não for reconhecido, a resposta inteira DEVE ser tratada como texto.

#### Scenario: Formato reconhecido
- **WHEN** a LLM responde no formato delimitado com resposta e lista de documentos
- **THEN** o sistema DEVE extrair a resposta e os documentos-alvo

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

O prompt enviado à LLM DEVE ser composto por um **prefixo estável** (instruções e contexto estável) seguido do histórico e de um **sufixo volátil** (fontes adicionais dependentes da pergunta, texto integral da escalada e a pergunta atual). O prefixo estável DEVE ser idêntico byte-a-byte entre turnos enquanto o contexto não mudar, de modo a ser reaproveitado pelo cache de prompt do provedor. Conteúdo volátil NÃO DEVE integrar o prefixo. As duas chamadas da cascata DEVEM compartilhar o mesmo prefixo e histórico, diferindo apenas no sufixo.

#### Scenario: Prefixo idêntico entre turnos

- **WHEN** duas perguntas consecutivas são feitas sem mudança de contexto
- **THEN** o prefixo estável enviado ao provedor DEVE ser byte-a-byte idêntico entre os turnos

#### Scenario: Conteúdo volátil no sufixo

- **WHEN** a pergunta atual e as fontes adicionais (busca vetorial/notícias) são montadas
- **THEN** elas DEVEM ficar após o histórico, sem compor o prefixo estável

#### Scenario: Prefixo compartilhado pelas duas chamadas

- **WHEN** a cascata escala para a segunda chamada com o texto integral dos alvos
- **THEN** as duas chamadas DEVEM compartilhar o prefixo estável e o histórico, e diferir apenas no sufixo

#### Scenario: Contexto alterado reconstrói o prefixo

- **WHEN** o contexto estável muda entre turnos
- **THEN** o prefixo DEVE ser reconstruído com o novo conteúdo, aceitando o cache-miss correspondente

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
