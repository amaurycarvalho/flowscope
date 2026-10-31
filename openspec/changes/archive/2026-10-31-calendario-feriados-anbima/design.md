## Context

Ver `proposal.md - Why`. O estado atual combina três problemas:

1. `domain/b3/calendario.py` concentra uma lista estática (`FERIADOS_NACIONAIS`) usada por `application/use_cases.py`, `infrastructure/b3/client.py` e `infrastructure/b3/calendar.py`.
2. O subsistema dinâmico copiado (`application/calendar/`, `infrastructure/calendar/` e `domain/calendar.py`) está não rastreado, importa `b3_selic_pre`, referencia utilitários inexistentes e usa `datetime.UTC` (Python ≥3.11), enquanto o projeto suporta Python ≥3.10.
3. A GUI usa UTC no botão “Hoje” e no `maxdate`; o CLI já usa `date.today()` local.

Restrições relevantes:

- `layer-boundaries`: `domain` não importa outras camadas; `application` não importa `infrastructure`; `presentation` só fala com `application`, exceto composição.
- O lock global existente é `ActionLock`, com bloqueio de arquivo e reentrância por thread. A escrita atômica existente é `_atomic_write_bytes`.
- O cache raiz já é `~/.cache/flowscope` (ou equivalente por plataforma) via `CacheManager`.
- O servidor MCP é stdio, somente-leitura, e hoje expõe exatamente oito tools `nav_*`.
- A amostragem existente ajusta cada data para o **próximo** dia útil; esse contrato não muda.

## Goals / Non-Goals

**Goals:**

- Uma única fonte de verdade para feriados: ANBIMA + cache local, com recesso local explícito.
- Predicado de dia útil injetável, sem `application -> infrastructure`.
- Carga nunca bloqueada por falha do calendário.
- Data de referência resolvida para o dia útil anterior; instantes de cache continuam em UTC.
- Superfícies CLI, MCP e GUI reutilizando o mesmo serviço de aplicação.

**Non-Goals:**

- Janela de evolução de 7/14/21/28 dias.
- Feriados estaduais/municipais.
- Segunda fonte de rede para feriados.
- Alterar a semântica de amostragem para “dia útil anterior”.
- Migrar dados antigos de calendário de outro projeto.

## Decisions

### 1. Modelo puro no domínio, portas na aplicação, I/O na infraestrutura

- `domain/calendar.py` mantém `Holiday` e `HolidayCalendar` (já existentes), puros, com `is_business_day`, `previous_business_day`, `next_business_day` e busca de feriado. `Holiday` ganha `source` (origem individual, padrão `ANBIMA`) para distinguir feriado publicado de recesso local.
- `application/calendar/ports.py` define `HolidaySource`, `HolidayRepository`, `YearHolidays`, erros de fonte e uma porta estreita `BusinessDayLookup` com `calendar_for(year)` e/ou `is_business_day(date)`.
- `application/calendar/service.py` orquestra TTL, fonte, fallback, housekeeping, resolução e exportação de conteúdo. `BusinessDayResolution` ganha `origem` para acompanhar o nome do feriado.
- `infrastructure/calendar/*` implementa HTML, cache, storage, housekeeping e a fábrica.
- `infrastructure/b3/*` e `application/use_cases.py` recebem a porta, nunca o adaptador concreto.

**Alternativa descartada:** manter `is_business_day` estático no domínio e só atualizar a lista. Não atende à fonte ANBIMA, ao TTL nem ao fallback.

**Alternativa descartada:** fazer a aplicação importar `HolidayCache`. Viola `layer-boundaries`.

### 2. Cache por ano em `<cache_root>/calendar`

```text
<cache_root>/calendar/
  holidays/2026.json
  holidays/2027.json
  locks/calendar.lock
```

- Um JSON por ano, com `schema_version` (incrementado por causa da origem individual), `year`, `source`, `source_url`, `fetched_at` (UTC), `ttl_seconds`, `published` e a lista de feriados (`date`, `weekday`, `name`, `source`).
- `calendar_cache_dir()` deriva de `CacheManager().get_cache_dir() / "calendar"`; não usa mais `b3-selic-pre`.
- O lock dedicado é `calendar.lock`; não compartilha o lock global de ação, evitando bloquear cargas longas.
- `write()` usa `ActionLock(caminho=lock_path).adquirir(esperar=<curto>)` + `_atomic_write_bytes`. Se o lock não for obtido, a operação lê o cache existente; sem cache, segue com fim de semana.
- Antes de gravar o resultado de uma busca, a operação relê o cache sob o lock; se outra carga já gravou um ano fresco enquanto esta buscava, o resultado novo é descartado e o cache existente é reutilizado.
- `read()` e `listagem` não criam diretórios, não renomeiam e não removem.

### 3. TTL, estados e fallback

- Ano passado publicado não expira automaticamente; só uma atualização forçada explícita o revalida.
- Ano corrente e anos futuros usam TTL curto (24h por padrão).
- Ano futuro não publicado grava marcador negativo com TTL curto (6h por padrão), tanto para ausência de página quanto para página sem tabela de feriados. Timeout transitório não grava marcador negativo.
- Marcador negativo é sempre lido como estado `calendario_indisponivel`, nunca como `ok`.
- Estados públicos: `ok`, `defasado`, `calendario_indisponivel`.
- Falha da fonte:
  - cache publicado anterior → usar cache, estado `defasado`;
  - sem cache → apenas fim de semana, estado `calendario_indisponivel`.
- `today`/ano corrente para TTL e housekeeping usam a data local do processo; `fetched_at` continua em UTC por ser instante.
- Housekeeping usa o ano local corrente como referência, não o ano carregado, e recebe o ano da operação como protegido. Assim, carregar 2021 em 2026 não remove o próprio 2021 durante a operação.

### 4. Parser ANBIMA all-or-nothing

- Decodifica `iso-8859-1` e usa `HTMLParser` para linhas de tabela.
- Normaliza `d/m/aa` para ISO; remove tags, entidades e acentos; valida o dia da semana declarado.
- Uma linha inválida invalida o ano inteiro; nada é gravado parcialmente.
- `HolidayYearUnavailable` cobre 404 e página sem tabela de feriados; `HolidaySourceError` cobre falha de transporte, timeout e HTML inválido. O serviço só grava marcador negativo para `HolidayYearUnavailable` em ano futuro.
- Recesso local: 24/12 e 31/12 entram quando forem dia de semana e não estiverem na página, com `source` individual próprio. A origem anual continua registrando a proveniência da leitura.
- A página 2026 real tem 13 feriados e é parseável; usar fixture salva nos testes, sem rede.

### 5. Injeção nas cargas

Fluxo de uma carga:

```text
GUI/CLI
  -> data de referência (local)
  -> CalendarService.ensure_year(ano_ref, best_effort=True)
       -> cache fresco? usa
       -> senão ANBIMA; falha -> cache anterior / fim de semana
  -> CalendarService.resolve_business_day(data_ref)  # retrocede
  -> AnalyzeTickersUseCase(repo, business_day=lookup)
       -> sampling continua usando next_business_day
```

- `B3DataRepository` recebe `BusinessDayLookup` para `get_available_dates` e para `has_data`/resolução.
- `B3Client` recebe o mesmo lookup para decidir se requisita o arquivo.
- `use_cases._find_replacement_date` recebe o lookup; o default para testes é “apenas fim de semana”.
- Se `ensure_year` falhar, a carga segue; a falha vai para log e o estado acompanha o payload.
- Quando a data de referência estiver nos primeiros dias de janeiro, a carga também garante o ano anterior, best-effort, para que a resolução atravesse a virada do ano.
- `ensure_year` trata contenção do lock dedicado: espera curta, tenta reler o cache e, sem cache, segue com fim de semana; não propaga a falha para a carga.
- `sampling-strategy` continua usando `next_business_day`; a resolução da referência é separada.

### 6. Consulta, exportação e atualização

- Aplicação expõe:
  - `listar_ano(year)` → metadados + feriados ordenados;
  - `classificar(data)` → dia útil, motivo, nome, estado;
  - `exportar_ano(year, formato)` → `str` CSV/JSON, sem I/O.
- CSV: separador `;`, data ISO, dia da semana abreviado, nome e origem.
- JSON: ano, origem, `fetched_at`, estado e lista.
- CLI:
  - `consultar feriados --ano` lê só cache;
  - `exportar feriados --ano --formato` imprime em `stdout` ou grava com `--saida`;
  - `atualizar feriados [--ano]...` força revalidação e devolve estado por ano.
- MCP: tools `calendario_listar` (exige `ano` inteiro), `calendario_classificar` (exige `data` ISO) e `calendario_exportar` (exige `ano` inteiro e `formato` enum `csv|json`), cache-only, sem escrita de arquivo, com schemas estritos e anotações de leitura.

### 7. Aba `Feriados`

- Nova aba de nível superior “Feriados”, sem sub-notebook, construída sem rede.
- Tratar `Feriados` como aba de nível superior no roteamento de abas, sem consultar `_TICKER` nem exigir sub-aba; incluir entrada em `TAB_CONTENT` para `(Feriados, Feriados)`, de modo que o `OrientationPanel` não mantenha o texto da aba anterior.
- Modelo puro de árvore (ano → mês → dia) em módulo sem Tk, testável headless; a casca Tk só monta o `ttk.Treeview` e o `ReadonlyText`.
- Anos decrescentes; meses e dias crescentes; folha `DD (seg)`.
- Seleção ano/mês/dia gera o texto correspondente no textbox, sem rede.
- Botão `view-refresh` troca para `content-loading` e desabilita durante a atualização em background; ao final, reconstrói a árvore preservando a seleção quando possível.
- Sem cache: árvore vazia e texto orientando a atualizar.
- Falha: mantém árvore/texto e informa defasagem/falha na statusbar.

### 8. Fuso local

- GUI: `date.today()` para “Hoje”, fallback de referência e `maxdate`.
- `CalendarService` usa data local para ano corrente/TTL/housekeeping e para decidir se um ano futuro ainda não foi publicado.
- `fetched_at`, timestamps de cache e logs continuam em UTC.
- As ações da CLI já usam `date.today()` local; `cli_consultas._exportar_vwap` é a exceção atual e passa a seguir o mesmo contrato. `noticias_panel` também passa a usar data local.

### 9. Testes

- Parser: fixture HTML real (2026), data normalizada, acento/entidade, dia da semana divergente, página inesperada, recesso local e origem individual.
- Cache: TTL por recência, ano passado imutável, marcador negativo lido como indisponível, corrupção, escrita atômica, contenção de lock, housekeeping com ano corrente/protegido.
- Serviço: fallback defasado, indisponível, resolução de bloco de feriados (inclusive virada do ano), origem na classificação, exportação CSV/JSON com origem por item.
- Integração: carga garante ano antes de resolver; falha do calendário não bloqueia; referência em feriado retrocede; amostragem continua avançando.
- Fuso: “Hoje”/`maxdate`/fallback usam data local em virada de dia.
- GUI: modelo puro da árvore e wiring mínimo; sem `DISPLAY` para lógica.
- MCP/CLI: schemas, cache-only, ausência de rede, formato de saída e código de saída.

## Decisões pós-implementação

Estas decisões foram tomadas durante a validação da GUI e da suíte, depois da escrita inicial dos artefatos.

### Referência de data na GUI

- **“Hoje” resolve primeiro pelo cache**: `FlowScopeController.on_today` chama `resolve_business_day` antes de carregar. Sem cache, isso corrige imediatamente sábado/domingo; feriados de segunda a sexta só são corrigidos depois que a carga principal garante o ano na ANBIMA.
- **Carga principal corrige o campo ao concluir**: `_ajustar_data_exibida` grava no `DateEntry` a `data_resolvida` devolvida pela carga. Assim, mesmo que a referência tenha sido digitada em um feriado, o campo passa a refletir o dia útil usado.
- **“Atualizar fundamentos” resolve a referência antes do job**: o caminho manual também atualiza `DateEntry` e o rótulo `Dados:`. A resolução usa `resolve_reference`, que faz `ensure_reference` e pode consultar a ANBIMA.
- **Risco aceito**: a resolução de “Atualizar fundamentos” ocorre na thread da interface e pode bloquear a janela até o timeout da fonte quando não há cache. A melhoria futura é mover essa etapa para o job em background, junto com o restante da análise.

### Aba `Feriados`

- A aba é de **nível superior**, sem sub-notebook, e é construída em `_build_main_area` por `_build_feriados_tab`; a ausência dessa chamada era o motivo de a aba não aparecer na primeira validação.
- A árvore é montada **somente do cache**. Se houver anos no cache e nenhuma seleção, o texto orienta “Selecione um ano, mês ou dia”; a mensagem de cache ausente só aparece com a árvore vazia.
- **Não há auto-seleção** do ano mais recente; a seleção é sempre explícita do usuário, preservada quando possível após uma atualização.
- A atualização forçada continua em background, com `view-refresh`/`content-loading`; falha mantém o conteúdo e informa o estado na statusbar.

### LiteLLM × Pydantic

- O ambiente foi atualizado para `litellm 1.106.6` e `pydantic 2.14.2`; o `pyproject.toml` passou a exigir `litellm>=1.106.6`.
- O aviso continua:
  `Item 'summary' on TypedDict class 'ChatCompletionReasoningItem' is using the ReadOnly qualifier...`
- **Decisão: não adicionar filtro de warnings.** O aviso é de terceiros, mas filtrá-lo esconderia uma incompatibilidade real de tipos; a preferência é manter a visibilidade e resolver na origem.
- **Solução futura**: acompanhar o PR upstream `BerriAI/litellm#44178`, que remove o `ReadOnly` do campo `summary` e silencia o aviso. Quando for mergeado e publicado em uma release, atualizar o LiteLLM e remover a pendência. Até lá, o aviso é aceito como ruído conhecido e não bloqueante.

Evidências consultadas na internet:

- `https://github.com/BerriAI/litellm/pull/44178` — PR aberto; remove `ReadOnly` de `ChatCompletionReasoningItem.summary`; ainda não mergeado.
- `https://github.com/hellices/korvid/issues/420` — documenta a incompatibilidade desde o LiteLLM 1.101.0, confirma que versões novas mantêm a anotação e que Pydantic mais novo não remove o aviso; o projeto fixou LiteLLM em 1.100.0.
- `https://github.com/mcdonc/klangk/issues/3574` — mesmo warning quebrando CI com `filterwarnings = error`; opções registradas: ignore direcionado ou pin de versão.
- `https://github.com/BerriAI/litellm/pull/37949` — precedente upstream de suppress direcionado para outro TypedDict (`StandardLoggingRoutingDecision`).

## Risks / Trade-offs

- **Mudança de HTML da ANBIMA** → parser all-or-nothing falha e o cache anterior sustenta a carga; teste com fixture e log claro.
- **Calendário desatualizado no ano corrente** → TTL curto e atualização forçada na GUI/CLI.
- **Recesso local divergir da B3** → regra explícita, restrita a 24/12 e 31/12, com origem própria e configuração futura possível.
- **Lock dedicado vs. lock global** → evita bloquear cargas; se o lock do calendário estiver retido, a carga espera brevemente, tenta reler o cache e, sem cache, segue com fim de semana.
- **Marcador negativo confundido com cache válido** → estado derivado de `published`; teste dedicado garante `calendario_indisponivel` em toda leitura.
- **Remoção da lista estática quebra testes existentes** → atualizar testes para injetar um `BusinessDayLookup` com feriados conhecidos; não manter duas fontes.
- **Tools MCP novas ampliam o catálogo** → agrupar em `calendario_*`, preservar as oito `nav_*` e atualizar testes de listagem/ordenação.
- **Python 3.10** → usar `timezone.utc` em vez de `datetime.UTC` e evitar APIs 3.11+.
- **Superfície grande** → implementar em incrementos: núcleo → cargas → Hoje → CLI → MCP → GUI, com testes por incremento.

## Migration Plan

1. Recuperar e adaptar o núcleo copiado; adicionar testes unitários do parser/cache/serviço.
2. Introduzir a porta de dia útil e remover a lista estática; atualizar chamadas e testes.
3. Fiar `ensure_year` nas cargas e resolver a data de referência.
4. Corrigir o fuso local na GUI e nos defaults de “hoje”.
5. Adicionar CLI, MCP e aba GUI.
6. Atualizar documentação e executar `make lint`, `make complexity` e os testes impactados.

Rollback: reverter a change; o cache em `<cache_root>/calendar` é aditivo e pode ser removido sem afetar os demais caches.
