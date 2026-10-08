## ADDED Requirements

### Requirement: Falha na pré-visualização sai do carregamento

Quando a extração de texto ou a geração do resumo da pré-visualização de um documento falhar, o sistema DEVE abandonar o estado de carregamento e exibir uma mensagem informativa na caixa de pré-visualização, sem permanecer "Carregando…" indefinidamente e sem erro fatal. O desfecho da pré-visualização de um documento que já não está mais selecionado NÃO DEVE alterar a caixa.

#### Scenario: Falha de extração ou resumo exibe mensagem

- **WHEN** o trabalho de pré-visualização falha ao extrair o texto ou ao gerar o resumo
- **THEN** a caixa de pré-visualização DEVE sair do estado de carregamento e exibir mensagem informativa

#### Scenario: Falha de documento não selecionado é descartada

- **WHEN** o trabalho de pré-visualização de um documento falha após o usuário selecionar outro documento
- **THEN** o desfecho NÃO DEVE alterar a pré-visualização do documento atualmente selecionado
