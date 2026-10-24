## ADDED Requirements

### Requirement: Atualização manual também adquire títulos de renda fixa

O botão "Atualizar" da sub-aba "Documentos" DEVE acionar, no mesmo fluxo de trabalho fora da thread da interface, a aquisição de documentos e a aquisição de títulos de renda fixa. As duas aquisições DEVEM ser internamente separadas, com progresso e desfecho próprios, e a falha de uma NÃO DEVE impedir a conclusão da outra.

A aquisição de títulos DEVE ser explícita, idempotente e cache-aware: DEVE reutilizar os ZIPs anuais da CVM e o JSON por ticker já existentes, DEVE evitar reescrever cache cuja assinatura não mudou e DEVE preservar o último cache válido quando uma fonte falhar.

#### Scenario: Documentos e títulos adquiridos
- **WHEN** o usuário aciona "Atualizar" para um ticker com fontes disponíveis
- **THEN** o sistema DEVE adquirir os documentos e os títulos e remontar a árvore ao final

#### Scenario: Títulos reutilizados do cache
- **WHEN** o JSON de títulos do ticker já existe e a assinatura não mudou
- **THEN** o sistema DEVE reutilizar o cache de títulos sem reescrevê-lo

#### Scenario: Falha de títulos não impede documentos
- **WHEN** a aquisição de títulos falha
- **THEN** a aquisição de documentos DEVE concluir e a árvore DEVE manter os títulos do último cache válido

#### Scenario: Falha de documentos não impede títulos
- **WHEN** a aquisição de documentos falha
- **THEN** a aquisição de títulos DEVE concluir e a árvore DEVE ser remontada com os dados disponíveis

#### Scenario: Ticker sem CNPJ resolvido
- **WHEN** o ticker não tem CNPJ resolvido para renda fixa
- **THEN** a etapa de títulos DEVE terminar sem download e sem erro fatal

#### Scenario: Reexecução idempotente
- **WHEN** o usuário aciona "Atualizar" repetidamente sem mudança de fonte
- **THEN** o sistema NÃO DEVE duplicar títulos nem reescrever cache inalterado

### Requirement: Progresso e desfecho distinguem documentos e títulos

O andamento exibido na barra de status e na barra de progresso DEVE identificar se a etapa corrente é de documentos ou de títulos. Ao término, o desfecho DEVE distinguir itens adquiridos, itens reutilizados e falhas de cada etapa, sem afirmar que os títulos foram atualizados quando nada foi adquirido e sem confundir falha com ausência de dados.

#### Scenario: Rótulo de progresso por etapa
- **WHEN** a aquisição está em andamento
- **THEN** o rótulo DEVE indicar se está adquirindo documentos ou títulos

#### Scenario: Desfecho de títulos sem novidades
- **WHEN** a etapa de títulos conclui sem adquirir nem atualizar itens
- **THEN** a barra de status NÃO DEVE afirmar que os títulos foram atualizados

#### Scenario: Falha de títulos é distinguida de ausência
- **WHEN** a etapa de títulos conclui com uma ou mais falhas
- **THEN** a barra de status DEVE sinalizar a falha, sem apresentá-la como ausência de títulos

#### Scenario: Bloqueio e thread da interface
- **WHEN** a aquisição de títulos está em andamento
- **THEN** os botões da aplicação DEVEM permanecer bloqueados e a thread da interface responsiva, como na aquisição de documentos
