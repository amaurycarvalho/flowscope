## 1. Classificação no job de lote

- [ ] 1.1 Expor o motivo da extração (OK/PARCIAL/FALHA/PROTEGIDO/apontador não resolvido) em `_texto_utilizavel` e fazer `executar_resumos` devolver um resultado com os conjuntos de itens por motivo (além da contagem "sem texto"); verificar com testes em `tests/test_presentation/test_resumos_job.py`
- [ ] 1.2 Ajustar `_iniciar_lote_resumos`/`_finalizar_resumos_job` ao novo contrato de retorno, preservando o desfecho textual atual; verificar com os testes de `ResumosActionsMixin`

## 2. Nota de extração e texto definitivo

- [ ] 2.1 Implementar a regra pura de montagem da nota (parcial com quantidade de páginas, falha crítica, protegido) e verificar com teste unitário headless
- [ ] 2.2 Adicionar o gancho de finalização no mixin/painel que persiste o texto definitivo (`texto + nota` no parcial; só a nota na falha e no protegido) sem tocar em widgets; verificar com testes em `tests/test_presentation/test_document_flow.py`
- [ ] 2.3 Implementar o resumo determinístico para `FALHA` e `PROTEGIDO` terminando em pontuação final e verificar que `resumo_completo` o considera íntegro; verificar com teste unitário

## 3. Job de finalização definitiva

- [ ] 3.1 Implementar o job de finalização (background) que, por item, persiste o texto definitivo e gera/grava o resumo — LLM no `PARCIAL`, determinístico nos demais — e avalia guidance quando houver texto; verificar com teste do job/gerenciador
- [ ] 3.2 Refletir a finalização no painel de origem (remontagem/atualização dos itens) após o job; verificar com teste observável de que os itens saem dos pendentes e o botão é reavaliado

## 4. Confirmação e retry na sub-aba "Documentos"

- [ ] 4.1 Encadear a confirmação ao término normal do lote após a remontagem, com os dois diálogos (tentar novamente → marcar definitivo), em `_finalizar_resumos_job`; verificar headless com `messagebox` substituído
- [ ] 4.2 Implementar o reprocessamento apenas da lista com pré-coleta de senha dos `PROTEGIDO` na thread do Tk e mapa `{caminho: senha}` repassado ao lote; verificar com teste headless
- [ ] 4.3 Garantir que a confirmação não é exibida em cancelamento, interrupção por erro, cota da LLM ou troca de ticker; verificar com testes

## 5. Confirmação e retry na sub-aba "Notícias"

- [ ] 5.1 Estender o mesmo fluxo à sub-aba "Notícias", excluindo apontador não resolvido da lista e tratando o documento vinculado protegido via pré-coleta de senha; verificar com testes em `tests/test_presentation/test_noticias_panel.py`

## 6. Quality gate

- [ ] 6.1 Executar `make quality-gate` (lint, testes com cobertura >= 85%, complexidade, duplicação, mutação e semgrep) e corrigir as pendências introduzidas
