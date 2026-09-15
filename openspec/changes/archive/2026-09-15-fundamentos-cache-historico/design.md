## Context

Ver `proposal.md` — Why. Restrições relevantes para o desenho:

- O resultado por ticker é o dataclass `AnaliseFundamental` (`domain/fii/analysis.py`), com `Decimal`, `date`, enums (`ClassificacaoAtivo`, `ClasseCotistas`, `ClassePatrimonio`, `TendenciaFfo`) e dataclasses aninhadas (`MetricasFii`, `MargensFii`, `UltimoDividendo`, `ClassificacaoExibicao`), além de `dict[str, Decimal]` (`indexadores`).
- O `FundamentusProvider` **ignora** `reference_date` (`infrastructure/fii/fundamentus/adapter.py`); a data só afeta B3/CVM/preço. Logo a única data estável para chave é a data solicitada na carga.
- O `ConditionalCache` existente guarda **um registro por chave** com retenção e eviction; não serve para múltiplas observações datadas.
- A convenção do projeto é JSON em `~/.cache/flowscope` com escrita atômica via `CacheManager` (`infrastructure/cache.py`), e a injeção de dependências é feita no controlador (`presentation/gui/controller_fundamental.py`).
- A análise roda em thread de background com token de geração e publica resultados por fila; os resultados são memorizados em memória por ticker para a carga corrente.

## Goals / Non-Goals

**Goals:**

- Cachear o resultado estruturado por `(ticker, data solicitada)`, com retenção de 365 dias.
- Read-through no `FundamentalAnalysisUseCase`, preservando o comportamento atual quando não há store.
- Recuperação histórica por data específica, lista de datas e intervalo.
- Nunca servir/gravar dado envenenado por falha; permitir correção no mesmo dia.

**Non-Goals:**

- UI de evolução do ticker (gráficos/série) — fica para uma change futura; aqui só a porta de recuperação.
- Substituir os caches condicionais por provider; o novo cache é uma camada acima.
- Migrar ou invalidar caches existentes.
- Cache distribuído/SQLite.

## Decisions

### 1. Chave `(ticker, data solicitada)`; `data_referencia` no conteúdo

A chave é a data pedida na carga; a `data_referencia` observada é gravada dentro do registro. Motivo: o Fundamentus ignora a data, então só a data solicitada é estável e alinhada a "mesmo ticker e data". Alternativas: chavear por `data_referencia` (pode ser `None` e gera pontos intradiários) ou manter as duas camadas (complexidade sem ganho claro).

### 2. Persistir `AnaliseFundamental` estruturado com `schema_version`

Serialização explícita (`to_dict`/`from_dict`) com `Decimal` como string, `date` em ISO e enums pelo valor; a versão do schema é gravada por observação. Alternativa descartada: persistir a linha formatada (lossy, dependente do layout de colunas).

### 3. Um JSON por ticker com mapa `data -> observação`

Caminho `~/.cache/flowscope/fundamentos/{TICKER}.json`, com escrita atômica (tmp + rename) reaproveitando a convenção do `CacheManager`. Motivo: recuperar a série completa do ticker é uma leitura só, e o prune vira filtro no mapa. Alternativas: um arquivo por `(ticker, data)` (sprawl e série via glob) e SQLite (novo padrão de persistência sem necessidade).

### 4. Falhas: não grava erro; parcial sobrescrevível; completa imutável no dia

"Completa" = possui identidade do Fundamentus (nome ou cotação); "parcial" = ausência dessa identidade. Em HIT, o store devolve a observação; o `execute` só a registra quando `analise.erro is None`. Uma observação parcial pode ser substituída por uma melhor no mesmo dia; a completa é first-write-wins. Alternativas: só gravar completa (perde linhas úteis quando o Fundamentus cai) e gravar tudo (congela dado ruim).

### 5. Versionamento: HIT estrito, histórico tolerante

O acerto do dia exige `schema_version == atual`; a leitura de histórico devolve observações antigas best-effort, identificando a versão. Alternativas: descartar versão divergente (perde pontos da série) e invalidar o arquivo (perde 365 dias).

### 6. Read-through no caso de uso via porta opcional

Nova porta `FundamentalHistoryStore` (`obter`, `historico`, `datas`, `registrar`) em `application`, injetada no `FundamentalAnalysisUseCase`; ausente, o comportamento é o de hoje. Alternativa: fazer o check no controlador (vazaria regra de negócio para a apresentação e dificultaria os testes).

### 7. Bypass explícito

`execute(..., force_refresh: bool = False)` propaga ao read-through: ignora o HIT e sobrescreve a observação do dia, inclusive completa. Alternativa: sem bypass (usuário preso ao snapshot do dia).

A ação na GUI é um botão da barra da lista de tickers, com ícone `edit-redo.png` e tooltip "Atualizar fundamentos", posicionado no grupo de seleção logo após "Desmarcar Todos". O botão fica visível apenas quando a sub-aba "Fundamentos" está ativa e é desabilitado durante qualquer carga de dados (integra o conjunto de controles desabilitados pela apresentação). Ao ser acionado, recomputa os tickers exibidos com `force_refresh` e repopula a tabela. Alternativa descartada: botão dedicado dentro da sub-aba, que exigiria uma segunda barra e poluiria a área da tabela.

### 8. Retenção e prune

Janela deslizante de 365 dias a partir da data corrente: na escrita, descarta observações anteriores ao limite; na leitura, ignora expiradas. Alternativa: prune só na leitura (arquivo cresce indefinidamente).

### 9. Escopo

Todos os tickers (FII e Papel), pois a porta é genérica sobre `AnaliseFundamental`.

### 10. Tooltips descritivos dos índices

Os botões de índice IBOV, IDIV e IFIX recebem tooltips curtos com apenas a descrição do índice (sem sigla nem travessão): "principais ações negociadas na B3", "ações com os maiores dividendos da B3" e "principais fundos imobiliários (FIIs)".

## Risks / Trade-offs

- [Congelar o snapshot do Fundamentus dentro do dia] → bypass explícito e política de parcial sobrescrevível.
- [Serialização divergir quando `AnaliseFundamental` ganhar campos] → `schema_version` por observação e testes de round-trip; o HIT do dia recomputa ao detectar versão antiga.
- [Observações parciais antigas no histórico com menos campos] → marcação de versão e leitura best-effort documentada.
- [Reescrita do arquivo do ticker a cada nova data] → payload pequeno (dezenas de campos) e escrita atômica; aceitável para 365 pontos.
- [Concorrência entre a thread de análise e leituras] → um arquivo por ticker, escrita atômica por rename; sem lock compartilhado necessário.
- [Resultados em memória da carga anterior vazarem para outra data] → a chave inclui a data e a tabela é repopulada por carga; teste cobre a troca de data.

## Migration Plan

Nenhuma migração: é um store novo, populado a partir da primeira carga após a mudança. Rollback = não configurar o store (o read-through fica inerte) ou remover o diretório `~/.cache/flowscope/fundamentos`.
