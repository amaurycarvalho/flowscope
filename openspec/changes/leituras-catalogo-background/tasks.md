## 1. Leitura assíncrona do catálogo de documentos

- [ ] 1.1 Extrair `carregar_catalogo(ticker)` (worker-safe) e `aplicar_catalogo(ticker, catalogo)` (Tk) em `DocumentTreePanel`, com teste headless de `carregar_catalogo` e teste de `aplicar_catalogo` restrito a árvore/empty-state
- [ ] 1.2 Migrar `_update_documentos`/`_adquirir_documentos` em `app_actions.py` para submeter a leitura ao grupo `"documentos-leitura"` (`latest_wins`, `key` do ticker) e verificar com teste headless que a thread do Tk não é bloqueada
- [ ] 1.3 Exibir estado de carregamento durante a leitura e verificar cache frio resultando em estado vazio
- [ ] 1.4 Verificar que trocar de ticker descarta a leitura anterior com teste headless de leitura obsoleta

## 2. Leitura assíncrona do catálogo de notícias

- [ ] 2.1 Extrair `carregar_secoes()` (worker-safe) e `aplicar_secoes(catalogo)` (Tk) em `NoticiasPanel`, com teste headless de `carregar_secoes` e teste de `aplicar_secoes` restrito a árvore/empty-state
- [ ] 2.2 Migrar `_update_noticias`/`_remontar_noticias` para submeter a leitura ao grupo `"noticias-leitura"` e verificar interface responsiva com teste headless
- [ ] 2.3 Exibir estado de carregamento, preservar o estado vazio em cache frio e garantir que nenhuma requisição à B3 é feita na leitura
- [ ] 2.4 Verificar que uma nova leitura iniciada antes da anterior concluir prevalece, com teste headless de descarte de leitura obsoleta

## 3. Leitura assíncrona da evolução dos fundamentos

- [ ] 3.1 Extrair a montagem das séries (`store.datas`/`historico` + `montar_series`) para uma função de trabalho e aplicar o resultado por evento no painel, com teste headless da preparação das séries
- [ ] 3.2 Migrar `_update_fundamental_evolution` para o grupo `"evolucao"` com `latest_wins` por ticker e verificar interface responsiva
- [ ] 3.3 Exibir estado de carregamento e verificar que o resultado de um ticker anterior não é aplicado ao novo

## 4. Orçamento de testes de UI

- [ ] 4.1 Substituir testes UI de varredura/leitura por testes headless de `carregar_*`/preparação de séries e manter em UI apenas `aplicar_*`, estado de carregamento e empty-state
- [ ] 4.2 Confirmar que a contagem de `@needs_display` não aumentou em relação ao baseline registrado na fatia A

## 5. Verificação final

- [ ] 5.1 Atualizar os deltas de `documentos-ticker-panel`, `noticias-panel` e `fundamental-evolution-panel` e validar o change
- [ ] 5.2 Rodar os testes de painel/integração, teste de complexidade e a checagem de fronteiras, confirmando paridade de ordenação, empty-state e filtragem de entradas sem HTML
