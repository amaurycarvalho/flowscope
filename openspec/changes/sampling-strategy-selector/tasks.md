## 1. Domain — SamplingConfig e calendário

- [ ] 1.1 Criar `SamplingConfig` dataclass em `domain/value_objects.py` ou novo arquivo `domain/sampling.py` com campos `period_days: int` e `method: str`
- [ ] 1.2 Implementar `generate_dates(ref_date, config) → list[date]` em `infrastructure/b3/calendar.py` com dispatcher para cada método
- [ ] 1.3 Implementar `_fibonacci_dates(ref_date, period_days)` — gera offsets de Fibonacci até o limite do período
- [ ] 1.4 Implementar `_fibonacci_reverse_dates(ref_date, period_days)` — parte do offset máximo do período e recua com Fibonacci
- [ ] 1.5 Implementar `_fibonacci_double_dates(ref_date, period_days)` — mescla Fibonacci com complementos concentrados no início/fim
- [ ] 1.6 Implementar `_monte_carlo_dates(ref_date, period_days, count)` — data base, data limite + N aleatórios
- [ ] 1.7 Implementar `_all_dates(ref_date, period_days)` — todos os dias úteis do período
- [ ] 1.8 Manter função `fibonacci_dates(ref_date)` existente como compatibilidade (delegando para `generate_dates` com config default)

## 2. Infraestrutura — Cache e ajuste de datas

- [ ] 2.1 Adicionar método `CacheManager.find_nearest(date, max_deviation=7) → date | None` que busca a data mais próxima no cache dentro de ±7 dias
- [ ] 2.2 Implementar `resolve_date(d, ref_date, config, cache) → date | None` que aplica: ajuste local para próximo dia útil, depois busca no cache (se cache_only)
- [ ] 2.3 Aplicar deduplicação: `sorted(set(resolved_dates))` filtrando None
- [ ] 2.4 Adicionar parâmetro `cache_only: bool = False` ao `B3Client.fetch_file()` — quando True, retorna None em cache miss sem fazer download

## 3. Aplicação — Repository e ports

- [ ] 3.1 Atualizar `DataRepository.get_available_dates()` em `application/ports.py` para aceitar `SamplingConfig` opcional
- [ ] 3.2 Atualizar `B3DataRepository.get_available_dates()` em `infrastructure/b3/repository.py` para usar `generate_dates(ref_date, config)` e ajustar com cache
- [ ] 3.3 Atualizar `AnalyzeTickersUseCase.execute()` em `application/use_cases.py` para receber e propagar `SamplingConfig`

## 4. Apresentação — Comboboxes na GUI

- [ ] 4.1 Adicionar `ttk.Combobox` de período em `app.py._build_top_bar()` entre o botão Carregar e o botão Copiar CSV, com valores `["Últimos 30 dias", "Últimos 60 dias (cache)", "Últimos 90 dias (cache)"]`, estado `readonly`
- [ ] 4.2 Adicionar `ttk.Combobox` de amostragem entre o combo de período e o botão Copiar CSV, com valores `["Fibonacci", "Fibonacci reverso", "Fibonacci duplo", "Monte Carlos", "Monte Carlos duplo", "Todos os dias"]`, estado `readonly`
- [ ] 4.3 Adicionar tooltips fixos em cada combobox usando a classe `ToolTip` existente
- [ ] 4.4 Implementar atualização da barra de status com texto explicativo ao navegar nos comboboxes (bind `<<ComboboxSelected>>` e teclado)
- [ ] 4.5 Implementar recarga automática: no evento `<<ComboboxSelected>>`, verificar se `self._current_data` está populado e, se sim, chamar `self._controller.on_load_data()`

## 5. Apresentação — Controller e Presenter

- [ ] 5.1 Adicionar método `get_sampling_config() → SamplingConfig` no `FlowScopePresenter` que lê os valores atuais dos comboboxes
- [ ] 5.2 Atualizar `FlowScopeController.on_load_data()` para ler config do presenter e propagar para o use case
- [ ] 5.3 Atualizar `FlowScopeController.on_index_clicked()` para usar config atual dos combos

## 6. Apresentação — OperationGuard

- [ ] 6.1 Adicionar os dois comboboxes à lista de widgets em `_disable_all_buttons()` no `app.py`
- [ ] 6.2 Garantir que `_restore_all_buttons()` retorna os combos para o estado `"readonly"`

## 7. Testes

- [ ] 7.1 Testar `generate_dates()` para cada combinação período × método (pelo menos 30d para cada método)
- [ ] 7.2 Testar `CacheManager.find_nearest()` com cache populado, cache vazio, data exata, data aproximada
- [ ] 7.3 Testar `resolve_date()` com ajuste de dia útil e fallback de cache
- [ ] 7.4 Testar deduplicação de datas
- [ ] 7.5 Testar `B3Client.fetch_file(cache_only=True)` — deve retornar None em cache miss
- [ ] 7.6 Verificar que testes existentes continuam passando (comportamento default inalterado)

## 8. Verificação manual

- [ ] 8.1 Iniciar aplicação e verificar comboboxes visíveis e com valores default
- [ ] 8.2 Carregar dados com período=30 e Fibonacci (comportamento atual) — deve funcionar
- [ ] 8.3 Alternar período para 60 dias com dados carregados — deve recarregar automático
- [ ] 8.4 Alternar amostragem sem dados carregados — não deve ter ação
- [ ] 8.5 Verificar tooltips ao passar mouse nos combos
- [ ] 8.6 Verificar texto explicativo na statusbar ao navegar nos combos
- [ ] 8.7 Verificar que combos são desabilitados durante carga e restaurados após
- [ ] 8.8 Testar período > 30 sem cache — deve executar sem erro (apenas menos datas)
