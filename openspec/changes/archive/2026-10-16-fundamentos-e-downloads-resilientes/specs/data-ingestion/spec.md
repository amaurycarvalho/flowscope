## ADDED Requirements

### Requirement: Dia não útil não é requisitado

A janela de datas de amostragem DEVE conter apenas dias úteis da B3 (excluindo fins de semana e feriados nacionais). O sistema NÃO DEVE requisitar o arquivo de negociação de um dia não útil e, caso uma resposta de ausência seja retornada para um dia não útil, ela DEVE ser tratada como ausência de pregão, sem registro de erro.

#### Scenario: Feriado excluído da janela
- **WHEN** a data de referência atravessa um feriado nacional
- **THEN** o feriado NÃO DEVE constar da janela de datas amostradas

#### Scenario: Ausência em dia não útil não é erro
- **WHEN** um arquivo de negociação é solicitado para um dia não útil e o serviço sinaliza ausência
- **THEN** o sistema DEVE tratar como ausência de pregão, sem warning de erro de download
