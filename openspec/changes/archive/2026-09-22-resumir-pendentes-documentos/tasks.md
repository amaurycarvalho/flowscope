## 1. Geração estrita e fachada de documentos

- [x] 1.1 Adicionar `DocumentSummaryService.gerar_estrito(arquivo, texto)` que propaga `LLMError` e exceções inesperadas (mantendo `gerar` tolerante); verificar com teste de propagação de `LLMError` e de exceção inesperada
- [x] 1.2 Expor no `DocumentTreePanel` `documentos_sem_resumo()` (arquivos de `_itens` com `long_summary is None`, em ordem da árvore) e `preparar_texto(arquivo)` reutilizando o cache de texto e convertendo só em *miss*, sem tocar widgets; verificar com teste de *hit* (sem conversão) e *miss* (converte e grava)
- [x] 1.3 Expor `DocumentTreePanel.aplicar_resumo(arquivo, resumo)` que persiste/atualiza `_itens`/`_por_caminho` e, se o documento estiver selecionado, recompõe a pré-visualização; verificar com teste de atualização do catálogo e do campo quando selecionado

## 2. Botão "Resumir pendentes"

- [x] 2.1 Adicionar `_resumir_btn` ("Resumir pendentes") imediatamente após `_ia_btn`, com comando roteando para o `resumir_callback` injetado, e incluí-lo em `all_buttons()`; verificar com teste de ordem dos filhos da barra e do conteúdo de `all_buttons()`
- [x] 2.2 Implementar `refresh_resumir_button()` com estado derivado (`disponivel() and ha_pendentes`), chamado em `update()` e em `_restore_all_buttons` (ao lado de `refresh_open_button`); verificar com teste de habilitado com LLM e pendentes, desabilitado sem LLM, desabilitado sem pendentes e desabilitado/restaurado no bloqueio global
- [x] 2.3 Adicionar `on_saved` ao `LLMConfigDialog` (invocado após `save_llm_config`) e injetar o refresh do painel em `_abrir_config_llm`; verificar com teste de que salvar reavalia o botão
- [x] 2.4 Injetar `resumir_callback=getattr(self, "_resumir_documentos_pendentes", None)` no `DocumentTreePanel` em `app_tab_layout.py`; verificar com teste de wiring que o acionamento do botão chama o callback

## 3. Job de resumo em lote

- [x] 3.1 Criar `ResumosPendentesJob` (modelo de `DocumentosJob`) com thread + fila e mensagens de progresso, resultado, erro e término, executando a fase "Preparando textos" e a fase "Resumindo documentos"; verificar com teste de duas fases com progresso e de pulo de documentos sem `tem_texto`
- [x] 3.2 Garantir interrupção: capturar qualquer exceção por documento, publicar o erro com o arquivo e encerrar o job; verificar com teste de erro no meio do lote interrompe e publica o erro, sem processar os seguintes

## 4. Orquestração no app-layer

- [x] 4.1 Implementar `_resumir_documentos_pendentes` em `ActionsMixin` no padrão de `_adquirir_documentos`: guarda `_resumos_job is None`, snapshot dos pendentes, `presenter.enter()`, criação/início do job e início do poll; verificar com teste de reentrância (segundo acionamento ignorado) e do balanceamento de `enter`/`exit`
- [x] 4.2 Implementar o poll na thread do Tk traduzindo progresso em `ProgressReporter`/`on_progress`, aplicando resultados com `painel.aplicar_resumo`, interrompendo com `set_status("<documento>: <motivo>", "⚠")` e log em erro, exibindo desfecho `Resumos gerados: M de N (K sem texto).` no sucesso e descartando resultados quando o ticker apresentado mudou; verificar com testes de progresso, interrupção, desfecho e descarte por troca de ticker
- [x] 4.3 Corrigir a exibição do avanço: reter a fase apenas ao término (última unidade), drenando sem atraso durante o processamento, e incluir `current/total` no rótulo da barra de status; verificar com teste de drenagem sem atraso durante a fase, de retenção no término e de contagem no rótulo

> Nota de implementação (ver Decisão 3): o poll consome uma mensagem por callback (`after(0)` entre mensagens) para o Tk repintar; a fase é reportada no início (`advance(0)`) com o avanço `current/total` no rótulo e mantida visível por ao menos `_FASE_RESUMOS_MINIMA_S` (~0,4 s) mesmo quando instantânea — a retenção é aplicada ao término da fase, sem bloquear o avanço; exibe `Resumindo N documento(s)…` ao iniciar. O estado do botão é reavaliado quando o catálogo muda (`_atualizar_resumo`) e quando o lote encontra zero pendentes (ver Decisão 7).

## 5. Verificação final

- [x] 5.1 Rodar `make lint` e corrigir avisos introduzidos
- [x] 5.2 Rodar `make test` e garantir a cobertura mínima do projeto
- [x] 5.3 Validar a change com `openspec validate "resumir-pendentes-documentos"` e `openspec validate "resumir-pendentes-documentos" --strict`
