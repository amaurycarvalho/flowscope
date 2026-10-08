## ADDED Requirements

### Requirement: Mensagem de conclusão honesta da aquisição de notícias

Ao concluir a aquisição de notícias acionada pelo usuário, o sistema DEVE informar o desfecho de forma honesta: quando ao menos um item for adquirido, a barra de status DEVE indicar a atualização; quando nenhum item for adquirido, o sistema NÃO DEVE afirmar que as notícias foram atualizadas, exibindo uma mensagem neutra. A tolerância a falhas de aquisição permanece: nenhum desses casos DEVE ser tratado como erro fatal.

#### Scenario: Notícias adquiridas informam atualização

- **WHEN** a aquisição conclui com ao menos um item adquirido
- **THEN** a barra de status DEVE indicar que as notícias foram atualizadas

#### Scenario: Nada adquirido não afirma atualização

- **WHEN** a aquisição conclui sem adquirir nenhum item, seja por ausência de itens ou por indisponibilidade tolerada
- **THEN** a barra de status NÃO DEVE afirmar "Notícias atualizadas!", exibindo mensagem neutra

### Requirement: Falha na leitura assíncrona sai do carregamento

Quando a leitura assíncrona do cache local da sub-aba "Notícias" falhar, o sistema DEVE abandonar o estado de carregamento e exibir uma mensagem informativa, sem permanecer carregando indefinidamente e sem erro fatal.

#### Scenario: Leitura falha não trava o carregamento

- **WHEN** a leitura assíncrona do cache local falha
- **THEN** a sub-aba DEVE sair do estado de carregamento e exibir mensagem informativa

#### Scenario: Leitura obsoleta não altera o estado

- **WHEN** uma leitura é substituída por outra mais recente e a anterior falha
- **THEN** o desfecho da leitura anterior NÃO DEVE alterar o estado apresentado
