## 1. Pré-visualização de documentos fora da thread do Tk

- [x] 1.1 Mover `_texto_cacheado` (leitura do store persistente), `_summary.precisa_resumo` e `_precisa_guidance` de `_iniciar_preview` para o worker `_trabalhar` em `document_flow_mixin.py`, publicando no `Resultado` o texto, se o resumo era necessário e o resumo gerado; verificar com teste headless (fake de `JobContext`) que nenhuma leitura de store ocorre na chamada de `_iniciar_preview`
- [x] 1.2 Ajustar `_aplicar_preview`/exibição para receber o novo payload e aplicar texto/resumo na thread do Tk, preservando o estado de carregamento e o early-return de documento já resumido; verificar com teste que o texto e o `long_summary` aparecem compostos como antes
- [x] 1.3 Converter os testes de preview/cache de texto do painel de documentos para headless (fakes de manager/`JobContext`), sem `@needs_display`, e confirmar a contagem de UI inalterada

## 2. Cópia de gráfico assíncrona

- [x] 2.1 Separar em `infrastructure/clipboard_image.py` o `salvar_png(figure)` (rendering, thread do Tk) da `transferir_png(path)` (subprocess), mantendo `ClipboardPort.copy_image` intacto para os chamadores síncronos; verificar com testes de infraestrutura que cada parte é chamada na etapa esperada
- [x] 2.2 Portar `ActionsMixin._copy_chart` em `app_actions.py` para salvar o PNG no Tk e submeter `transferir_png` a um `BackgroundManager` (grupo `"clipboard"`, `Politica.LATEST_WINS`), publicando sucesso/erro por eventos e mantendo `presenter.busy()`; verificar com teste headless que a thread do Tk não chama o subprocess
- [x] 2.3 Cobrir feedback de status ("Gráfico copiado!") e falha de clipboard (`ClipboardError`) por eventos, com teste headless do despacho e verificação de que os controles são restaurados

## 3. Remontagem de notícias pelo término do job

- [x] 3.1 Remover `_reagendar_remontagem` e `_LIMITE_REMONTAGEM` de `noticias_actions.py` e agendar `_remontar_noticias` com `after(0, ...)` a partir do `ao_termino` do job de aquisição; verificar com teste headless que nenhum `after` de polling é criado
- [x] 3.2 Garantir a precedência da carga nova: `_remontar_noticias` só remonta quando não há job de aquisição ativo (`tem_ativo(GRUPO)`), com teste que inicia uma nova aquisição antes do término da cancelada e confirma que a árvore nova não é sobrescrita

## 4. Verificação final

- [x] 4.1 Validar o change (`openspec validate descarregar-tk-io-restante`) e confirmar os deltas de `documentos-ticker-panel`, `clipboard-export` e `noticias-panel`
- [x] 4.2 Rodar a suíte de aplicação e apresentação, `ruff`, flake8, complexidade (`xenon`/`radon`) e a checagem de fronteiras, confirmando ausência de novas violações
- [x] 4.3 Confirmar que a contagem de `@needs_display` não aumentou (guardrail de teto de UI), que todos os testes `@needs_display` preexistentes ligados aos objetos modificados nessa change foram avaliados se podem tornar-se headless (devem ser transformados em headless se a avaliação mostrar ser possível) e que nenhum teste novo exige `DISPLAY`


## Nota de orçamento de UI (4.3)

A change não adiciona teste `@needs_display`. Foram avaliados os testes gated
ligados aos objetos modificados e convertidos para headless os que só exercitam
processamento:

- `test_document_tree_panel.py`: removidos os testes de preview/cache de texto
  (`test_selecao_de_arquivo_dispara_preview_cacheada`,
  `test_preview_sem_texto_exibe_mensagem`, `TestPreviewEmThread`) e o
  `TestGeracaoDeResumo`; a cobertura foi movida para
  `test_document_preview_flow.py` (manager/JobContext fakes, sem Tk).
- `test_document_guidance_flow.py`: `_trabalhar` atualizado ao novo payload.
- `test_copy_chart.py`: reescrito headless para o fluxo assíncrono.
- `test_noticias_panel.py::TestNoticiasActions`: headless com `after(0)` deferido.

Baseline `tests/architecture/ui_test_budget.txt` reduzido de 236 para 228 (o teto
só encolhe). Nenhum teste novo exige `DISPLAY`.
