## 1. Domain — SamplingConfig e calendário

- [x] 1.1 Criar `SamplingConfig` dataclass em `domain/value_objects.py` ou novo arquivo `domain/sampling.py` com campos `period_days: int` e `method: str`
- [x] 1.2 Implementar `generate_dates(ref_date, config) → list[date]` em `infrastructure/b3/calendar.py` com dispatcher para cada método
- [x] 1.3 Implementar `_fibonacci_dates(ref_date, period_days)` — gera offsets de Fibonacci até o limite do período
- [x] 1.4 Implementar `_fibonacci_reverse_dates(ref_date, period_days)` — parte do offset máximo do período e recua com Fibonacci
- [x] 1.5 Implementar `_fibonacci_double_dates(ref_date, period_days)` — mescla Fibonacci com complementos concentrados no início/fim
- [x] 1.6 Implementar `_monte_carlo_dates(ref_date, period_days, count)` — data base, data limite + N aleatórios
- [x] 1.7 Implementar `_all_dates(ref_date, period_days)` — todos os dias úteis do período
- [x] 1.8 Manter função `fibonacci_dates(ref_date)` existente como compatibilidade (delegando para `generate_dates` com config default)

## 2. Infraestrutura — Cache e ajuste de datas

- [x] 2.1 Adicionar método `CacheManager.find_nearest(date, max_deviation=7) → date | None` que busca a data mais próxima no cache dentro de ±7 dias
- [x] 2.2 Implementar `resolve_dates(ref_date, config, cache) → list[date]` que aplica: ajuste local para próximo dia útil, depois busca no cache (se cache_only)
- [x] 2.3 Aplicar deduplicação: `sorted(set(resolved_dates))` filtrando None
- [x] 2.4 Adicionar parâmetro `cache_only: bool = False` ao `B3Client.fetch_file()` — quando True, retorna None em cache miss sem fazer download

## 3. Aplicação — Repository e ports

- [x] 3.1 Atualizar `DataRepository.get_available_dates()` em `application/ports.py` para aceitar `SamplingConfig` opcional
- [x] 3.2 Atualizar `B3DataRepository.get_available_dates()` em `infrastructure/b3/repository.py` para usar `generate_dates(ref_date, config)` e ajustar com cache
- [x] 3.3 Atualizar `AnalyzeTickersUseCase.execute()` em `application/use_cases.py` para receber e propagar `SamplingConfig`

## 4. Apresentação — Comboboxes na GUI

- [x] 4.1 Adicionar `ttk.Combobox` de período em `app.py._build_top_bar()` entre o botão Carregar e o botão Copiar CSV, com valores `["Últimos 30 dias", "Últimos 60 dias (cache)", "Últimos 90 dias (cache)"]`, estado `readonly`
- [x] 4.2 Adicionar `ttk.Combobox` de amostragem entre o combo de período e o botão Copiar CSV, com valores `["Fibonacci", "Fibonacci reverso", "Fibonacci duplo", "Monte Carlos", "Monte Carlos duplo", "Todos os dias"]`, estado `readonly`
- [x] 4.3 Adicionar tooltips fixos em cada combobox usando a classe `ToolTip` existente
- [x] 4.4 Implementar atualização da barra de status com texto explicativo ao selecionar itens nos comboboxes (bind `<<ComboboxSelected>>`)
- [x] 4.5 Implementar recarga automática: no evento `<<ComboboxSelected>>`, verificar se `self._current_data` está populado e, se sim, chamar `self._controller.on_load_data()`

## 5. Apresentação — Controller e Presenter

- [x] 5.1 Adicionar método `get_sampling_config() → SamplingConfig` no `FlowScopePresenter` que lê os valores atuais dos comboboxes
- [x] 5.2 Atualizar `FlowScopeController.on_load_data()` para ler config do presenter e propagar para o use case
- [x] 5.3 Atualizar `FlowScopeController.on_index_clicked()` para usar config atual dos combos

## 6. Apresentação — OperationGuard

- [x] 6.1 Adicionar os dois comboboxes à lista de widgets em `_disable_all_buttons()` no `app.py`
- [x] 6.2 Garantir que `_restore_all_buttons()` retorna os combos para o estado `"readonly"`

## 7. Testes

- [x] 7.1 Testar `generate_dates()` para cada combinação período × método (pelo menos 30d para cada método)
- [x] 7.2 Testar `CacheManager.find_nearest()` com cache populado, cache vazio, data exata, data aproximada
- [x] 7.3 Testar `resolve_dates()` com ajuste de dia útil e fallback de cache
- [x] 7.4 Testar deduplicação de datas
- [x] 7.5 Testar `B3Client.fetch_file(cache_only=True)` — deve retornar None em cache miss
- [x] 7.6 Verificar que testes existentes continuam passando (comportamento default inalterado)

## 8. Pós-resolução ticker-aware

- [x] 8.1 Implementar varredura d±1..d±7 em `AnalyzeTickersUseCase.execute()` para substituir datas sem trades de nenhum ticker analisado
- [x] 8.2 Mover `_engine.execute()` para depois da varredura de substituição, garantindo que indicadores sejam computados para todas as datas
- [x] 8.3 Propagar `_sampling_dates` no dict resultado do use case

## 9. Renomeação UI

- [x] 9.1 Renomear "Monte Carlos" → "Monte Carlo" nos labels do combobox, status labels e sampling_map

## 10. Verificação manual

- [ ] 10.1 Iniciar aplicação e verificar comboboxes visíveis e com valores default **(manual)**
- [ ] 10.2 Carregar dados com período=30 e Fibonacci (comportamento atual) — deve funcionar **(manual)**
- [ ] 10.3 Alternar período para 60 dias com dados carregados — deve recarregar automático **(manual)**
- [ ] 10.4 Alternar amostragem sem dados carregados — não deve ter ação **(manual)**
- [ ] 10.5 Verificar tooltips ao passar mouse nos combos **(manual)**
- [ ] 10.6 Verificar texto explicativo na statusbar ao navegar nos combos **(manual)**
- [ ] 10.7 Verificar que combos são desabilitados durante carga e restaurados após **(manual)**
- [ ] 10.8 Testar período > 30 sem cache — deve executar sem erro (apenas menos datas) **(manual)**
- [ ] 10.9 Verificar que CSV contém todas as datas de amostragem, incluindo linhas vazias para datas sem trade **(manual)**
- [ ] 10.10 Verificar que gráfico "Evolução da Dominância" exibe todas as datas de amostragem (sem datas faltando) **(manual)**
