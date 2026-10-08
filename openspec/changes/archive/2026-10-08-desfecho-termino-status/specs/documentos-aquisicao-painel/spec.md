## ADDED Requirements

### Requirement: Mensagem de conclusão honesta da aquisição

Ao concluir a aquisição acionada pelo botão "Atualizar", o sistema DEVE informar o desfecho de forma honesta: quando ao menos um documento for adquirido, a barra de status DEVE indicar a atualização; quando nenhum documento for adquirido, o sistema NÃO DEVE afirmar que os documentos foram atualizados, exibindo uma mensagem neutra (por exemplo, ausência de documentos novos). A tolerância a falhas de aquisição permanece: nenhum desses casos DEVE ser tratado como erro fatal.

#### Scenario: Documentos adquiridos informam atualização

- **WHEN** a aquisição conclui com ao menos um documento adquirido
- **THEN** a barra de status DEVE indicar que os documentos foram atualizados

#### Scenario: Nada adquirido não afirma atualização

- **WHEN** a aquisição conclui sem adquirir nenhum documento, seja por ausência de documentos ou por indisponibilidade tolerada
- **THEN** a barra de status NÃO DEVE afirmar "Documentos atualizados!", exibindo mensagem neutra

#### Scenario: Falha tolerada não é erro fatal

- **WHEN** a aquisição falha de forma tolerada
- **THEN** a sub-aba DEVE permanecer utilizável e o desfecho NÃO DEVE ser apresentado como erro fatal
