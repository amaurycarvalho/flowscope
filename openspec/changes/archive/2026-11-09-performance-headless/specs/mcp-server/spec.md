# Spec Delta

## MODIFIED Requirements

### Requirement: Preparação opcional na inicialização do servidor MCP

O subcomando `flowscope mcp` DEVE aceitar os parâmetros opcionais `--watchlist <arquivo>` e `--data <AAAA-MM-DD>`. Quando `--watchlist` for informado, o sistema DEVE executar, antes de iniciar o servidor, a mesma etapa de `flowscope carregar watchlist <arquivo>`. Quando `--data` for informado, o sistema DEVE executar, antes de iniciar o servidor, a mesma etapa de `flowscope atualizar fundamentos --data <AAAA-MM-DD>` e, logo depois, a mesma etapa de `flowscope atualizar performance --data <data resolvida>`, usando a watchlist resultante. A preparação DEVE reusar os mesmos núcleos das ações, DEVE ocorrer sob o lock global de ação — liberado antes de o servidor começar a atender —, DEVE registrar progresso em `stderr` e NÃO DEVE escrever em `stdout`. Uma falha dura na preparação DEVE abortar a inicialização com código de saída diferente de zero, sem iniciar o servidor. Uma falha recuperável da Performance NÃO DEVE abortar a inicialização: o servidor DEVE iniciar com a árvore refletindo o resultado disponível ou a ausência do ramo. A árvore DEVE ser montada após a preparação, refletindo a data de referência resolvida e o snapshot de Performance mais recente.

#### Scenario: Watchlist preparada na inicialização

- **WHEN** `flowscope mcp --watchlist carteira.txt` é executado
- **THEN** a watchlist do arquivo DEVE ser persistida como em `flowscope carregar watchlist` antes de o servidor iniciar

#### Scenario: Fundamentos preparados na inicialização

- **WHEN** `flowscope mcp --data 2026-10-14` é executado
- **THEN** os fundamentos DEVEM ser atualizados como em `flowscope atualizar fundamentos --data 2026-10-14` antes de o servidor iniciar
- **AND** a árvore DEVE refletir a data de referência resolvida

#### Scenario: Performance preparada após os fundamentos

- **WHEN** `flowscope mcp --data 2026-10-14` é executado
- **THEN** a Performance DEVE ser atualizada como em `flowscope atualizar performance --data 2026-10-14` logo após os fundamentos
- **AND** a árvore DEVE expor o ramo `/performance` quando o snapshot estiver disponível

#### Scenario: Falha recuperável da Performance não aborta

- **WHEN** a atualização de Performance falha de forma recuperável (por exemplo, série do índice indisponível)
- **THEN** o servidor DEVE iniciar normalmente, registrar `WARNING` em `stderr` e montar a árvore com o resultado disponível ou sem o ramo

#### Scenario: Sem parâmetros não há preparação

- **WHEN** `flowscope mcp` é executado sem `--watchlist` e sem `--data`
- **THEN** nenhuma escrita, download ou consulta externa DEVE ocorrer na inicialização
- **AND** a árvore DEVE ler o snapshot de Performance existente, se houver

#### Scenario: Falha na preparação aborta a inicialização

- **WHEN** a preparação falha de forma dura (por exemplo, arquivo de watchlist inexistente)
- **THEN** o processo DEVE encerrar com código diferente de zero, sem iniciar o servidor

#### Scenario: Preparação não polui o `stdout`

- **WHEN** a preparação executa antes de o servidor atender
- **THEN** a saída das etapas de preparação, inclusive a Performance, DEVE ir para `stderr` e o `stdout` DEVE conter apenas mensagens JSON-RPC do servidor

## ADDED Requirements

### Requirement: Ramo `/performance` acessível pelas tools `nav_*`

Quando o snapshot de Performance estiver disponível, o servidor MCP DEVE permitir navegar o ramo `/performance` com as tools `nav_*` existentes, sem criar tools novas e sem sair do cache local. Quando o snapshot estiver ausente ou inválido, o ramo NÃO DEVE existir e a navegação DEVE continuar funcionando nos demais ramos.

#### Scenario: Listagem do ramo

- **WHEN** o cliente invoca `nav_listar` em `/performance` e existe snapshot
- **THEN** o servidor DEVE devolver os filhos do ramo, incluindo a configuração e os benchmarks disponíveis

#### Scenario: Leitura de um ticker

- **WHEN** o cliente invoca `nav_obter` em `/performance/benchmarks/IFIX/tickers/<ticker>` e o ticker está no snapshot
- **THEN** o servidor DEVE devolver os retornos, o excesso em pontos percentuais, as observações e o aviso de evento suspeito, quando houver

#### Scenario: Snapshot ausente

- **WHEN** o cliente invoca `nav_existe` em `/performance` e não há snapshot
- **THEN** o servidor DEVE devolver `false` e não deve falhar nem consultar a rede

#### Scenario: Somente leitura

- **WHEN** qualquer tool `nav_*` navega o ramo `/performance`
- **THEN** nenhuma escrita, download ou consulta externa DEVE ocorrer
