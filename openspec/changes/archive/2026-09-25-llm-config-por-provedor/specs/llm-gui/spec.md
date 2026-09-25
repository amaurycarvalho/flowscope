## ADDED Requirements

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
