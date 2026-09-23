## MODIFIED Requirements

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
