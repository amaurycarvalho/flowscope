## Context

Ver `proposal.md` — Why. O lote de notícias usa `painel.documentos_sem_resumo()`, que devolve `self._itens.values()` na ordem de inserção da árvore (`document_flow_mixin.py:38`). Essa ordem é seção-major (`SECOES_ORDEM`) e, dentro da seção, ano/mês decrescentes; porém, no nível folha, a ordenação da árvore usa o *stem* do arquivo (`document_catalog.py:252`), que para notícias é um `sha1` (`noticias_aquisicao.py:189`) — praticamente aleatório. `NoticiaArquivo` carrega `secao` e `data_publicacao`, hoje sem uso na ordenação. A persistência depende de `documentos-resumo-lote-persistente`.

## Goals / Non-Goals

**Goals:**
- Ordem explícita e determinista do lote: grupos na ordem de `SECOES_ORDEM` e, dentro do grupo, mais recente → mais antiga.
- Reaproveitar o seam de persistência no worker introduzido pela change de Documentos.
- Não alterar a ordem de exibição da árvore nem o conteúdo da pré-visualização.

**Non-Goals:**
- Mudar a estrutura da árvore (ano → mês → categoria → item).
- Introduzir ordenação por data na exibição ou nas demais ações do painel.
- Definir `SECOES_ORDEM` de novo — a constante existente é a fonte da ordem dos grupos.

## Decisions

### 1. Ordenação explícita na fachada do painel

A lista de pendentes do lote passa a ser produzida por um caminho que ordena, em vez de herdar a ordem da árvore. A chave de ordenação é `(índice da seção em SECOES_ORDEM, data de publicação decrescente, desempate determinista)`. O desempate (ex.: categoria e caminho) garante estabilidade entre execuções.

Alternativa considerada: ordenar dentro de `documentos_sem_resumo()` — descartada porque esse método também é usado por Documentos, cuja ordem não deve mudar.

### 2. Parsear a data, não comparar strings

`data_publicacao` vem em formatos variados (`"2026-09-20 10:00:00"`, `"2026-07-28"`, possivelmente vazio). Comparar strings é frágil; a ordenação usa o helper de parsing já existente (`data_noticia`/`para_data`) e, quando a data é ausente ou inválida, cai para `(ano, mes)` derivados do caminho do item — que já estão em `NoticiaArquivo`.

Alternativa considerada: ordenar por `(ano, mes, nome)` — descartada porque o nome é `sha1` e não reflete a cronologia dentro do mês.

### 3. Reuso do seam de persistência

Em vez de regravar por conta própria, o lote das notícias liga o mesmo gancho de persistência no worker criado por `documentos-resumo-lote-persistente`. A thread do Tk continua apenas refletindo o resultado.

### 4. Ordem do lote não é ordem da árvore

A árvore permanece como está; a ordenação é aplicada ao snapshot de pendentes entregue ao job. Assim a interface não muda e a regra fica testável isoladamente.

## Risks / Trade-offs

- [Formatos de data heterogêneos entre as quatro seções] → parse tolerante com fallback `(ano, mes)` e desempate determinista; cenário de teste dedicado.
- [Atrito com `refactor-documentos-layers`] → a regra nasce na apresentação e é candidata natural ao `application`/`domain`; manter isolada em um único ponto para facilitar a migração.
- [Dependência entre changes] → implementar depois de `documentos-resumo-lote-persistente`, pois ambas tocam `app_resumos_actions.py` e `resumos_job.py`.

## Migration Plan

1. Implementar e validar primeiro `documentos-resumo-lote-persistente` (seam e store).
2. Adicionar a ordenação dos pendentes de notícias e testá-la isoladamente.
3. Ligar a persistência no worker para notícias e validar interrupção e ordem.
