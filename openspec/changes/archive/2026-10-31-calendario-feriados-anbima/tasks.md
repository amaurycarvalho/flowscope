# Tasks

## 1. Recuperar o núcleo do calendário

- [x] 1.1 Renomear os imports de `b3_selic_pre.*` para `flowscope.*` em `application/calendar/`, `infrastructure/calendar/` e `domain/calendar.py`; substituir `datetime.UTC` por `timezone.utc`, remover referências a `days_ago`/`EVOLUTION_DAYS` e remover `evolution_targets`; verificar com `.venv/bin/python -c "import flowscope.application.calendar, flowscope.infrastructure.calendar"`.
- [x] 1.2 Corrigir o caminho do cache para `<cache_root>/calendar`, trocar o lock copiado por `ActionLock(caminho=...)` com espera curta, reler o cache sob o lock antes de gravar e usar `_atomic_write_bytes`; verificar com testes de concorrência em `tests/test_infrastructure/test_calendar_cache.py`.
- [x] 1.3 Implementar/validar o parser ANBIMA all-or-nothing: normalização de data, acentos/entidades, dia da semana, origem individual e recesso local 24/12 e 31/12; separar `HolidayYearUnavailable` (404/página sem tabela) de `HolidaySourceError` (transporte/HTML inválido); adicionar fixture HTML real de 2026 e verificar com `.venv/bin/python -m pytest tests/test_infrastructure/test_calendar_parser.py -q`.
- [x] 1.4 Cobrir storage e cache por ano: TTL de ano passado/current/futuro, marcador negativo lido como `calendario_indisponivel`, corrupção, escrita atômica e leitura sem escrita; verificar com `.venv/bin/python -m pytest tests/test_infrastructure/test_calendar_cache.py -q`.
- [x] 1.5 Cobrir housekeeping `[ano-3, ano+1]` com referência no ano local corrente, preservação do ano da operação, arquivos corrompidos e remoção de anos antigos; verificar com `.venv/bin/python -m pytest tests/test_infrastructure/test_calendar_housekeeping.py -q`.
- [x] 1.6 Implementar no serviço de aplicação `ensure_year`, fallback defasado, `calendario_indisponivel`, cache negativo só para `HolidayYearUnavailable` em ano futuro, contenção de lock, `_today` em data local, resolução de bloco de feriados (inclusive virada do ano), `listar_ano`, `classificar` (com origem) e `exportar_ano` (CSV/JSON com origem por item); verificar com `.venv/bin/python -m pytest tests/test_application/test_calendar_service.py -q`.

## 2. Porta de dia útil e remoção da lista estática

- [x] 2.1 Definir a porta `BusinessDayLookup` na aplicação e um adaptador de infraestrutura que lê somente o cache; incluir implementação padrão “apenas fim de semana” para composições/testes sem calendário; verificar com um teste que o adaptador não cria nem altera arquivos.
- [x] 2.2 Remover `FERIADOS_NACIONAIS` e a lista estática de `domain/b3/calendario.py`, ajustando `domain/b3/__init__.py` e `infrastructure/b3/holidays.py`; verificar com `rg "FERIADOS_NACIONAIS" src tests` sem ocorrências de uso real.
- [x] 2.3 Injetar o lookup em `B3Client`, `B3DataRepository` e `AnalyzeTickersUseCase` (`_find_replacement_date`), mantendo o default de testes como fim de semana; verificar com `.venv/bin/python -m pytest tests/test_infrastructure/test_b3_client.py tests/test_infrastructure/test_b3_repository.py tests/test_application/test_use_cases_extended.py -q`.

## 3. Cargas e resolução da data de referência

- [x] 3.1 Garantir o calendário do ano da data de referência antes de resolver/consultar, de forma best-effort, e garantir também o ano anterior quando a referência estiver nos primeiros dias de janeiro; registrar falha em log sem bloquear a carga; verificar com testes de integração de falha da fonte e de virada do ano.
- [x] 3.2 Resolver a data de referência para o dia útil anterior quando necessário e passar a data resolvida para a amostragem, sem alterar o ajuste de amostragem para o próximo dia útil; verificar com testes de referência em sábado, domingo e feriado.
- [x] 3.3 Propagar o estado do calendário (`ok`, `defasado`, `calendario_indisponivel`) e os dados de resolução (`data_solicitada`, `data_resolvida`, `ajustada`, `motivo`, `feriado`, `origem`) no resultado/log; verificar com testes de serviço e de carga.

## 4. Fuso local na apresentação

- [x] 4.1 Trocar `datetime.now(timezone.utc).date()` por `date.today()` no botão “Hoje”, no fallback de referência e no `maxdate` do DateEntry em `app_actions.py`, `controller.py` e `app_layout.py`; verificar com teste que simula a virada do dia local.
- [x] 4.2 Alinhar `noticias_panel._hoje` e `cli_consultas._exportar_vwap` ao dia local; verificar com testes de apresentação/CLI que usam a data local.

## 5. CLI de feriados

- [x] 5.1 Adicionar `flowscope consultar feriados --ano <AAAA> [--saida]`, lendo apenas o cache e devolvendo JSON com metadados, estado e feriados; verificar com `.venv/bin/python -m pytest tests/test_presentation/test_cli_calendar.py -q`.
- [x] 5.2 Adicionar `flowscope exportar feriados --ano <AAAA> --formato csv|json [--saida]`, com CSV `;`/ISO e impressão em `stdout` sem `--saida`; verificar com testes de formato e de ausência de gravação.
- [x] 5.3 Adicionar `flowscope atualizar feriados [--ano]...`, com revalidação forçada, housekeeping, JSON por ano e código de saída 1 quando o ano ficar indisponível; verificar com `.venv/bin/python -m pytest tests/test_presentation/test_cli_acoes.py -q` (ou arquivo equivalente).

## 6. MCP de feriados

- [x] 6.1 Adicionar `calendario_listar` (`ano` inteiro), `calendario_classificar` (`data` ISO) e `calendario_exportar` (`ano` inteiro e `formato` enum `csv|json`) ao catálogo MCP, com `title`, anotações e schemas estritos; verificar que as oito `nav_*` continuam presentes e que a listagem segue ordem alfabética.
- [x] 6.2 Garantir que as tools `calendario_*` leem somente o cache, não consultam a ANBIMA, não gravam arquivos e devolvem `calendario_indisponivel` sem cache; verificar com testes de `tools/call` e de ausência de chamadas HTTP.
- [x] 6.3 Garantir que exportação MCP devolve CSV/JSON como conteúdo estruturado e que nenhum arquivo é criado/alterado/removido; verificar com teste em `tmp_path`.

## 7. Aba `Feriados` na GUI

- [x] 7.1 Extrair um modelo puro de árvore ano/mês/dia (anos decrescentes, meses/dias crescentes, folha `DD (seg)`) testável sem Tk; verificar com `.venv/bin/python -m pytest tests/test_presentation/test_feriados_tree_model.py -q`.
- [x] 7.2 Criar a aba `Feriados` de nível superior, com `ttk.Treeview` à esquerda e `ReadonlyText` à direita, montada apenas do cache, com estado vazio orientando a atualizar, roteamento próprio de aba (sem `_TICKER`/sub-aba) e entrada em `TAB_CONTENT` para o `OrientationPanel`; verificar com teste de wiring sem rede.
- [x] 7.3 Implementar seleção ano/mês/dia atualizando o textbox, com dia da semana abreviado e texto somente leitura; verificar com testes de modelo/eventos.
- [x] 7.4 Implementar o botão de atualização com `view-refresh`/`content-loading`, desabilitação durante a operação, revalidação dos anos exibidos (ou ano corrente se vazio), preservação de seleção e manutenção do conteúdo em caso de falha; verificar com testes de estado do botão e de reconstrução da árvore.

## 8. Documentação e verificação final

- [x] 8.1 Atualizar `docs/misc/datasources.md` com a fonte ANBIMA, URL, cache, TTL, fallback, recesso local, origem por feriado e estados; verificar que os comandos e caminhos documentados correspondem ao código.
- [x] 8.2 Atualizar `docs/misc/panels.md` e, se necessário, `README.md`/`docs/misc/mcp.md` com a aba `Feriados`, os comandos CLI e as tools MCP; verificar que os exemplos executam como escritos.
- [x] 8.3 Executar `make lint`, `make complexity` e os testes relacionados/impactados pela change; corrigir falhas antes de finalizar.
- [x] 8.4 (Manual, usuário) Executar a suíte completa `make test` e o quality gate `make quality-gate` apenas se desejar a verificação ampla; não faz parte da execução automática do agente.

## Workflow follow-up

- Arquivar a change após a implementação e a revisão do projeto.
- Verificar o resultado arquivado e atualizar o changelog quando aplicável.
- Acompanhar `BerriAI/litellm#44178`; quando o PR for mergeado e publicado, atualizar o LiteLLM e remover o aviso de `ChatCompletionReasoningItem`/`ReadOnly`. Evidências e decisão de não filtrar estão em `design.md`.
- Avaliar mover a resolução de referência de `on_atualizar_fundamentos` para o job em background, eliminando o possível bloqueio da interface quando não há cache.
