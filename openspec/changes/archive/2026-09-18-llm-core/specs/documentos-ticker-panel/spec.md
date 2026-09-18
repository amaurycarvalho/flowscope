## ADDED Requirements

### Requirement: Botão "I.A." na barra de documentos

A sub-aba "Documentos" DEVE exibir um botão "I.A." na barra de controles, imediatamente após o botão "Abrir documento". O botão DEVE estar disponível independentemente de haver documentos em cache ou ticker selecionado, pois a configuração de LLM é global, e ao ser acionado DEVE abrir o diálogo de configuração de LLM. Durante as cargas de dados, o botão "I.A." DEVE seguir a mesma regra dos demais botões do painel, sendo desabilitado e restaurado ao estado anterior.

#### Scenario: Botão disponível na barra
- **WHEN** o usuário navega para a sub-aba "Documentos"
- **THEN** o botão "I.A." DEVE ser exibido imediatamente após o botão "Abrir documento"

#### Scenario: Acionamento abre o diálogo de configuração
- **WHEN** o usuário clica no botão "I.A."
- **THEN** o diálogo de configuração de LLM DEVE ser aberto

#### Scenario: Botão disponível sem documentos
- **WHEN** o ticker não tem documentos em cache ou nenhum ticker está selecionado
- **THEN** o botão "I.A." DEVE permanecer habilitado

#### Scenario: Botão desabilitado durante cargas de dados
- **WHEN** uma carga de dados está em andamento
- **THEN** o botão "I.A." DEVE ser desabilitado junto com os demais botões do painel e restaurado ao término
