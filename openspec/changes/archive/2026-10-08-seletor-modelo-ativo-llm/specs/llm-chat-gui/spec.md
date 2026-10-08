## MODIFIED Requirements

### Requirement: Estado não configurado e botão "Configuração"

Quando `llm.chat.provider` está ausente ou é `none`, a aba "Chat AI" DEVE permanecer visível, com o campo de entrada desabilitado e exibindo orientação para configurar a LLM. O cabeçalho DEVE ter os botões "Copiar chat" e um botão de configuração com o ícone `ai-properties.png`, sempre visível logo após o combobox de modelo ativo, e abrindo o diálogo de configuração fornecido pela `llm-core`. Ao salvar a configuração, o estado DEVE ser reavaliado.

#### Scenario: Provedor não configurado

- **WHEN** `llm.chat.provider` está ausente ou é `none`
- **THEN** a aba DEVE exibir a orientação de configuração com a entrada desabilitada e o botão de configuração disponível

#### Scenario: Configuração salva

- **WHEN** o usuário salva uma configuração válida no diálogo
- **THEN** o campo de entrada DEVE ser habilitado

#### Scenario: Configuração sempre acessível

- **WHEN** a aba "Chat AI" está exibida
- **THEN** o botão de configuração com ícone DEVE estar visível no cabeçalho, logo após o combobox de modelo ativo

### Requirement: Bloqueio do cabeçalho durante o envio

Enquanto houver um envio em processamento, os botões "Limpar", "Copiar chat", o combobox de modelo ativo e o botão de configuração DEVEM ficar desabilitados, além do "Enviar". Ao término do processamento (resposta, erro ou cancelamento), esses controles DEVEM ser reavaliados e voltar ao normal conforme o estado da conversa e da seleção de modelos.

#### Scenario: Botões desabilitados durante o envio

- **WHEN** uma pergunta é enviada e o processamento está em andamento
- **THEN** "Limpar", "Copiar chat", o combobox de modelo ativo e o botão de configuração DEVEM estar desabilitados

#### Scenario: Botões restaurados ao término

- **WHEN** o processamento termina, com sucesso ou erro
- **THEN** o botão de configuração DEVE voltar a ficar habilitado e "Limpar"/"Copiar chat" conforme a existência de conteúdo

#### Scenario: Botões restaurados ao cancelar

- **WHEN** o usuário cancela o envio
- **THEN** o botão de configuração e o combobox DEVEM voltar a ficar habilitados, sem aguardar a thread de trabalho

## ADDED Requirements

### Requirement: Seletor de modelo ativo no cabeçalho

O cabeçalho da aba "Chat AI" DEVE exibir um combobox com os provedores ativos e a opção `None`, refletindo o provedor correntemente selecionado em `llm.chat.provider`. Trocar o item do combobox DEVE persistir imediatamente o novo provedor ativo; selecionar `None` DEVE desativar o provedor corrente sem remover entradas de `providers` nem da lista de ativos. O combobox DEVE incluir o provedor corrente ainda que ele não tenha sido testado, e NÃO DEVE listar provedores não testados.

#### Scenario: Combobox reflete o provedor ativo

- **WHEN** a aba "Chat AI" é exibida com `llm.chat.provider` igual a um provedor ativo
- **THEN** o combobox DEVE exibir esse provedor como selecionado

#### Scenario: Troca persiste o provedor

- **WHEN** o usuário seleciona outro provedor ativo no combobox
- **THEN** `llm.chat.provider` DEVE ser gravado com o novo provedor, preservando `providers` e a lista de ativos, e o painel DEVE reavaliar o estado da LLM

#### Scenario: Opção None desativa

- **WHEN** o usuário seleciona `None` no combobox
- **THEN** o provedor ativo DEVE passar a `none`, a entrada e as demais listas DEVEM ser preservadas, e a entrada de chat DEVE ser desabilitada

#### Scenario: Lista contém apenas ativos e o corrente

- **WHEN** o combobox é populado
- **THEN** ele DEVE conter `None`, os provedores testados com sucesso e, se distinto destes e não `none`, o provedor correntemente ativo
