# Spec Delta

## ADDED Requirements

### Requirement: Registro de problemas da Performance headless e da navegação

O sistema DEVE registrar, no formato e na rotação do log da aplicação, os problemas recuperáveis da atualização, da leitura do snapshot e da exportação de Performance. Ciclo de vida e decisões DEVEM ser `INFO`; dados inválidos, índice indisponível, snapshot corrompido ou de schema divergente, snapshot defasado e falha de escrita DEVEM ser `WARNING` com contexto (data de referência, benchmark, ticker ou caminho). No modo MCP, os registros NÃO DEVEM ir para `stdout`.

#### Scenario: Índice indisponível

- **WHEN** a série de um índice não pode ser obtida durante `atualizar performance`
- **THEN** uma linha de `WARNING` DEVE identificar o benchmark, o intervalo e a causa

#### Scenario: Snapshot corrompido ou de schema divergente

- **WHEN** o snapshot de Performance não pode ser interpretado
- **THEN** uma linha de `WARNING` DEVE identificar o caminho e o motivo, sem impedir a navegação dos demais ramos

#### Scenario: Snapshot defasado

- **WHEN** a data de referência do snapshot é anterior à referência resolvida atual
- **THEN** o sistema DEVE registrar `WARNING` com as duas datas e expor `ref_date` e `cached_at` no ramo

#### Scenario: Falha de escrita do snapshot

- **WHEN** a gravação atômica do snapshot falha por erro de I/O
- **THEN** uma linha de `WARNING` DEVE identificar o caminho e a causa, sem derrubar o cálculo já concluído

#### Scenario: Exportação sem snapshot

- **WHEN** `flowscope exportar performance` é executado e não há snapshot
- **THEN** o erro estruturado DEVE ser registrado em log com o motivo e a dica de recuperação

#### Scenario: Falha recuperável na preparação do MCP

- **WHEN** a Performance falha de forma recuperável durante a preparação do MCP
- **THEN** o `WARNING` DEVE ir para `stderr` e o `stdout` DEVE permanecer exclusivo de JSON-RPC

#### Scenario: Ciclo de vida em INFO

- **WHEN** `atualizar performance` inicia, reutiliza cache, calcula benchmarks e conclui
- **THEN** as etapas DEVEM ser registradas em `INFO` com a data resolvida, a configuração e os benchmarks processados

### Requirement: Ausência de snapshot não gera ruído na navegação

Na montagem da árvore de conhecimento por mensagem do chat, a ausência de snapshot de Performance NÃO DEVE gerar `WARNING` repetido a cada turno. A ausência DEVE ser registrada em `DEBUG` ou uma única vez por assinatura de estado; apenas snapshot inválido ou defasado DEVE gerar `WARNING`.

#### Scenario: Chat sem snapshot

- **WHEN** o chat monta a árvore repetidamente e não há snapshot de Performance
- **THEN** nenhum `WARNING` de ausência DEVE ser emitido a cada mensagem

#### Scenario: Snapshot inválido continua visível no log

- **WHEN** o snapshot existe, mas está corrompido ou tem schema divergente
- **THEN** o problema DEVE ser registrado em `WARNING` com contexto, sem silenciar a falha

#### Scenario: Mudança de assinatura reavalia o snapshot

- **WHEN** a assinatura do estado muda e o snapshot passa a existir ou a mudar
- **THEN** a nova leitura DEVE ser registrada conforme o desfecho, sem repetir o aviso de ausência em cada turno estável
