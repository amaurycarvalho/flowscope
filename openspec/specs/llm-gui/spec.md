# llm-gui Specification

## Purpose

Oferece a interface gráfica para configurar o provedor de LLM — presets, credenciais e limite de RPM — e para validar a comunicação com o provedor antes de usar os recursos de IA.

## Requirements

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

O diálogo DEVE oferecer um botão "Testar" que monta um provedor com os valores atualmente preenchidos (mesmo antes de salvar), envia o texto `hello` pela porta `LLMPort` e exibe o desfecho: sucesso quando houver resposta, ou um motivo de falha amigável, adequado à categoria do erro, quando a chamada falhar. O teste NÃO DEVE salvar a configuração.

#### Scenario: Teste bem-sucedido
- **WHEN** o usuário clica em "Testar" com um provedor válido e uma chave correta
- **THEN** o diálogo DEVE exibir sucesso após receber a resposta do LLM

#### Scenario: Teste com provedor indisponível
- **WHEN** o provedor é `none` ou as dependências `[llm]` estão ausentes
- **THEN** o diálogo DEVE exibir o motivo de indisponibilidade

#### Scenario: Teste com falha de comunicação
- **WHEN** a chamada falha por timeout ou erro de rede
- **THEN** o diálogo DEVE exibir uma mensagem amigável indicando falha de conexão

#### Scenario: Teste com sobrecarga do provedor
- **WHEN** a chamada falha por indisponibilidade temporária (ex.: HTTP 503)
- **THEN** o diálogo DEVE exibir uma mensagem amigável orientando tentar novamente em instantes

#### Scenario: Teste com erro do provedor
- **WHEN** a chamada falha por autenticação, requisição inválida ou cota excedida
- **THEN** o diálogo DEVE exibir uma mensagem amigável correspondente, sem expor detalhes internos do provedor

#### Scenario: Teste com configuração incompleta
- **WHEN** o provedor `custom` é selecionado sem modelo ou sem API URL
- **THEN** o diálogo DEVE exibir o motivo de configuração inválida

### Requirement: Registro em log das falhas do teste

Além de exibir o motivo na tela, o diálogo DEVE registrar em log as falhas obtidas ao acionar o botão "Testar", para análise posterior. O registro DEVE ocorrer no logger da aplicação (`flowscope`, gravado em `~/.flowscope/logs/flowscope.log`) e DEVE conter o provedor, o modelo, a API URL e o tipo e a mensagem do erro. A chave de API NÃO DEVE ser registrada. O registro DEVE ocorrer na thread da interface, ao consumir o desfecho do teste.

#### Scenario: Falha registrada no log
- **WHEN** o teste de conexão falha por indisponibilidade, comunicação, provedor ou configuração
- **THEN** uma entrada de log de nível aviso DEVE ser gravada com o provedor, o modelo, a API URL e o erro

#### Scenario: Chave de API não é registrada
- **WHEN** o teste falha com uma chave de API preenchida
- **THEN** a chave NÃO DEVE aparecer na entrada de log

### Requirement: Bloqueio durante o teste

Enquanto o teste estiver em andamento, o diálogo DEVE impedir testes concorrentes, mantendo a janela responsiva.

#### Scenario: Teste concorrente bloqueado
- **WHEN** o usuário clica em "Testar" enquanto um teste anterior ainda está em andamento
- **THEN** um novo teste NÃO DEVE ser iniciado

### Requirement: Restauração da configuração por provedor ao trocar no diálogo

Ao trocar o provedor selecionado, o diálogo DEVE exibir a configuração salva daquele provedor quando ela existir; caso contrário, DEVE exibir o `model` e a `api_url` do preset com a `api_key` vazia. O diálogo NÃO DEVE transportar a `api_key` de um provedor para outro. Selecionar `none` DEVE limpar os campos. As edições ainda não salvas DEVEM ser mantidas em memória durante a sessão do diálogo e reaplicadas ao voltar ao provedor, sem serem gravadas no disco antes do clique em "Salvar".

#### Scenario: Troca de provedor restaura o que foi salvo
- **WHEN** os provedores `deepseek` e `openai` têm configurações salvas e o usuário troca a seleção de `openai` para `deepseek`
- **THEN** o diálogo DEVE preencher `api_url`, `model`, `api_key` e `rpm` com os valores salvos de `deepseek`

#### Scenario: Troca para provedor não configurado limpa a chave
- **WHEN** o usuário troca para um provedor sem configuração salva
- **THEN** o `model` e a `api_url` DEVEM ser os defaults do preset e o campo de chave DEVE ficar vazio

#### Scenario: Seleção de none limpa os campos
- **WHEN** o usuário seleciona `none`
- **THEN** os campos de API URL, modelo e chave DEVEM ser limpos

#### Scenario: Edições não salvas sobrevivem à troca na sessão
- **WHEN** o usuário edita a chave de um provedor sem salvar, troca para outro provedor e volta ao anterior
- **THEN** a edição NÃO salva DEVE reaparecer no campo, sem ter sido gravada no disco

#### Scenario: Gravação apenas ao salvar
- **WHEN** o usuário troca de provedor sem clicar em "Salvar" e fecha o diálogo
- **THEN** o `config.json` NÃO DEVE ser alterado
