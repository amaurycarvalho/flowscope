## ADDED Requirements

### Requirement: Envio longo não é encerrado por inatividade

Enquanto uma chamada ao provedor ou a espera pela confirmação de leitura do texto integral estiver em andamento, o processamento do envio do chat NÃO DEVE ser encerrado por inatividade. O botão de cancelamento DEVE permanecer habilitado e o botão "Enviar" DEVE permanecer desabilitado durante toda a duração do envio, e os controles só DEVEM ser restaurados ao término real (resposta, erro ou cancelamento do usuário).

#### Scenario: Chamada longa mantém os botões

- **WHEN** uma pergunta é enviada e o provedor demora além do limite de inatividade
- **THEN** o botão de cancelamento DEVE permanecer habilitado e o botão "Enviar" desabilitado até o término real

#### Scenario: Espera de confirmação não encerra o envio

- **WHEN** o diálogo de confirmação de leitura do texto integral permanece aberto além do limite de inatividade
- **THEN** o envio NÃO DEVE ser encerrado por inatividade e os botões DEVEM permanecer no estado de processamento

#### Scenario: Término real restaura os controles

- **WHEN** o provedor conclui a resposta, falha ou o usuário cancela
- **THEN** os controles DEVEM ser reavaliados conforme o estado da conversa
