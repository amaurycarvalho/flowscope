## Purpose

Oferece a interface gráfica para configurar o provedor de LLM — presets, credenciais e limite de RPM — e para validar a comunicação com o provedor antes de usar os recursos de IA.

## ADDED Requirements

### Requirement: Diálogo de configuração de LLM

O sistema DEVE oferecer um diálogo de configuração de LLM com: seletor de provedor com os presets, campo de API URL, campo de modelo, campo de chave de API mascarado e campo de RPM. O diálogo DEVE ser acionado pelo botão "I.A." da sub-aba "Documentos", DEVE ser modal e NÃO DEVE permitir a alteração do tamanho da janela. Ao abrir, o diálogo DEVE carregar a configuração salva; ao salvar, DEVE persistir o bloco `llm.chat`.

#### Scenario: Abertura carrega a configuração salva
- **WHEN** o diálogo é aberto e existe configuração salva
- **THEN** o provedor, a API URL, o modelo e o RPM salvos DEVEM ser exibidos

#### Scenario: Diálogo modal e não redimensionável
- **WHEN** o diálogo de configuração é aberto
- **THEN** ele DEVE capturar a interação da janela principal (modal) e NÃO DEVE permitir a alteração do tamanho da janela

#### Scenario: Salvar persiste a configuração
- **WHEN** o usuário seleciona um preset, informa a chave de API e clica em "Salvar"
- **THEN** a configuração DEVE ser gravada em `llm.chat` no `config.json`

#### Scenario: Chave de API mascarada
- **WHEN** o diálogo exibe uma chave de API configurada
- **THEN** o valor NÃO DEVE ser exibido em texto claro

### Requirement: Botão "Testar" da conexão LLM

O diálogo DEVE oferecer um botão "Testar" que monta um provedor com os valores atualmente preenchidos (mesmo antes de salvar), envia o texto `hello` pela porta `LLMPort` e exibe o desfecho: sucesso quando houver resposta, ou o motivo da falha quando a chamada falhar. O teste NÃO DEVE salvar a configuração.

#### Scenario: Teste bem-sucedido
- **WHEN** o usuário clica em "Testar" com um provedor válido e uma chave correta
- **THEN** o diálogo DEVE exibir sucesso após receber a resposta do LLM

#### Scenario: Teste com provedor indisponível
- **WHEN** o provedor é `none` ou as dependências `[llm]` estão ausentes
- **THEN** o diálogo DEVE exibir o motivo de indisponibilidade

#### Scenario: Teste com falha de comunicação
- **WHEN** a chamada falha por timeout ou erro de rede
- **THEN** o diálogo DEVE exibir o motivo da falha de comunicação

#### Scenario: Teste com erro do provedor
- **WHEN** a chamada falha por autenticação, requisição inválida ou cota excedida
- **THEN** o diálogo DEVE exibir o motivo retornado pelo provedor

#### Scenario: Teste com configuração incompleta
- **WHEN** o provedor `custom` é selecionado sem modelo ou sem API URL
- **THEN** o diálogo DEVE exibir o motivo de configuração inválida

### Requirement: Bloqueio durante o teste

Enquanto o teste estiver em andamento, o diálogo DEVE impedir testes concorrentes, mantendo a janela responsiva.

#### Scenario: Teste concorrente bloqueado
- **WHEN** o usuário clica em "Testar" enquanto um teste anterior ainda está em andamento
- **THEN** um novo teste NÃO DEVE ser iniciado
