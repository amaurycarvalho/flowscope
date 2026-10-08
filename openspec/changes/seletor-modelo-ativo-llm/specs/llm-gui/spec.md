## MODIFIED Requirements

### Requirement: Diálogo de configuração de LLM

O sistema DEVE oferecer um diálogo de configuração de LLM com: seletor de provedor com os presets, campo de API URL, campo de modelo, campo de chave de API mascarado e campo de RPM. O diálogo NÃO DEVE mais oferecer a caixa de seleção "janela de entrada limitada" (`input_limitado`). O diálogo DEVE ser acionado pelo botão de configuração com ícone presente no cabeçalho da aba "Chat AI" e nas barras das sub-abas "Documentos" e "Notícias", DEVE ser modal e NÃO DEVE permitir a alteração do tamanho da janela. Ao abrir, o diálogo DEVE carregar a configuração salva; ao salvar, DEVE persistir o bloco `llm.chat`.

#### Scenario: Abertura carrega a configuração salva

- **WHEN** o diálogo é aberto e existe configuração salva
- **THEN** o provedor, a API URL, o modelo e o RPM salvos DEVEM ser exibidos, sem caixa de seleção de janela de entrada limitada

#### Scenario: Diálogo modal e não redimensionável

- **WHEN** o diálogo de configuração é aberto
- **THEN** ele DEVE capturar a interação da janela principal (modal) e NÃO DEVE permitir a alteração do tamanho da janela

#### Scenario: Salvar persiste a configuração

- **WHEN** o usuário seleciona um preset, informa a chave de API e clica em "Salvar"
- **THEN** a configuração DEVE ser gravada em `llm.chat` no `config.json`, sem o campo `input_limitado`

#### Scenario: Chave de API mascarada

- **WHEN** o diálogo exibe uma chave de API configurada
- **THEN** o valor NÃO DEVE ser exibido em texto claro

#### Scenario: Acionado pelo botão de ícone

- **WHEN** o usuário aciona o botão de configuração com ícone em qualquer uma das três telas
- **THEN** o diálogo de configuração de LLM DEVE ser aberto

## ADDED Requirements

### Requirement: Ativação e seleção automática no salvamento

Ao salvar o diálogo, o sistema DEVE ativar e selecionar automaticamente o provedor quando os valores salvos corresponderem a um teste de conexão bem-sucedido realizado na mesma sessão do diálogo. Quando o salvamento ocorrer sem esse teste correspondente, o sistema NÃO DEVE alterar a seleção ativa anteriormente vigente, limitando-se a persistir a entrada do provedor escolhido.

#### Scenario: Testar com sucesso e salvar ativa

- **WHEN** o usuário seleciona um provedor, clica em "Testar" e obtém sucesso, e depois clica em "Salvar"
- **THEN** o provedor DEVE ser ativado, a seleção ativa DEVE mudar para ele e ele DEVE ficar selecionado no combobox

#### Scenario: Salvar sem teste preserva a seleção

- **WHEN** há uma seleção ativa anterior e o usuário seleciona outro provedor e salva sem que o teste correspondente tenha sido bem-sucedido
- **THEN** a seleção ativa DEVE permanecer a anterior e o novo provedor DEVE apenas ter a sua entrada gravada

#### Scenario: Testar e salvar valores divergentes

- **WHEN** o usuário testa um provedor com determinados valores, altera os valores e salva
- **THEN** o provedor NÃO DEVE ser ativado por esse teste
