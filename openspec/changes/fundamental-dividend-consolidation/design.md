## Context

`domain/fii/dividends.py` define `TendenciaDividendo` (`SUBINDO`/`CAINDO`/`MANTEVE`/`N_A`) e `calcular_ultimo_dividendo`, que consome `list[Provento]` vindos de `FiiFundamentalRepository.obter_proventos` (hoje `B3FundamentalRepository`, apenas B3). A tabela exibe o rótulo via `_rotulo_dividendo`. Ver `proposal.md - Why`.

## Goals / Non-Goals

**Goals:**
- Trocar a regra de tendência por comparação direta igual/acima/abaixo.
- Consolidar o histórico de dividendos de B3, CVM e Fundamentus.

**Non-Goals:**
- Alterar as demais colunas ou a classificação de ativos (change `fundamentos-table-data`).
- Introduzir histórico de dividendos fora das três fontes citadas.

## Decisions

### 1. Rótulos e comparação estrita

Substituir os valores do enum por `CRESCIMENTO`/`REDUCAO`/`NEUTRO` (mantendo `N_A`) e remover o parâmetro de banda de `calcular_tendencia`. A comparação usa `Decimal` diretamente: `ultimo > anterior` → `CRESCIMENTO`; `ultimo < anterior` → `REDUCAO`; senão `NEUTRO`.

**Alternativa considerada:** manter a banda com valor 0 — rejeitada por deixar um parâmetro sem efeito e manter a API confusa.

### 2. Consolidação de fontes

Estender a porta de dividendos para devolver um histórico consolidado com origem por entrada. Ordem de prioridade por recência: B3 (histórico estruturado), CVM (informes), Fundamentus (`Dividendo/cota` como valor escalar de último recurso). A consolidação remove duplicatas por data-base e mantém a fonte que forneceu cada valor.

**Alternativa considerada:** escolher uma única fonte por ticker — rejeitada porque a proposta pede "pegar o que estiver faltando".

### 3. Papel do `Dividendo/cota`

O campo `Dividendo/cota` do Fundamentus é a soma dos rendimentos dos últimos 12 meses (confirmado na página real). Ele é usado apenas como fallback quando B3 e CVM não têm histórico, tratado como o último dividendo disponível, e essa semântica fica registrada como aviso/evidência.

**Alternativa considerada:** tratar `Dividendo/cota` como dividendo mensal — rejeitada por contrariar o rótulo real da fonte.

## Risks / Trade-offs

- **[Risco] `Dividendo/cota` (12m) comparado a um dividendo mensal distorce a tendência** → Só usar o campo quando não houver histórico; documentar a origem na evidência.
- **[Risco] Duplicidade de proventos entre B3 e CVM** → Deduplicar por (data-base, valor) ao consolidar.
- **[Trade-off] Dependência de ordem de arquivamento** → Arquivar `fundamental-metrics-table` antes desta para materializar `dividend-metrics`.
