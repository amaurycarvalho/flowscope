# Spec Delta

## MODIFIED Requirements

### Requirement: Ajuste para próximo dia útil

Cada data calculada DEVE ser ajustada individualmente para o próximo dia útil (aproximação local, sem cascata). Dias úteis são segunda a sexta, excluindo os feriados nacionais obtidos do calendário dinâmico da capability `calendario-feriados`. Quando o calendário do ano não estiver disponível, o ajuste DEVE considerar apenas sábado e domingo como não úteis, sem bloquear a carga.

#### Scenario: Data calculada cai em sábado
- **WHEN** a data calculada é um sábado
- **THEN** o sistema DEVE avançar para o próximo domingo, depois segunda (se aplicável), até encontrar um dia útil

#### Scenario: Data calculada cai em feriado
- **WHEN** a data calculada é 25 de dezembro (Natal)
- **THEN** o sistema DEVE avançar para 26 de dezembro (se for dia útil) ou próximo dia útil seguinte

#### Scenario: Feriado vem do calendário dinâmico
- **WHEN** o calendário do ano está no cache ou foi obtido da ANBIMA
- **THEN** o ajuste usa os feriados desse calendário
- **THEN** não usa a lista estática antiga

#### Scenario: Calendário indisponível
- **WHEN** não há cache do ano e a ANBIMA falha
- **THEN** o ajuste considera apenas sábado e domingo como não úteis
- **THEN** a geração de datas continua sem erro fatal
