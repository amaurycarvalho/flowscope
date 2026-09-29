## 1. Pré-visualização de documentos fora da thread do Tk

- [ ] 1.1 Mover `_texto_cacheado` (leitura do store persistente), `_summary.precisa_resumo` e `_precisa_guidance` de `_iniciar_preview` para o worker `_trabalhar` em `document_flow_mixin.py`, publicando no `Resultado` o texto, se o resumo era necessário e o resumo gerado; verificar com teste headless (fake de `JobContext`) que nenhuma leitura de store ocorre na chamada de `_iniciar_preview`
- [ ] 1.2 Ajustar `_aplicar_preview`/exibição para receber o novo payload e aplicar texto/resumo na thread do Tk, preservando o estado de carregamento e o early-return de documento já resumido; verificar com teste que o texto e o `long_summary` aparecem compostos como antes
- [ ] 1.3 Converter os testes de preview/cache de texto do painel de documentos para headless (fakes de manager/`JobContext`), sem `@needs_display`, e confirmar a contagem de UI inalterada

## 2. Cópia de gráfico assíncrona

- [ ] 2.1 Separar em `infrastructure/clipboard_image.py` o `salvar_png(figure)` (rendering, thread do Tk) da `transferir_png(path)` (subprocess), mantendo `ClipboardPort.copy_image` intacto para os chamadores síncronos; verificar com testes de infraestrutura que cada parte é chamada na etapa esperada
- [ ] 2.2 Portar `ActionsMixin._copy_chart` em `app_actions.py` para salvar o PNG no Tk e submeter `transferir_png` a um `BackgroundManager` (grupo `"clipboard"`, `Politica.LATEST_WINS`), publicando sucesso/erro por eventos e mantendo `presenter.busy()`; verificar com teste headless que a thread do Tk não chama o subprocess
- [ ] 2.3 Cobrir feedback de status ("Gráfico copiado!") e falha de clipboard (`ClipboardError`) por eventos, com teste headless do despacho e verificação de que os controles são restaurados

## 3. Remontagem de notícias pelo término do job

- [ ] 3.1 Remover `_reagendar_remontagem` e `_LIMITE_REMONTAGEM` de `noticias_actions.py` e agendar `_remontar_noticias` com `after(0, ...)` a partir do `ao_termino` do job de aquisição; verificar com teste headless que nenhum `after` de polling é criado
- [ ] 3.2 Garantir a precedência da carga nova: `_remontar_noticias` só remonta quando não há job de aquisição ativo (`tem_ativo(GRUPO)`), com teste que inicia uma nova aquisição antes do término da cancelada e confirma que a árvore nova não é sobrescrita

## 4. Verificação final

- [ ] 4.1 Validar o change (`openspec validate descarregar-tk-io-restante`) e confirmar os deltas de `documentos-ticker-panel`, `clipboard-export` e `noticias-panel`
- [ ] 4.2 Rodar a suíte de aplicação e apresentação, `ruff`, flake8, complexidade (`xenon`/`radon`) e a checagem de fronteiras, confirmando ausência de novas violações
- [ ] 4.3 Confirmar que a contagem de `@needs_display` não aumentou (guardrail de teto de UI) e que nenhum teste novo exige `DISPLAY`
