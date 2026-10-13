## MODIFIED Requirements

### Requirement: Marcador de ausência de texto

Quando a conversão de um documento concluir que não há texto extraível (ausência
definitiva), o sistema DEVE registrar no cache o marcador `Sem texto extraível
para pré-visualização.` no lugar do texto. Quando a conversão produzir apenas
texto parcial, falhar por erro de leitura ou o documento estiver protegido por
senha, o sistema NÃO DEVE registrar o marcador nem o texto, de modo que o
documento permaneça pendente de conversão e seja tentado novamente. O marcador
DEVE ser tratado como ausência de texto por todos os consumidores do cache,
distinguindo-se de um documento ainda não convertido. Como exceção, quando o
usuário finalizar explicitamente um resultado não conclusivo como definitivo
(capability `finalizacao-extracao-definitiva`), o sistema DEVE persistir o texto
parcial — ou, na ausência de texto, apenas a nota de extração — acrescido da nota
que descreve a limitação, mesmo nos estados `PARCIAL`, `FALHA` ou `PROTEGIDO`;
nesse caso o item deixa de ser retentado.

#### Scenario: Documento sem texto extraível
- **WHEN** a conversão de um documento conclui que não há texto extraível
- **THEN** o cache DEVE registrar o marcador `Sem texto extraível para pré-visualização.`

#### Scenario: Texto parcial não é persistido
- **WHEN** a conversão de um documento produz texto parcial (uma ou mais páginas não extraídas), sem finalização explícita
- **THEN** o cache NÃO DEVE registrar o texto nem o marcador, e o documento DEVE permanecer pendente de conversão

#### Scenario: Falha de conversão não é persistida
- **WHEN** a conversão de um documento falha por erro de leitura, sem finalização explícita
- **THEN** o cache NÃO DEVE registrar o marcador nem texto, e o documento DEVE permanecer pendente de conversão

#### Scenario: Documento protegido não é persistido
- **WHEN** a conversão de um documento é impedida por proteção de senha, sem finalização explícita
- **THEN** o cache NÃO DEVE registrar o marcador nem texto, e o documento DEVE permanecer pendente de conversão

#### Scenario: Marcador distinto de não convertido
- **WHEN** a entrada de cache de um documento contém o marcador de ausência
- **THEN** os consumidores DEVEM tratá-la como ausência de texto, e não como documento pendente de conversão

#### Scenario: Finalização explícita de parcial persiste texto e nota
- **WHEN** o usuário finaliza explicitamente um documento `PARCIAL` como definitivo
- **THEN** o cache DEVE registrar o texto parcial acrescido da nota de extração parcial

#### Scenario: Finalização explícita de falha ou protegido persiste a nota
- **WHEN** o usuário finaliza explicitamente um documento `FALHA` ou `PROTEGIDO` como definitivo
- **THEN** o cache DEVE registrar apenas a nota de extração correspondente

### Requirement: Nova tentativa de conversão após resultado não definitivo

Um documento cuja conversão terminou de forma parcial, falhou ou cujo PDF está
protegido NÃO DEVE ser tratado como já processado: uma nova conversão DEVE ser
tentada em um novo contexto de processamento (nova seleção, novo lote ou nova
execução), sem exigir limpeza manual do cache. Exceto quando o documento tiver
sido finalizado explicitamente como definitivo (capability
`finalizacao-extracao-definitiva`): nesse caso o texto definitivo persistido DEVE
ser reutilizado e nenhuma nova conversão DEVE ser tentada.

#### Scenario: Falha permite nova tentativa
- **WHEN** a conversão de um documento falhou e o documento é processado novamente depois
- **THEN** o sistema DEVE tentar converter o arquivo outra vez

#### Scenario: Parcial permite nova tentativa
- **WHEN** a conversão de um documento produziu texto parcial e o documento é processado novamente
- **THEN** o sistema DEVE tentar converter o arquivo outra vez, podendo obter o texto completo

#### Scenario: Protegido permite nova tentativa com senha
- **WHEN** um documento protegido é processado novamente e uma senha válida é informada
- **THEN** o sistema DEVE extrair e persistir o texto

#### Scenario: Documento finalizado não é retentado
- **WHEN** um documento foi finalizado explicitamente como definitivo e é processado novamente
- **THEN** o texto persistido DEVE ser reutilizado, sem nova conversão
