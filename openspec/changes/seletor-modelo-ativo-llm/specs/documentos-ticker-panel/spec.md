## RENAMED Requirements

- FROM: `### Requirement: Botão "I.A." na barra de documentos`
- TO: `### Requirement: Seletor de modelo ativo e botão de configuração na barra de documentos`

## MODIFIED Requirements

### Requirement: Seletor de modelo ativo e botão de configuração na barra de documentos

A sub-aba "Documentos" DEVE exibir, na barra de controles e imediatamente após o botão "Abrir documento", um combobox com os provedores ativos e a opção `None` e, logo após, um botão de configuração com o ícone `ai-properties.png`. O botão "I.A." textual NÃO DEVE mais existir. O combobox e o botão DEVEM estar disponíveis independentemente de haver documentos em cache ou ticker selecionado, pois a configuração de LLM é global. Trocar o item do combobox DEVE persistir imediatamente o novo provedor ativo e reavaliar o estado dos resumos; acionar o botão DEVE abrir o diálogo de configuração de LLM. Durante processamentos, o combobox e o botão DEVEM ser desabilitados e restaurados ao estado anterior, junto com os demais controles do painel.

#### Scenario: Botão disponível na barra

- **WHEN** o usuário navega para a sub-aba "Documentos"
- **THEN** o combobox de modelo ativo DEVE ser exibido imediatamente após o botão "Abrir documento" e o botão de configuração com ícone logo após o combobox

#### Scenario: Acionamento abre o diálogo de configuração

- **WHEN** o usuário clica no botão de configuração com ícone
- **THEN** o diálogo de configuração de LLM DEVE ser aberto

#### Scenario: Botão disponível sem documentos

- **WHEN** o ticker não tem documentos em cache ou nenhum ticker está selecionado
- **THEN** o combobox e o botão de configuração DEVEM permanecer habilitados

#### Scenario: Botão desabilitado durante cargas de dados

- **WHEN** uma carga de dados ou um resumo em lote está em andamento
- **THEN** o combobox e o botão de configuração DEVEM ser desabilitados junto com os demais controles do painel e restaurados ao término

#### Scenario: Troca de modelo pelo combobox

- **WHEN** o usuário seleciona um provedor ativo no combobox
- **THEN** o provedor ativo DEVE ser persistido e o estado do botão "Resumir pendentes" DEVE ser reavaliado

### Requirement: Mensagem de indisponibilidade de resumo

Quando um resumo não estiver preenchido, o sistema DEVE exibir `Resumo indisponível.` seguido de ` Clique no documento para análise.` se a LLM estiver configurada, ou seguido de ` Configure a LLM pelo botão de configuração e teste a comunicação.` caso contrário. A LLM DEVE ser considerada configurada quando o provedor for diferente de `none` e as dependências `[llm]` estiverem presentes.

#### Scenario: LLM configurada

- **WHEN** o resumo está ausente e a LLM está configurada
- **THEN** a mensagem DEVE orientar clicar no documento para análise

#### Scenario: LLM não configurada

- **WHEN** o resumo está ausente e a LLM não está configurada
- **THEN** a mensagem DEVE ser `Resumo indisponível. Configure a LLM pelo botão de configuração e teste a comunicação.`

### Requirement: Botão "Resumir pendentes" na barra de documentos

A sub-aba "Documentos" DEVE exibir um botão "Resumir pendentes" na barra de controles, imediatamente após o seletor de modelo ativo e o botão de configuração, sempre visível. O botão DEVE estar habilitado somente quando a LLM estiver configurada, existir ao menos um documento do ticker apresentado sem `long_summary` e nenhum resumo em lote estiver em andamento; caso contrário DEVE estar desabilitado. A LLM DEVE ser considerada configurada quando o provedor for diferente de `none` e as dependências `[llm]` estiverem presentes. Ao salvar a configuração ou trocar o provedor pelo combobox, o estado do botão DEVE ser reavaliado. Durante o lote e durante as cargas de dados, o botão DEVE ser desabilitado e restaurado ao término, junto com os demais controles do painel.

#### Scenario: Botão disponível na barra

- **WHEN** o usuário navega para a sub-aba "Documentos"
- **THEN** o botão "Resumir pendentes" DEVE ser exibido imediatamente após o seletor de modelo ativo e o botão de configuração

#### Scenario: Habilitado com pendentes e LLM configurada

- **WHEN** a LLM está configurada e o ticker apresentado tem ao menos um documento sem `long_summary`
- **THEN** o botão "Resumir pendentes" DEVE estar habilitado

#### Scenario: Desabilitado sem LLM configurada

- **WHEN** a LLM não está configurada
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado, sem ser ocultado

#### Scenario: Desabilitado sem pendentes

- **WHEN** todos os documentos do ticker apresentado já têm `long_summary`
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado

#### Scenario: Reavaliação quando o catálogo muda

- **WHEN** o último documento pendente passa a ter `long_summary` por um resumo individual (sem troca de aba)
- **THEN** o botão "Resumir pendentes" DEVE ser reavaliado e ficar desabilitado

#### Scenario: Reavaliação após salvar a configuração

- **WHEN** o usuário salva uma configuração de LLM válida no diálogo de configuração e há documentos pendentes
- **THEN** o botão "Resumir pendentes" DEVE passar a estar habilitado

#### Scenario: Reavaliação após trocar o modelo

- **WHEN** o usuário troca o provedor ativo pelo combobox e há documentos pendentes
- **THEN** o botão "Resumir pendentes" DEVE ser reavaliado conforme a disponibilidade da LLM

#### Scenario: Desabilitado durante o lote e cargas de dados

- **WHEN** um resumo em lote ou uma carga de dados está em andamento
- **THEN** o botão "Resumir pendentes" DEVE ser desabilitado junto com os demais controles do painel e restaurado ao término
