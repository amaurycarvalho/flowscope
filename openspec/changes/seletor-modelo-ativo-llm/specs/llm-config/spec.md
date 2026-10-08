## MODIFIED Requirements

### Requirement: Persistência do bloco `llm.chat` sem `input_limitado`

O sistema DEVE persistir a configuração de completion no bloco `llm.chat` de `~/.flowscope/config.json`, contendo `provider` (a seleção ativa), um mapa `providers` com uma entrada por provedor já configurado, cada uma com `api_url`, `model`, `api_key` e `rpm`, e uma lista `active` com os provedores cujo teste de conexão foi bem-sucedido e corresponde à configuração salva. O campo `input_limitado` NÃO DEVE mais existir. A leitura DEVE ignorar silenciosamente o campo antigo `input_limitado`, sem falhar, e DEVE preencher os campos ausentes com os valores padrão. A gravação DEVE preservar as demais chaves do arquivo (preferências da GUI e outros sub-blocos de `llm`, como `embedding` e `guidance`). A lista `active` DEVE ser preservada ao gravar, inclusive quando a seleção ativa é `none`.

#### Scenario: Config completa

- **WHEN** `config.json` contém `{"llm": {"chat": {"provider": "deepseek", "active": ["deepseek"], "providers": {"deepseek": {"api_url": "https://api.deepseek.com/v1", "model": "deepseek-chat", "api_key": "sk-...", "rpm": 5}}}}}`
- **THEN** a leitura DEVE retornar o provedor ativo `deepseek` com a API URL, o modelo, a chave e o RPM da entrada `providers.deepseek`, e a lista `active` com `deepseek`

#### Scenario: Config ausente

- **WHEN** `config.json` não contém o bloco `llm.chat`
- **THEN** a leitura DEVE retornar os valores padrão, com `provider` igual a `none`, `providers` vazio e `active` vazio

#### Scenario: Chave antiga ignorada

- **WHEN** uma entrada de provedor ainda contém `input_limitado`
- **THEN** a leitura DEVE ignorá-lo silenciosamente e a próxima gravação NÃO DEVE persistí-lo

#### Scenario: Gravação preserva outras chaves

- **WHEN** o `config.json` contém preferências da GUI, o bloco `llm.embedding` e o bloco `llm.guidance`, e a configuração de `llm.chat` é salva
- **THEN** as preferências da GUI, o bloco `llm.embedding` e o bloco `llm.guidance` DEVEM permanecer intactos

#### Scenario: `active` preservada ao desativar

- **WHEN** `active` contém `["deepseek", "gemini"]` e a seleção ativa passa para `none`
- **THEN** o arquivo gravado DEVE manter `active = ["deepseek", "gemini"]` e `providers` inalterado

## ADDED Requirements

### Requirement: Provedores ativos

O sistema DEVE manter, em `llm.chat.active`, a lista de provedores cuja conexão foi testada com sucesso com os valores efetivamente salvos. Um provedor é considerado ativo quando o teste de conexão executado com a mesma `api_url`, `model` e `api_key` que foram salvos obtém sucesso; o `rpm` NÃO DEVE integrar essa identidade de conexão. Uma vez ativo, o provedor DEVE permanecer ativo mesmo que a sua credencial salva seja editada depois sem novo teste. A lista NÃO DEVE conter o provedor `none`.

#### Scenario: Teste bem-sucedido promove

- **WHEN** um provedor é salvo com valores que foram testados com sucesso na mesma sessão do diálogo
- **THEN** o provedor DEVE ser incluído em `active`

#### Scenario: Teste de valores não salvos não promove

- **WHEN** um provedor é testado com valores A e salvo com valores B diferentes
- **THEN** o provedor NÃO DEVE ser incluído em `active` por esse teste

#### Scenario: Edição posterior não rebaixa

- **WHEN** um provedor já está em `active` e a sua credencial é editada e salva sem novo teste
- **THEN** o provedor DEVE permanecer em `active`

#### Scenario: Sem teste, lista vazia

- **WHEN** nenhum provedor foi testado com sucesso
- **THEN** `active` DEVE ser vazia

### Requirement: Ativação condicional no salvamento

Ao salvar a configuração do diálogo, o sistema DEVE gravar a entrada do provedor em `providers` e DEVE alterar a seleção ativa apenas quando houver, na sessão do diálogo, um teste bem-sucedido correspondente aos valores salvos. Sem esse teste correspondente, a seleção ativa (`provider`) DEVE permanecer inalterada, ainda que o provedor escolhido no diálogo seja outro.

#### Scenario: Salvar após teste ativa e seleciona

- **WHEN** o usuário seleciona um provedor, o testa com sucesso e salva
- **THEN** a entrada DEVE ser gravada, o provedor DEVE ser incluído em `active` e `provider` DEVE apontar para ele

#### Scenario: Salvar sem teste mantém a seleção anterior

- **WHEN** existe um provedor ativo anteriormente e o usuário seleciona outro provedor no diálogo e salva sem testar
- **THEN** a entrada do novo provedor DEVE ser gravada em `providers` e `provider` DEVE permanecer no provedor anterior

#### Scenario: Testar e salvar valores divergentes não ativa

- **WHEN** o usuário testa um provedor com valores A, altera para valores B e salva
- **THEN** `provider` NÃO DEVE mudar para esse provedor e ele NÃO DEVE entrar em `active`

### Requirement: Semeadura do provedor corrente na leitura

Na leitura da configuração, quando `provider` for diferente de `none` e não constar em `active`, o sistema DEVE tratar o provedor corrente como membro efetivo da seleção de ativos, de modo que a interface reflita o provedor em uso, sem afirmar que ele foi testado. As demais entradas de `providers` NÃO DEVEM ser promovidas a ativas por essa regra.

#### Scenario: Provedor corrente já em uso

- **WHEN** `config.json` contém `provider: "gemini"` com entrada em `providers` e `active` ausente ou vazio
- **THEN** o provedor `gemini` DEVE constar como seleção efetiva da lista de ativos, sem alterar os demais provedores

#### Scenario: Config já com active preenchida

- **WHEN** `active` já contém provedores testados e `provider` pertence a ela
- **THEN** a lista efetiva DEVE ser exatamente `active`
