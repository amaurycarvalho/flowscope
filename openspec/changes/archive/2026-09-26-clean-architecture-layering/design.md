## Context

Ver `proposal.md` — Why. O estado atual que molda o desenho:

- `presentation` já possui o padrão correto de fronteira em `presenter.py`: depende de um `GUIView` Protocol e é testado sem Tk. É o modelo a generalizar.
- Já existe um teste de fronteira, mas restrito ao subpacote FII (`tests/test_domain/test_fii/test_layer_boundaries.py`); não cobre as demais camadas.
- A camada `domain` hoje não importa `application`/`infrastructure`/`presentation`, e `application` não importa `infrastructure`/`presentation`. O problema concentra-se em: lógica pura sob `presentation/gui/charts/`, entidades sob `infrastructure`, e imports `presentation -> infrastructure` fora do composition root (contagem atual: 27 ocorrências em painéis, chat e stores).
- Restrição de CI: `make test` roda em `ubuntu-latest` sem `DISPLAY`, então testes marcados `needs_display` são ignorados. Não piorar isso é requisito.

## Goals / Non-Goals

**Goals:**

- Fixar o contrato de fronteira, a localização de entidades/regras e a convenção de view-model (ver `specs/layer-boundaries/spec.md`).
- Decompor o programa em incrementos que chegam ao estado-alvo (A) sem um PR único.
- Tornar o estado-alvo irreversível por teste (guardrail com allowlist que só encolhe).
- Migrar testes de lógica pura de `test_presentation` para `test_domain`/`test_application`.

**Non-Goals:**

- Não alterar comportamento observável, rótulos, números ou layout.
- Não introduzir framework de arquitetura, injeção de dependência ou reescrita de UI.
- Não mover parsing/I/O de `infrastructure` para `domain` — parsing continua infraestrutura.
- Não converter todo `presentation` em testável sem display; o objetivo é reduzir, não eliminar, os testes de UI.

## Decisions

### D1 — Estratégia incremental por fatia vertical (B), não big-bang (A)

Cada incremento é uma fatia vertical fechada (uma feature: Documentos, Notícias, ...) que move código e testes juntos e mantém paridade de comportamento. Alternativa considerada: um único change por camada (move tudo de `presentation`, depois tudo de `infrastructure`). Rejeitada: gera diffs irrecuperáveis, mistura features e torna a revisão e o rollback inviáveis.

### D2 — Convenção de view-model na fronteira

`application` devolve dataclasses imutáveis já preparadas (séries, linhas, contagens, resumos) e `presentation` apenas formata e desenha. Alternativa: expor o `dict` bruto atual e mover só as funções de cálculo para `application` sem mudar o contrato. Rejeitada como estado final porque a apresentação continuaria acessando `all_indicators`/`daily_data` diretamente; adotamos a migração do contrato em cada fatia, sem big-bang.

### D3 — Guardrail com allowlist decrescente

O incremento de fundação generaliza o teste de fronteira para todas as camadas e registra as violações legadas em allowlist explícita. Alternativa: bloquear tudo de imediato. Rejeitada porque o repositório já contém violações e o teste nasceria vermelho. O fechamento zera a allowlist.

### D4 — Localização de entidades de domínio

Entidades de catálogo e classificação saem de `infrastructure` para `domain`; adaptadores de leitura permanecem em `infrastructure` e a orquestração (montar catálogo, gerar resumo) vai para `application`. Alternativa: manter entidades em `infrastructure` e apenas criar tipos espelho em `domain`. Rejeitada por duplicar modelo.

### D5 — Composition root como única exceção

`presentation` só pode importar `infrastructure` no ponto de composição, isolado (`app_wiring.py`, `main.py`, `cli.py`), que fica na allowlist até o fechamento e é o único resíduo aceito. O restante da apresentação passa a depender de portas/use cases de `application`.

### D6 — Ordem das fatias por payoff de teste

Fundação primeiro; depois Documentos e Notícias (maior volume de testes de UI: `document_tree_panel` 133, `noticias_panel` 37); por fim as fatias de gráficos e o fechamento. Fatias pequenas e independentes (Rede, Dominância, Quadrante+VWAP, Amplitude, Fluxo, Fundamentos, Chat) podem ir em qualquer ordem.

```
[F] guardrails
     |
     +--> [1] Documentos --+
     +--> [2] Noticias ----+--> [C] fechamento --> A
     +--> [8] Fundamentos -+
     +--> [3][4][5][6][7][9] (independentes)
```

## Risks / Trade-offs

- [Diff grande por fatia] → limitar cada change a uma feature; manter paridade de comportamento coberta por testes que acompanham o código movido.
- [Allowlist virar dívida permanente] → o incremento de fechamento (C) é obrigatório e o guardrail verifica que a allowlist está vazia.
- [Migração de testes quebra cobertura/mutation] → mover (não reescrever) os testes junto do código; recalcular baseline de cobertura e mutação ao fim de cada fatia.
- [Ciclos de import ao mover entidades] → mover sempre no sentido das dependências (entidade antes do adaptador) e deixar o guardrail acusar regressões.
- [Reduzir testes de UI esconde bugs visuais] → manter o conjunto mínimo de UI que cobre wiring/estado/empty-state/thread, e considerar um smoke opcional sob Xvfb no futuro.

## Migration Plan

1. **F** — `add-layer-architecture-guardrails`: teste de fronteira generalizado + allowlist inicial + convenção de view-model documentada.
2. **1-9** — fatias verticais (`refactor-documentos-layers`, `refactor-noticias-layers`, `refactor-correlation-network-layers`, `refactor-dominance-panels-layers`, `refactor-quadrant-vwap-layers`, `refactor-price-range-layers`, `refactor-flow-panels-layers`, `refactor-fundamental-table-layers`, `refactor-chat-context-layers`), cada uma removendo suas entradas da allowlist e migrando os testes correspondentes.
3. **C** — `enforce-clean-architecture-boundaries`: allowlist vazia, imports de infraestrutura restritos ao composition root.

Rollback: cada incremento é independente e preserva comportamento; reverter um change reverte apenas sua fatia.

## Open Questions

- O agrupamento opcional de fatias pequenas (Rede+Quadrante+VWAP; Amplitude+Fluxo) pode ser decidido ao criar cada change filho, sem alterar as specs ou a abordagem.
