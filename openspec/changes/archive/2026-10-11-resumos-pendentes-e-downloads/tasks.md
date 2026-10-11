## 1. Pendência de texto conclusivamente ausente

- [x] 1.1 Extrair no serviço de resumo de aplicação a decisão "necessita de resumo" (resumo ausente/não íntegro E texto não conclusivamente ausente), reusando `resumo_integro` e `tem_texto`; verificar com testes unitários em `tests/test_application` cobrindo ausente, truncado, marcador de ausência e texto em branco.
- [x] 1.2 Resolver, no worker de leitura do catálogo de documentos, o conjunto de caminhos com ausência definitiva de texto (lendo o text store do ticker) e entregá-lo à thread do Tk; verificar com teste headless de `carregar_catalogo`/`aplicar_catalogo` sem `DISPLAY`.
- [x] 1.3 Ajustar `documentos_sem_resumo`/`resumir_habilitado` e o alvo do lote de documentos para excluir os caminhos sem texto conclusivo; verificar com testes de painel em `tests/test_presentation` (botão desabilitado quando só restam documentos sem texto).
- [x] 1.4 Ajustar a pendência de notícias (`pendentes_ordenados`) para excluir itens com ausência definitiva de texto e manter apontadores não resolvidos pendentes; verificar com testes em `tests/test_application` e `tests/test_presentation/test_noticias_panel.py`.

## 2. Regeneração de resumos truncados em Notícias

- [x] 2.1 Aplicar `resumo_integro` à lista de pendentes de notícias, tratando como desatualizado o `long_summary` sem pontuação final; verificar com teste unitário do predicado em `tests/test_application`.
- [x] 2.2 Garantir que o lote de notícias regera e regrava o resumo truncado, preservando a ordem determinista; verificar com teste de lote cobrindo resumo truncado e resumo íntegro.

## 3. Guidance acionável e falha de IA

- [x] 3.1 Registrar no serviço de guidance da sessão os RGs cuja tentativa de IA falhou e expor "pendência acionável" (entrada ausente ou `deterministico` sem falha registrada); verificar com testes em `tests/test_application/test_document_guidance.py`.
- [x] 3.2 Impedir que a cascata de IA descarte uma avaliação já obtida por falha em fonte posterior e propagar a falha para registro; verificar com testes em `tests/test_application/test_avaliar_guidance.py`.
- [x] 3.3 Propagar a falha de guidance ao desfecho do lote ("falha(s)") e reavaliar o botão sem manter a pendência acionável; verificar com testes de `app_resumos_actions`/`resumos_job`.
- [x] 3.4 Reabilitar o RG ao reconfigurar o provedor ou iniciar nova sessão; verificar com teste que a reconfiguração limpa o registro de falha.

## 4. Data de referência com hora

- [x] 4.1 Interpretar `DD/MM/AAAA HH:MM[:SS]` descartando a hora em helper de normalização de datas; verificar com testes unitários dos formatos com e sem hora e inválidos.
- [x] 4.2 Usar a data interpretada em `_data_documento` e `resolver_data_referencia` para estabilizar o caminho de cache; verificar que a mesma data gera o mesmo caminho entre execuções com testes em `tests/test_infrastructure`.

## 5. Registro de URLs baixadas com sucesso

- [x] 5.1 Criar o store JSON de URLs por escopo (ticker e global de notícias), com leitura tolerante a ausência/corrupção e gravação atômica, espelhando `content_hashes`; verificar com testes em `tests/test_infrastructure`.
- [x] 5.2 Consultar o registro antes do download e registrar a URL após sucesso em `_persistir_material_fact` (ações/BDRs) e no `persistir` de documentos relevantes (FIIs); verificar que uma URL já registrada não dispara nova requisição.
- [x] 5.3 Consultar e registrar URLs na aquisição de notícias antes de `baixar_noticia`; verificar reuso entre execuções com teste de aquisição.
- [x] 5.4 Atualizar a poda (`podar_documento`/`podar_noticia`) para remover a URL do registro quando o arquivo é removido; verificar com teste de housekeeping que a URL é liberada e as demais permanecem.

## 6. Verificação integrada

- [x] 6.1 Rodar `pytest` (marker padrão) e confirmar que a suíte passa, incluindo os novos testes headless.
- [x] 6.2 Rodar a verificação das specs: `openspec validate resumos-pendentes-e-downloads --strict`.
- [x] 6.3 Conferir manualmente no cache real que GGRC11/RBVA11/XPLG11/BBDC3 deixam de contar como pendentes sem texto e que CACR11 não mantém o botão por guidance com falha de IA.
