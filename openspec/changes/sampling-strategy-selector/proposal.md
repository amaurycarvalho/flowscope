## Why

Atualmente o sistema sempre carrega exatamente 7 datas usando offsets fixos de Fibonacci (d-1, d-2, d-3, d-5, d-8, d-13, d-21), sem dar ao usuário controle sobre o período analisado ou o método de amostragem. Isso limita a flexibilidade da análise — o usuário pode querer janelas maiores (60/90 dias) para visão histórica mais ampla, ou diferentes estratégias de amostragem (Monte Carlo, Fibonacci reverso, todos os dias) para testar hipóteses distintas sobre o comportamento dos ativos.

## What Changes

- Adicionar dois comboboxes `ttk.Combobox` na barra superior, ao lado do botão "Copiar dados CSV":
  - **Período**: "Últimos 30 dias" (default), "Últimos 60 dias (cache)", "Últimos 90 dias (cache)"
  - **Amostragem**: "Fibonacci" (default), "Fibonacci reverso", "Fibonacci duplo", "Monte Carlos", "Monte Carlos duplo", "Todos os dias"
- Modificar a barra de status para exibir texto explicativo do item selecionado ao percorrer o combobox (sem recarregar dados)
- Tooltip único e fixo em cada combobox com explicação geral do controle
- Modificar `calendar.py` com novas funções de geração de datas para cada combinação período × amostragem
- Modificar `DataRepository.get_available_dates()` para receber os parâmetros de período e amostragem
- Modificar `B3Client.fetch_file()` para aceitar modo `cache_only` — quando período > 30, apenas dados em cache são usados (sem download B3)
- Ajustar cada data de amostragem para o próximo dia útil disponível no cache (aproximação local, sem cascata); pular datas sem cache nas proximidades (±7 dias), evitando duplicatas
- Modificar `AnalyzeTickersUseCase.execute()` para receber config de período/amostragem e propagar ao repositório
- Incluir os dois comboboxes no `OperationGuard` (desabilitar durante carga/processamento)
- Se dados já estiverem carregados e o usuário mudar um combo, recarregar automaticamente
- Se nenhum dado estiver carregado, mudar combos não tem efeito

## Capabilities

### New Capabilities
- `sampling-strategy`: Configuração de período (30/60/90 dias) e método de amostragem (Fibonacci, Fibonacci reverso, Fibonacci duplo, Monte Carlos, Monte Carlos duplo, Todos os dias) para seleção de datas históricas

### Modified Capabilities
- `data-ingestion`: A janela temporal com offsets de Fibonacci passa a ser parametrizável por período e estratégia de amostragem; período > 30 dias opera apenas com cache
- `gui-interface`: Dois novos comboboxes na barra superior para seleção de período e amostragem, com tooltips fixos e texto explicativo dinâmico na barra de status
- `loading-state-management`: Os dois novos comboboxes devem ser desabilitados/habilitados junto com os demais controles durante operações de carga e processamento

- **Target**: Release 0.6.0

## Impact

- `infrastructure/b3/calendar.py`: Novas funções de geração de datas para cada estratégia de amostragem
- `infrastructure/b3/repository.py`: `get_available_dates()` recebe parâmetros de config; `fetch_trades()` ou `B3Client` propaga `cache_only`
- `infrastructure/b3/client.py`: `fetch_file()` aceita `cache_only` opcional
- `infrastructure/cache.py`: Método auxiliar para buscar data mais próxima no cache (±7 dias)
- `application/ports.py`: `DataRepository.get_available_dates()` altera assinatura
- `application/use_cases.py`: `AnalyzeTickersUseCase.execute()` recebe config de sampling
- `presentation/gui/app.py`: Dois novos `ttk.Combobox` na barra superior, lógica de recarga automática, inclusão no `_disable_all_buttons`/`_restore_all_buttons`
- `presentation/gui/controller.py`: Propaga config de sampling para o use case
- `presentation/gui/presenter.py`: Expõe métodos para ler config dos combos e atualizar statusbar
- Nenhuma nova dependência externa
