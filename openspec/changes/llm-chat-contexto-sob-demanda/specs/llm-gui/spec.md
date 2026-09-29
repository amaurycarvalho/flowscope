## MODIFIED Requirements

### Requirement: Diálogo de configuração de LLM

O sistema DEVE oferecer um diálogo de configuração de LLM com: seletor de provedor com os presets, campo de API URL, campo de modelo, campo de chave de API mascarado, campo de RPM e uma caixa de seleção "janela de entrada limitada" (`input_limitado`). O diálogo DEVE ser acionado pelo botão "I.A." da sub-aba "Documentos", DEVE ser modal e NÃO DEVE permitir a alteração do tamanho da janela. Ao abrir, o diálogo DEVE carregar a configuração salva; ao salvar, DEVE persistir o bloco `llm.chat`, incluindo o estado da caixa de seleção.

#### Scenario: Abertura carrega a configuração salva
- **WHEN** o diálogo é aberto e existe configuração salva
- **THEN** o provedor, a API URL, o modelo, o RPM e o estado de `input_limitado` salvos DEVEM ser exibidos

#### Scenario: Diálogo modal e não redimensionável
- **WHEN** o diálogo de configuração é aberto
- **THEN** ele DEVE capturar a interação da janela principal (modal) e NÃO DEVE permitir a alteração do tamanho da janela

#### Scenario: Salvar persiste a configuração
- **WHEN** o usuário seleciona um preset, informa a chave de API, marca ou desmarca a caixa de seleção e clica em "Salvar"
- **THEN** a configuração DEVE ser gravada em `llm.chat` no `config.json`, incluindo o estado de `input_limitado`

#### Scenario: Chave de API mascarada
- **WHEN** o diálogo exibe uma chave de API configurada
- **THEN** o valor NÃO DEVE ser exibido em texto claro

### Requirement: Restauração da configuração por provedor ao trocar no diálogo

Ao trocar o provedor selecionado, o diálogo DEVE exibir a configuração salva daquele provedor quando ela existir; caso contrário, DEVE exibir o `model` e a `api_url` do preset com a `api_key` vazia e a caixa de seleção de janela de entrada limitada desmarcada. O diálogo NÃO DEVE transportar a `api_key` de um provedor para outro. Selecionar `none` DEVE limpar os campos. As edições ainda não salvas DEVEM ser mantidas em memória durante a sessão do diálogo e reaplicadas ao voltar ao provedor, sem serem gravadas no disco antes do clique em "Salvar".

#### Scenario: Troca de provedor restaura o que foi salvo
- **WHEN** os provedores `deepseek` e `openai` têm configurações salvas e o usuário troca a seleção de `openai` para `deepseek`
- **THEN** o diálogo DEVE preencher `api_url`, `model`, `api_key`, `rpm` e `input_limitado` com os valores salvos de `deepseek`

#### Scenario: Troca para provedor não configurado limpa a chave
- **WHEN** o usuário troca para um provedor sem configuração salva
- **THEN** o `model` e a `api_url` DEVEM ser os defaults do preset, o campo de chave DEVE ficar vazio e a caixa de seleção DEVE ficar desmarcada

#### Scenario: Seleção de none limpa os campos
- **WHEN** o usuário seleciona `none`
- **THEN** os campos de API URL, modelo, chave e a caixa de seleção DEVEM ser limpos

#### Scenario: Edições não salvas sobrevivem à troca na sessão
- **WHEN** o usuário edita a chave de um provedor sem salvar, troca para outro provedor e volta ao anterior
- **THEN** a edição NÃO salva DEVE reaparecer no campo, sem ter sido gravada no disco

#### Scenario: Gravação apenas ao salvar
- **WHEN** o usuário troca de provedor sem clicar em "Salvar" e fecha o diálogo
- **THEN** o `config.json` NÃO DEVE ser alterado
