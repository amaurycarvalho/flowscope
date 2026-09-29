## ADDED Requirements

### Requirement: Teto de testes de UI verificado

O sistema DEVE manter um baseline commitado da contagem de testes de apresentação que exigem interface gráfica (gating por `DISPLAY`/`@needs_display`) e DEVE ter um teste arquitetural que compare a contagem corrente ao baseline. O teste DEVE reprovar quando a contagem aumentar e DEVE exigir a atualização do baseline quando diminuir, de modo que o teto apenas encolha.

#### Scenario: Aumento da contagem reprova

- **WHEN** um teste novo marcado com gating de display é adicionado sem reduzir outro
- **THEN** o teste arquitetural DEVE falhar, apontando o aumento em relação ao baseline

#### Scenario: Redução exige atualização do baseline

- **WHEN** um teste de UI é convertido para headless ou removido
- **THEN** o teste arquitetural DEVE exigir a atualização do baseline para o novo valor menor

#### Scenario: Teste headless não consome o orçamento

- **WHEN** um teste de processamento é escrito sem exigir `DISPLAY`
- **THEN** ele NÃO DEVE contar para o teto de testes de UI
