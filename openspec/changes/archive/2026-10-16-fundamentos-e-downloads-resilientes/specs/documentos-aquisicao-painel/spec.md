## MODIFIED Requirements

### Requirement: Mensagem de conclusão honesta da aquisição

Ao concluir a aquisição acionada pelo botão "Atualizar", o sistema DEVE informar o desfecho de forma honesta e distinguindo **falha** de **ausência de novidades**: quando ao menos um documento for adquirido, a barra de status DEVE indicar a atualização; quando nenhum documento for adquirido, o sistema NÃO DEVE afirmar que os documentos foram atualizados, exibindo uma mensagem neutra (por exemplo, ausência de documentos novos); quando um ou mais documentos falharem em ser adquiridos, o sistema DEVE sinalizar a existência de falhas (por exemplo, contagem de documentos não baixados), sem confundi-las com ausência. A tolerância a falhas de aquisição permanece: nenhum desses casos DEVE ser tratado como erro fatal.

#### Scenario: Documentos adquiridos informam atualização

- **WHEN** a aquisição conclui com ao menos um documento adquirido
- **THEN** a barra de status DEVE indicar que os documentos foram atualizados

#### Scenario: Nada adquirido não afirma atualização

- **WHEN** a aquisição conclui sem adquirir nenhum documento, por ausência de documentos no período
- **THEN** a barra de status NÃO DEVE afirmar "Documentos atualizados!", exibindo mensagem neutra de ausência de novidades

#### Scenario: Falha de download é distinguida de ausência

- **WHEN** a aquisição conclui com um ou mais documentos que não puderam ser baixados
- **THEN** a barra de status DEVE sinalizar a falha (por exemplo, contagem de documentos não baixados), sem apresentá-la como ausência de novidades nem como "Documentos atualizados!"

#### Scenario: Falha tolerada não é erro fatal

- **WHEN** a aquisição falha de forma tolerada
- **THEN** a sub-aba DEVE permanecer utilizável e o desfecho NÃO DEVE ser apresentado como erro fatal
