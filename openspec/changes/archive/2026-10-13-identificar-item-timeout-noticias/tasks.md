## 1. Diagnóstico do item no watchdog

- [x] 1.1 Adicionar o campo `descricao: str = ""` a `JobHandle` (`src/flowscope/presentation/gui/background/job.py`) e verificar com teste unitário que um handle recém-criado tem descrição vazia
- [x] 1.2 Adicionar `JobContext.descrever(descricao)` (`src/flowscope/presentation/gui/background/context.py`) que grava `handle.descricao` sem atualizar `ultima_atividade`, e verificar com teste que descrever não impede o encerramento por inatividade
- [x] 1.3 Incluir `handle.descricao` nos avisos de `_aplicar_watchdog` (`manager.py`) nos dois ramos (inatividade e thread morta sem término), omitindo quando vazia, e verificar estendendo `test_inatividade_entrega_termino_e_loga` para exigir a descrição no log
- [x] 1.4 Marcar o item corrente com `ctx.descrever(...)` em `resumos_job._preparar_textos` (antes de `preparar_texto`) e em `_resumir` (antes de `gerar_resumo_do_lote`), e em `finalizacao_job.executar_finalizacao` por item, e verificar com teste que o `JobContext` recebe a descrição `ticker/nome`
- [x] 1.5 Marcar o item corrente na pré-visualização individual (`document_flow_mixin._trabalhar`) antes da extração, e verificar com teste que o job de preview descreve o arquivo

## 2. Extração orçada de PDF a partir de bytes

- [x] 2.1 Adicionar `extrair_pdf_com_orcamento(dados, senha=None, *, timeout=EXTRACAO_TIMEOUT_S)` e o alvo de processo filho que recebe `bytes` em `src/flowscope/application/extracao_orcada.py`, reusando `_consumir`/`_Acumulado`/`_finalizar`/`_configurar_log_pypdf`, e verificar com teste que um PDF em memória dentro do orçamento retorna o texto completo
- [x] 2.2 Verificar com testes que o estouro do orçamento retorna `PARCIAL` (com texto) ou `FALHA` (sem texto), nunca `SEM_TEXTO`, e que um PDF em memória protegido retorna `PROTEGIDO` (`tests/test_application/test_extracao_orcada.py`)
- [x] 2.3 Verificar com teste que o orçamento do worker de bytes permanece abaixo de `LIMITE_INATIVIDADE_S`, como no caminho por arquivo

## 3. Orçamento da resolução do documento vinculado

- [x] 3.1 Adicionar o parâmetro opcional `timeout_total` a `baixar_conteudo_vinculado` e derivar um deadline compartilhado, aplicando o restante a cada requisição em `_obter`/`_post_exibir_pdf` (incluindo o segundo GET do FNET e o POST do CVM), abortando quando o restante esgotar (`src/flowscope/infrastructure/b3/noticias_vinculo.py`)
- [x] 3.2 Fazer `_texto_do_documento` parsear o PDF baixado com `extrair_pdf_com_orcamento` usando o restante do deadline, mantendo o parse de HTML sem orçamento
- [x] 3.3 Verificar com testes em `tests/test_infrastructure/test_regulacao/test_noticias_vinculo.py` que, sem `timeout_total`, o comportamento atual é preservado, e que, com orçamento esgotado, a resolução retorna `None` dentro do prazo sem propagar exceção
- [x] 3.4 Em `NoticiasPanel._texto_do_arquivo` (`src/flowscope/presentation/gui/charts/noticias_panel.py`), calcular o deadline a partir de `timeout_extracao()` e repassá-lo como `timeout_total` ao resolvedor, atualizando o contrato/tipo de injeção e os dublês de teste
- [x] 3.5 Registrar `WARNING` nomeando a notícia (`ticker/nome`) quando, após a tentativa de resolução, o corpo permanece um apontador não resolvido, e verificar com teste em `tests/test_presentation/test_noticias_panel.py` que a notícia é nomeada no log

## 4. Verificação

- [x] 4.1 Rodar `make lint` e confirmar que não há erros
- [x] 4.2 Rodar `make complexity` e confirmar que os limites são respeitados
- [x] 4.3 Rodar os testes impactados (`tests/test_presentation/test_background_manager.py`, `tests/test_presentation/test_noticias_panel.py`, `tests/test_presentation/test_resumos_job.py`, `tests/test_infrastructure/test_regulacao/test_noticias_vinculo.py`, `tests/test_application/test_extracao_orcada.py`) e confirmar que passam
- [x] 4.4 (Usuário, se necessário) Rodar a suíte completa com `make test` apenas se a mudança se mostrar ampla; executar como task manual do usuário
