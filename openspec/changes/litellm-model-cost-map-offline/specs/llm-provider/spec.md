# Spec Delta — llm-provider

## ADDED Requirements

### Requirement: Catálogo local de model cost map sem busca externa

O sistema DEVE forçar o uso do catálogo local de model cost map do liteLLM antes da primeira importação da biblioteca, de modo que a inicialização não faça requisição ao GitHub nem emita avisos de tentativa de download.

#### Scenario: Importação usa a fonte local
- **WHEN** o liteLLM é importado pela primeira vez pelo adaptador ou pelos presets
- **THEN** a fonte do model cost map DEVE ser a local e nenhuma requisição ao catálogo remoto DEVE ser disparada

#### Scenario: Sem aviso de falha de download
- **WHEN** o ambiente não tem acesso ao GitHub
- **THEN** a inicialização NÃO DEVE emitir o aviso `model cost map fetch attempt ... failed` nem iniciar retentativas em background

#### Scenario: Janela e contagem continuam funcionando offline
- **WHEN** a rede está indisponível e o sistema resolve a janela de contexto ou conta tokens
- **THEN** o catálogo local DEVE ser usado e a operação DEVE concluir com o valor conhecido ou com o fallback do preset

#### Scenario: Override explícito do usuário é preservado
- **WHEN** o usuário define explicitamente a variável de ambiente do catálogo remoto
- **THEN** o sistema NÃO DEVE sobrescrever essa escolha e o comportamento remoto DEVE ser mantido
