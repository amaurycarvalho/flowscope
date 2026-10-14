## ADDED Requirements

### Requirement: Prefixo de sistema estável na avaliação de guidance

Ao avaliar uma fonte pela IA, o sistema DEVE enviar as instruções de avaliação como um prefixo de sistema (`system_prompt`) constante e a mensagem de usuário DEVE conter apenas o trecho avaliado. O prefixo DEVE ser idêntico entre fontes e entre Relatórios Gerenciais, de modo que o provedor possa reaproveitar o cache de prompt.

#### Scenario: Instruções no prefixo de sistema

- **WHEN** uma fonte é avaliada pela IA
- **THEN** as instruções DEVEM ser enviadas em `system_prompt` e a mensagem `user` DEVE conter apenas o trecho

#### Scenario: Prefixo idêntico entre fontes

- **WHEN** duas fontes distintas são avaliadas pela IA
- **THEN** o `system_prompt` enviado DEVE ser idêntico nos dois casos

### Requirement: Formato e regras da resposta da avaliação pela IA

O prefixo de sistema DEVE exigir a resposta em quatro linhas, nesta ordem: `GUIDANCE: SIM ou NAO`, `VALOR_MIN: <valor por cota ou vazio>`, `VALOR_MAX: <valor por cota ou vazio>` e `PERIODO: <período ou vazio>`. O prompt DEVE ainda definir que, com `GUIDANCE: NAO`, os campos de valor e período ficam vazios; que um valor único preenche mínimo e máximo com o mesmo número; que o separador decimal é o ponto, sem símbolo de moeda; e que, na dúvida, deve-se responder `NAO`.

#### Scenario: Saída vazia quando não há guidance

- **WHEN** o trecho não contém guidance de distribuição
- **THEN** o prefixo DEVE exigir `GUIDANCE: NAO` com `VALOR_MIN`, `VALOR_MAX` e `PERIODO` vazios

#### Scenario: Valor único replica em mínimo e máximo

- **WHEN** o trecho projeta um único valor por cota
- **THEN** o prefixo DEVE exigir que `VALOR_MIN` e `VALOR_MAX` recebam o mesmo número

#### Scenario: Separador decimal sem símbolo

- **WHEN** o trecho projeta um valor por cota
- **THEN** o prefixo DEVE exigir ponto como separador decimal e vedar símbolos de moeda
