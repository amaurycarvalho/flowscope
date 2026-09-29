## RENAMED Requirements

- FROM: `### Requirement: Orquestração da cascata em até duas chamadas`
- TO: `### Requirement: Orquestração da cascata em até três chamadas`

## MODIFIED Requirements

### Requirement: Orquestração da cascata em até três chamadas

O sistema DEVE resolver cada pergunta em no máximo duas chamadas de completion por padrão: a primeira com os resumos curtos e longos do escopo; a segunda, quando necessária, com o texto integral dos documentos-alvo. Quando o parâmetro `input_limitado` estiver ativo, o sistema DEVE admitir até três chamadas: a primeira com o manifesto de recursos no lugar dos resumos; a segunda com os recursos iniciais solicitados pela LLM (conhecimento, fundamentos e/ou resumos); e a terceira, quando necessária, com o texto integral dos documentos-alvo. Quando uma chamada já responder de forma conclusiva, as chamadas seguintes NÃO DEVEM ocorrer. Todas as chamadas DEVEM compartilhar o mesmo prefixo estável e o mesmo histórico, diferindo apenas no sufixo.

#### Scenario: Resposta nos resumos
- **WHEN** a primeira chamada devolve uma resposta suficiente
- **THEN** apenas uma chamada de completion DEVE ter sido feita

#### Scenario: Necessidade do texto integral
- **WHEN** a primeira chamada devolve documentos-alvo sem resposta conclusiva
- **THEN** uma segunda chamada DEVE ler o texto integral desses alvos

#### Scenario: Recursos iniciais sob demanda com janela limitada
- **WHEN** `input_limitado` está ativo e a primeira chamada devolve recursos iniciais solicitados
- **THEN** uma segunda chamada DEVE carregar esses recursos, e uma terceira chamada DEVE ler o texto integral dos documentos-alvo quando solicitados

#### Scenario: Resposta conclusiva encerra a cascata
- **WHEN** uma chamada intermediária já responde de forma conclusiva
- **THEN** nenhuma chamada adicional DEVE ocorrer
