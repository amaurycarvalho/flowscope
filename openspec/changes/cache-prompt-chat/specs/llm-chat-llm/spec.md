## ADDED Requirements

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
