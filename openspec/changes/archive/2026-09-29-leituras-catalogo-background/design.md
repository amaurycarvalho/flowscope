## Context

Ver `proposal.md - Why`. Hoje os painéis leem o cache diretamente na thread do Tk: `DocumentTreePanel.update` chama `ConsultarCatalogoUseCase.executar(ticker)` (varredura de diretórios + leitura de índice de resumos), `NoticiasPanel.update` chama `ConsultarCatalogoNoticiasUseCase.secoes()` (leitura de índice + checagem de existência de HTML por item) e `ActionsMixin._update_fundamental_evolution` lê `JsonFundamentalHistoryStore.datas/historico` e chama `montar_series`. Os painéis não conhecem threads hoje; quem orquestra jobs é o mixin de ações (`app_actions`, `noticias_actions`). A fatia A forneceu o `BackgroundManager`.

## Goals / Non-Goals

**Goals:**
- Tirar as leituras de catálogo/séries da thread do Tk, com estado de carregamento e descarte de leituras obsoletas.
- Manter os painéis como views, sem introduzir dependência de threading neles.
- Testar `carregar_*`/preparação de séries headless; manter em UI apenas `aplicar_*`, estado de widget e empty-state.

**Non-Goals:**
- Alterar as regras de varredura/catálogo (permanecem em `application`/`infrastructure`).
- Introduzir cache em memória de longo prazo para os catálogos.
- Migrar a pré-visualização/resumo individual, que já roda em background.
- Adicionar testes `@needs_display` para varredura/leitura de catálogo.

## Decisions

### Decisão 1: Painéis expõem "preparar" (worker) e "aplicar" (Tk); o mixin submete

**Escolha**: cada painel ganha um método puro de preparação executável no worker (`carregar_catalogo(ticker)`, `carregar_secoes()`) e um método de aplicação na thread do Tk (`aplicar_catalogo(ticker, catalogo)`, `aplicar_secoes(catalogo)`). O mixin de ações submete o trabalho ao manager e registra o callback de resultado. O `update()` existente passa a delegar a submissão (ou é substituído nos pontos de chamada).

**Alternativas**: injetar o `BackgroundManager` nos painéis; manter a leitura no painel e apenas envolver em thread.

**Razão**: preserva a separação atual (painéis são views; mixins orquestram) e mantém os painéis testáveis sem threads. Injeta threading no painel e espalha a dependência do manager pela árvore de widgets.

### Decisão 2: Séries da evolução preparadas no worker

**Escolha**: extrair a montagem das séries de `_update_fundamental_evolution` para uma função de trabalho que lê `store.datas/historico`, aplica a janela e chama `montar_series`; a aplicação no painel (`painel.update`) ocorre por evento.

**Alternativas**: manter a leitura na thread do Tk por ser pequena.

**Razão**: a leitura pode tocar muitos arquivos por ticker; a migração é uniforme e barata, e o `store` já é usado fora do Tk pelo job fundamentalista.

### Decisão 3: Grupo e política por painel com `key` de ticker

**Escolha**: grupo por painel (`"documentos"`, `"noticias"`, `"evolucao"`), política `latest_wins`, `key` derivada do ticker/escopo. Trocar de ticker descarta a leitura anterior.

**Alternativas**: `serialize`.

**Razão**: a leitura mais recente é a única relevante; `latest_wins` evita trabalho obsoleto e casa com a semântica de "ticker apresentado".

### Decisão 4: Estado de carregamento e empty-state preservados

**Escolha**: reutilizar `mostrar_carregando` (documentos) e adicionar equivalentes para notícias/evolução; cache frio continua resultando em estado vazio após a leitura.

**Alternativas**: não exibir carregamento (transição direta).

**Razão**: a leitura agora é assíncrona; sem estado de carregamento haveria um piscar de conteúdo antigo. As specs dos painéis passam a exigir o carregamento.

### Decisão 5: Estratégia de teste — preparação headless, aplicação em UI

**Escolha**: testar `carregar_catalogo`/`carregar_secoes`/preparação de séries diretamente, sem `tk.Tk` (headless), incluindo cache frio, ordenação e filtragem de entradas sem HTML. Ficam sob `@needs_display` apenas `aplicar_*`, o estado de carregamento/empty-state e a remontagem da árvore — o mínimo que só existe na presença do Tk.

**Alternativas**: testar cada leitura através de uma instância de painel com Tk (como hoje em `test_document_tree_panel.py`/`test_noticias_panel.py`).

**Razão**: a separação "preparar (worker) / aplicar (Tk)" torna a maior parte do comportamento verificável headless. Testar a varredura via Tk é custo sem cobertura adicional e mantém inflada a contagem de `@needs_display`.

## Risks / Trade-offs

- **[Risco]** `latest_wins` no painel de documentos competir com o job de aquisição (`"documentos"` já é usado para aquisição) → **Mitigação**: usar grupos distintos (`"documentos-leitura"` vs. `"documentos-aquisicao"`), já que a aquisição publica progresso e a leitura não.
- **[Risco]** Aplicar um catálogo de leitura antiga sobre a árvore recém-atualizada por uma aquisição → **Mitigação**: `key`/geração por escopo e teste de leitura obsoleta descartada.
- **[Risco]** Estado de carregamento piscar em leituras muito rápidas → **Trade-off** aceito; pode ser atenuado com um pequeno atraso de exibição, a decidir na implementação.
- **[Trade-off]** Um `after` a mais por leitura → **Benefício**: interface responsiva com caches grandes.

## Migration Plan

1. Extrair `carregar_catalogo`/`aplicar_catalogo` no painel de documentos e migrar a chamada em `app_actions`/`_update_documentos`.
2. Extrair `carregar_secoes`/`aplicar_secoes` no painel de notícias e migrar `_update_noticias`/`_remontar_noticias`.
3. Extrair a preparação das séries da evolução e migrar `_update_fundamental_evolution`.
4. Ajustar as specs dos três painéis (deltas deste change) e validar.
5. Migrar os testes de leitura para headless (via `carregar_*`), reduzir os testes de UI de varredura e confirmar que a contagem de `@needs_display` não aumentou em relação ao baseline da fatia A.
6. Rodar os testes de painel/integração; rollback = reverter o commit (sem migração de dados).
