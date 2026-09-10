## Context

As preferências ficam em `config.json` (`presentation/gui/app.py`), com salvamento em `_on_close`. O `FundamentalTablePanel` cria as colunas com `width=140` fixo. O `FundamentusFundamentalDataProvider.obter_com_resultado` colapsa o `CacheOutcome` em um booleano `atualizou`; o `FundamentalJob` publica um único `atualizou`; `FlowScopePresenter.on_fundamental_result` só exibe "Dados atualizados" quando `atualizou`. O cursor é limpo em `on_operation_finished`, que roda antes de o job fundamental terminar (`controller.py`). Ver `proposal.md - Why`.

## Goals / Non-Goals

**Goals:**
- Persistir e restaurar larguras das colunas.
- Propagar o resultado de cache por ticker até a apresentação.
- Manter o cursor de espera durante a análise fundamentalista.

**Non-Goals:**
- Alterar dados/colunas da tabela (change `fundamentos-table-data`).
- Redesenhar o mecanismo de cache.

## Decisions

### 1. Persistência de larguras

Adicionar `fundamental_column_widths` ao `DEFAULT_CONFIG`, mapeando id da coluna → largura. O painel recebe as larguras iniciais e um callback de mudança; a leitura é feita na construção e o salvamento em `_on_close`, seguindo o padrão de `sash_positions`. A chave é o id estável da coluna, não o índice, para resistir a reordenação.

**Alternativa considerada:** salvar em arquivo separado — rejeitada por fragmentar as preferências já centralizadas.

### 2. Resultado de cache por ticker

O adapter passa a devolver o `CacheOutcome`; o `CompositeFundamentalProvider` agrega por ticker (`HIT`/`REVALIDATED` = cache; `UPDATED`/`MISS` = rede). O caso de uso acumula o estado por ticker e classifica falhas recuperáveis (ticker isolado) versus catastrófica (job inteiro), publicando esse resumo no resultado do job.

**Alternativa considerada:** manter o booleano `atualizou` — rejeitada por não distinguir cache de falha nem permitir o sufixo por ticker.

### 3. Ciclo do cursor

Reter o cursor "watch" até o término do job fundamental. O `on_operation_finished` deixa de limpar o cursor quando há job em andamento; a limpeza ocorre em `on_fundamental_result`/erro, com um contador de operações ativas para evitar liberar cedo demais.

**Alternativa considerada:** mover a análise fundamental para dentro da operação principal — rejeitada por manter a responsividade do Tk e o isolamento atual.

## Risks / Trade-offs

- **[Risco] Cursor preso se o job fundamental falhar sem publicar resultado** → Sempre liberar o cursor no caminho de erro do job e no `finally` do controller.
- **[Risco] Muitas chaves de largura no `config.json`** → Mapear apenas colunas redimensionadas e ignorar valores inválidos na leitura.
- **[Trade-off] Dependência de ordem de arquivamento** → Arquivar `fundamental-metrics-table` e `conditional-cache-fundamentus-cvm` antes desta.
