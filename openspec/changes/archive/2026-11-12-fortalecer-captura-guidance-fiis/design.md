## Context

Ver `proposal.md` — Why. A avaliação da watchlist atual mostrou que a captura cobre os RGs recentes, mas a qualidade derivada depende de decisões implícitas no ledger:

- `RZAK11` tem, para `2026-08`, uma entrada `deterministico` (`1,05`) e uma `ia` (`1,00–1,10`); a derivação por `max(data_relatorio)` pode escolher o determinístico e exibir o valor errado.
- `GGRC11` tem o mesmo RG com `ia` período `2026` e determinístico sem período; o desempate também não é definido.
- `BTLG11`, `GGRC11` e `RZAK11` exibem períodos vagos/ausentes, e a resposta da IA é aceita sem normalização.
- Entradas `ia` não são reavaliadas; uma resposta ruim fica congelada mesmo após melhoria de prompt/modelo. O ledger atual é quase todo `ia`, então esse congelamento afeta a maior parte da watchlist.

O store atual (`JsonGuidanceStore`) usa schema v2, sem campos de proveniência. A derivação fica em `_corrente`; a interpretação da resposta em `AvaliarGuidanceUseCase._interpretar`; o controle por método em `avaliar_rg`; e a chave de conteúdo é o hash do PDF.

## Goals / Non-Goals

**Goals:**
- Tornar a derivação determinística e auditável (método e momento da avaliação).
- Permitir reavaliação controlada quando o prompt ou o modelo mudar, sem perder resultados anteriores em caso de falha.
- Aumentar a tolerância à resposta da IA e evitar ausência indevida quando a resposta é semanticamente SIM mas não parseável.
- Melhorar a qualidade do período exibido.
- Diagnosticar conflitos entre a IA e o extrator determinístico sem alterar silenciosamente a decisão da IA.

**Non-Goals:**
- Criar uma nova fonte de guidance ou alterar a prioridade Fundamentus → B3 → CVM.
- Reavaliar automaticamente toda a watchlist em segundo plano na carga de fundamentos; a reavaliação ocorre nos fluxos existentes de leitura/lote de RGs.
- Expirar guidance por antiguidade ou inferir o fim do período; a mudança não altera a regra “ausência recente não apaga guidance anterior”.
- Migrar destrutivamente o ledger ou reescrever PDFs/hashes.

## Decisions

### 1. Proveniência opcional no ledger, sem bump destrutivo

Adicionar `avaliado_em`, `prompt_version` e `modelo` como campos opcionais de `AvaliacaoGuidance` e do JSON. O schema permanece v2: entradas antigas continuam legíveis, e a ausência de `prompt_version` é o sinal de “desatualizada” para reavaliação. Um bump de schema obrigaria uma migração que descartaria ou reescreveria entradas sem necessidade.

- **Alternativa descartada**: schema v3 com migração obrigatória. A compatibilidade é mais valiosa e os campos são aditivos.
- **Alternativa descartada**: reavaliar sempre. Aumentaria custo de LLM em toda leitura sem ganho quando a versão é a mesma.

### 2. Versão do prompt como constante de aplicação e modelo opcional

Definir `PROMPT_VERSION` junto de `SYSTEM_PROMPT` e gravá-la em cada avaliação. O modelo é obtido, quando o adaptador expõe `modelo`, via atributo opcional; sem esse dado, grava-se vazio e a reavaliação fica governada apenas pela versão do prompt.

- **Alternativa descartada**: incluir o texto do prompt no ledger. A versão é suficiente e evita duplicação.

### 3. Derivação com precedência `ia` > `deterministico` > mais recente

`_corrente` passa a ordenar por `(data_relatorio, prioridade_metodo, avaliado_em)` e escolher o maior. `ia` vence o determinístico na mesma data; dentro do mesmo método, a avaliação mais recente vence. Entradas antigas sem `avaliado_em` ficam atrás das que têm o campo e, entre si, mantêm uma ordem estável.

- **Alternativa descartada**: escolher sempre `ia` independentemente da data. Isso poderia promover uma avaliação antiga sobre um RG mais recente com determinístico; a data continua sendo o critério primário.
- **Alternativa descartada**: não desempatar e ordenar por chave. É o comportamento atual e produziu a ambiguidade observada.

### 4. Interpretação da IA em três estados

`_interpretar` deixa de devolver apenas `Guidance | None` e passa a distinguir `guidance`, `ausente` e `invalida`. `ausente` (`GUIDANCE: NAO`) é decisão válida; `invalida` (`GUIDANCE: SIM` sem valor interpretável) é falha de interação e aciona o extrator determinístico, preservando a regra de fallback já existente. A leitura tolera `R$`, milhar, faixa na mesma linha e sufixo “por cota”.

- **Alternativa descartada**: tratar resposta inválida como ausência. Foi o risco identificado: uma resposta mal formatada enterraria guidance real e ainda marcaria a entrada como `ia`.

### 5. Normalização de período apenas para exibição/armazenamento

Períodos vagos conhecidos (`não especificado`, `sem período`, `N/A`, vazio) são convertidos em string vazia; períodos reconhecidos são preservados como o modelo os devolveu. Não se tenta converter “2S26” em datas nem inferir validade.

- **Alternativa descartada**: parsing completo de períodos para datas. Complexidade alta e sem requisito de expiração nesta change.

### 6. Conflito IA x determinístico é apenas diagnóstico

Quando a cascata da IA conclui ausência em todas as fontes, o extrator determinístico é executado sobre as mesmas fontes e, se encontrar guidance, um warning é registrado com ticker, data, valores e período. O ledger e a decisão da IA permanecem inalterados.

- **Alternativa descartada**: usar o determinístico para sobrescrever a ausência da IA. O caso `RZAK11` mostra que o determinístico pode capturar uma distribuição passada (`1,05`) em vez da faixa de guidance (`1,00–1,10`); sobrescrever aumentaria falsos positivos.

## Risks / Trade-offs

- **Reavaliação em massa de entradas antigas** → ocorre no máximo uma vez por entrada, nos fluxos já existentes de leitura/lote, reutilizando resumos e texto; falhas preservam o resultado anterior.
- **Modelo não exposto pelo adaptador** → a versão do prompt ainda rege a reavaliação; o campo `modelo` fica vazio e não bloqueia a leitura.
- **Parsing tolerante aceitar valor indevido** → a validação continua exigindo mínimo/máximo numéricos e ordena a faixa; a origem e a data permanecem registradas para auditoria.
- **Período útil descartado como vago** → só são convertidos rótulos explicitamente vagos; qualquer período reconhecido é preservado.
- **Warning de conflito ruidoso** → é apenas log, sem alteração de ledger; pode ser filtrado por nível/ambiente.
- **Entradas sem `avaliado_em` em empates** → a ordem entre elas é estável, mas não há como saber qual avaliação é mais recente; a reavaliação por versão corrige as entradas antigas na próxima passagem.

## Migration Plan

1. Publicar o código mantendo o schema v2 e lendo os campos opcionais.
2. Na primeira avaliação por IA após a mudança, gravar `prompt_version`/`avaliado_em`/`modelo`.
3. Entradas `ia` sem versão viram acionáveis para reavaliação nos fluxos existentes; falha preserva a entrada antiga.
4. Rollback: remover a leitura dos novos campos e voltar ao desempate anterior; o ledger permanece compatível e os campos extras são ignorados.

## Open Questions

Nenhuma.
