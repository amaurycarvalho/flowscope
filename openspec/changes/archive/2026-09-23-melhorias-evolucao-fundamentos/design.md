## Context

Ver `proposal.md` para a motivação. O painel `FundamentalEvolutionPanel` desenha small multiples a partir de `montar_series` (`fundamental_evolution_data.py`), que hoje produz sete séries a partir de `CAMPOS_EVOLUCAO`. A grade é `4x2` e apenas sete eixos são criados (`range(_LINHAS * _COLUNAS - 1)`), deixando a oitava célula livre. Os rótulos do eixo usam `strftime("%m/%y")` e não há interação de hover — nenhum `motion_notify_event` é conectado.

O campo `AnaliseFundamental.short.shorts_pct` já é calculado e persistido pela change `analise-short-interest` (schema de fundamentos v2), então a nova série é somente de apresentação: nenhuma porta, fonte, domínio ou migração de cache é necessária.

O padrão de tooltip já existe no projeto (`dominance_timeline.py`, `price_range_panel.py`): um `annotate` com `bbox`, um handler `motion_notify_event` e a busca do ponto mais próximo.

## Goals / Non-Goals

**Goals:**

- Acrescentar a oitava série (`Shorts%`) usando a célula livre da grade, sem redesenhar o layout.
- Rotular as datas com dia/mês/ano e formatar `Shorts%` com uma casa decimal.
- Oferecer tooltip de data e valor em todos os oito painéis, reutilizando o padrão de hover existente.
- Manter a montagem de séries pura e sem I/O.

**Non-Goals:**

- Alterar fontes, domínio, schema do cache histórico ou a tabela de Fundamentos.
- Adicionar zoom, seleção ou exportação de pontos individuais.
- Mudar a amostragem Fibonacci das datas ou a ordenação cronológica.

## Decisions

### Nova série via `CAMPOS_EVOLUCAO` e a célula livre da grade

Adicionar `CampoEvolucao("shorts_pct", "Shorts%", TIPO_PERCENTUAL_1, _shorts_pct)` ao fim de `CAMPOS_EVOLUCAO`, com extrator tolerante (`analise.short.shorts_pct if analise.short else None`). No painel, trocar `range(_LINHAS * _COLUNAS - 1)` por `range(_LINHAS * _COLUNAS)`, passando a usar os oito eixos da grade `4x2`. A suptitle e o `_configurar_eixo_x` já operam por índice e não precisam de ajuste estrutural.

Alternativa descartada: criar uma subclasse de painel dedicada — duplicaria o pequeno-múltiplo e a lógica de eixo.

### Um tipo de formatação para percentual com uma casa

O `_FORMATADORES` mapeia `TIPO_PERCENTUAL` para `formatar_percentual(valor, 2)`, compartilhado com o Dividend Yield, que deve permanecer com duas casas. Para não alterar o Dividend Yield, adicionar uma constante `TIPO_PERCENTUAL_1` mapeada para `formatar_percentual(valor, 1)`, mantendo `formatar_ponto(tipo, valor)` com a assinatura atual.

Alternativa descartada: adicionar um atributo `casas` a `CampoEvolucao`/`SerieEvolucao` e propagá-lo por `formatar_ponto` — mais invasivo para o ganho, alterando assinaturas e testes existentes.

### Formato de data `%d/%m/%y`

Trocar o rótulo de `data.strftime("%m/%y")` para `data.strftime("%d/%m/%y")` e usar o mesmo formato no texto do tooltip, mantendo a coerência entre eixo e tooltip (`01/09/26`).

### Tooltip por eixo, seguindo o padrão existente

Conectar `motion_notify_event` no canvas e manter uma lista de anotações alinhada a `self._axes`. Cada anotação é (re)criada ao desenhar a série, com `bbox` no estilo já usado pelos outros painéis. No handler:

- Se `event.inaxes` não for um dos eixos com série, ocultar a anotação e `draw_idle`.
- Caso contrário, converter cada ponto via `ax.transData` para coordenadas de display e escolher o de menor distância em pixels; se estiver dentro de um limiar (ex.: 20 px), exibir `Data` (DD/MM/AA) e o valor formatado pelo formatter do campo; senão, ocultar.
- Limpar/ocultar todas as anotações em `update`/`reset` para não deixar resíduos entre redesenhos.

Usar distância em pixels (em vez de apenas no eixo X) evita disparos quando o cursor está distante do traço, e o limiar restringe o redesenho.

Alternativa descartada: reutilizar `pick_event` com `picker=True` — exigiria seleção por clique e não cobre a leitura de hover pedida.

### Texto de orientação e documentação

Atualizar `TAB_CONFIGS` (incluir `shorts_pct`), o `TAB_CONTENT` da sub-aba ("sete" → "oito mini-gráficos" e inclusão do `Shorts%` em indicadores/como interpretar) e `panels.md` (campos, diagrama da grade e interação). São textos de apresentação alinhados aos specs `fundamental-evolution-panel` e `gui-interface`.

## Risks / Trade-offs

- **Shorts% ausente em observações antigas do cache** → observações gravadas antes do schema v2 são recomputadas no acerto do cache; quando ausente, o painel mostra "sem dado" sem afetar os demais, conforme o spec.
- **Custo de redesenho no hover** (oito eixos) → exibir a anotação apenas quando há ponto dentro do limiar e usar `draw_idle`, evitando redesenho contínuo.
- **Ambiguidade do formato `%d/%m/%y`** (dia vs. mês em leitores acostumados a `MM/DD`) → o projeto é pt-BR e o exemplo é explícito no spec; o formato permanece determinístico.
- **Conversão de coordenadas no hover** com eixos de escala muito diferentes → a comparação é feita em pixels, o que normaliza as escalas entre os painéis.

## Migration Plan

1. Domínio de apresentação: novo campo/tipo em `fundamental_evolution_data.py` e ajuste de eixos no painel.
2. Formato de data no eixo e no tooltip.
3. Tooltip de hover nos oito eixos.
4. Textos (`app_tabs.py`, `panels.md`) e testes.

Rollback: reverter os arquivos de apresentação é suficiente; não há migração de dados nem alteração de schema.
