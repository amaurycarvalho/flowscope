## 1. Estado derivado e wiring

- [x] 1.1 Adicionar o parâmetro opcional `resumir_ativo_callback: Callable[[], bool] | None` ao `DocumentTreePanel.__init__` e armazená-lo; verificar com teste de construção do painel sem o callback (padrão `None`)
- [x] 1.2 Incorporar a condição de lote ativo em `refresh_resumir_button()`, tratando callback ausente como inativo; verificar com teste de botão desabilitado com LLM e pendentes quando o predicado é `True`, e de comportamento atual preservado quando o callback é `None`
- [x] 1.3 Adicionar `_resumos_em_andamento()` em `ResumosActionsMixin` retornando `_resumos_job is not None`; verificar com teste unitário do predicado com e sem job
- [x] 1.4 Injetar `resumir_ativo_callback=getattr(self, "_resumos_em_andamento", None)` na construção do `DocumentTreePanel` em `app_tab_layout.py`; verificar com teste de wiring que o callback é passado ao painel

## 2. Cobertura dos cenários

- [x] 2.1 Testar que, com o lote ativo (predicado `True`), `aplicar_resumo` de um documento não reabilita o botão; verificar via `tests/test_presentation/test_document_tree_panel.py`
- [x] 2.2 Testar que, com o lote ativo, `update()` do painel mantém o botão desabilitado mesmo havendo pendentes; verificar via `tests/test_presentation/test_document_tree_panel.py`
- [x] 2.3 Testar no host de teste do mixin que, com `_resumos_job` ativo, o refresh permanece desabilitado e que, após finalizar com pendentes, o botão reabilita; verificar via `tests/test_presentation/test_document_tree_panel.py`
- [x] 2.4 Testar no host de teste do mixin que, ao finalizar o lote sem pendentes remanescentes, o botão permanece desabilitado; verificar via `tests/test_presentation/test_document_tree_panel.py`

## 3. Verificação final

- [x] 3.1 Executar `ruff check` e a suíte `pytest` relevante (`tests/test_presentation`) e confirmar que passam
