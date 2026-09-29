## Context

Ver `proposal.md - Why`. O `B3ShortInterestSource` (`infrastructure/b3/emprestimos.py`) lê as Posições em Aberto (`BTBLendingOpenPosition`) por data e faz recuo de até 7 dias quando a data pedida ainda não foi publicada. O cache é um metadado por data, sem TTL nem validação: `_mapa` grava o resultado da agregação mesmo quando vazio. A B3 publica a posição do pregão anterior, então o primeiro acesso do dia costuma retornar vazio — e ficava preso. O read-through do histórico da análise fundamentalista (`observacao_completa` = `nome or cotacao`) pode manter o `N/A` do dia até um refresh forçado.

## Goals / Non-Goals

**Goals:**
- Tornar o cache de ações alugadas tolerante à publicação tardia da B3.
- Recuperar automaticamente os caches vazios já gravados no ambiente do usuário.
- Preservar o comportamento dos cálculos e das colunas (`N/A`/`Inexistente`).

**Non-Goals:**
- Alterar `_JANELA_DIAS`, os cálculos de Shorts%/SIR ou as classificações.
- Adicionar TTL genérico ao `CacheManager`.
- Recalcular automaticamente as observações já persistidas no histórico de fundamentos.

## Decisions

### Decisão 1: Não persistir mapa vazio e reconsultar cache vazio

**Escolha**: `_mapa` só grava o cache quando o mapa agregado é não vazio; ao ler, um mapa vazio é tratado como *miss* e o dia é baixado novamente.

**Alternativas**: aumentar a janela de recuo; adicionar TTL ao cache.

**Razão**: o recuo de 7 dias não recupera um dia envenenado e o TTL ainda recarregaria vazios repetidamente. Ignorar o vazio resolve tanto os caches futuros quanto os existentes sem apagar dados válidos.

### Decisão 2: Bust dos caches vazios legados na inicialização

**Escolha**: `B3ShortInterestSource.__init__` chama `_bust_stale_empty_cache`, que remove os arquivos `b3_emprestimos_btb-v1_*.json` com `data` vazio.

**Alternativas**: apagar manualmente; apenas ignorar o vazio na leitura.

**Razão**: a Decisão 1 já garante a correção, mas o bust limpa o cache do usuário e evita reescrever/ler vazios; replica o padrão já existente em `B3Client._bust_stale_portfolio_cache`.

## Risks / Trade-offs

- **[Risco]** Rebaixar vazios para *miss* faz rereconsultar fins de semana e feriados a cada execução → **Trade-off** aceito; são poucas páginas e o custo é baixo frente a recuperar a data publicada.
- **[Risco]** O `N/A` já persistido na observação do dia no histórico de fundamentos não é recalculado automaticamente → **Mitigação**: documentado; resolve-se com "Atualizar fundamentos" (`force_refresh`), fora do escopo desta change.

## Migration Plan

1. Ajustar `_mapa` para não gravar vazio e ignorar cache vazio.
2. Adicionar `_bust_stale_empty_cache` e chamá-lo no construtor.
3. Cobrir com testes de infraestrutura (vazio não cacheado, cache vazio reconsultado, bust preserva dados).
4. Rollback = reverter o commit; o cache é regenerado na próxima leitura.
