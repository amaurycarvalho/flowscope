## Why

Hoje o resumo de um documento só é gerado sob demanda, ao selecionar cada arquivo individualmente e aguardar a chamada à LLM. Num ticker com dezenas de documentos, isso exige clicar e esperar documento a documento, sem visão do quanto falta nem do que falhou. Com `cache-texto-documentos` persistindo o texto e `centralizar-controle-cursor` concentrando a autoridade de estado ocupado, há base para processar todos os documentos pendentes do ticker em lote, com progresso e interrupção segura.

## What Changes

- Adicionar o botão **"Resumir pendentes"** na barra de controles da sub-aba "Documentos", imediatamente após o botão "I.A.". O botão fica sempre visível e é **habilitado apenas** quando a LLM está configurada, existe ao menos um documento do ticker apresentado sem `long_summary` e nenhum lote está em andamento; nos demais casos fica desabilitado (não oculto).
- Ao ser acionado, processar em background, em duas fases — **preparar o texto** (reutilizando o cache e convertendo apenas em *miss*) e **gerar o resumo** — todos os documentos do ticker apresentado sem `long_summary`, exatamente como se cada um tivesse sido selecionado. Os resumos gerados DEVEM ser persistidos e refletidos no catálogo em memória.
- Exibir o andamento na **barra de status com a barra de progresso**, uma fase por vez, e manter botões e cursor bloqueados pela autoridade única de estado ocupado durante todo o lote.
- **Interromper o lote em qualquer erro** e reportar na barra de status o documento e o motivo da falha, liberando os controles.
- Pular documentos sem texto extraível (`SEM_TEXTO`), sem chamar a LLM, contabilizando-os no desfecho.
- Reavaliar o estado do botão após salvar a configuração de I.A. e ao término do lote.

## Capabilities

### New Capabilities
<!-- Nenhuma nova capability. -->

### Modified Capabilities
- `documentos-ticker-panel`: novo requisito de botão "Resumir pendentes" e de processamento em lote dos documentos pendentes do ticker, com progresso, pulo de documentos sem texto e interrupção por erro.

## Impact

- **Apresentação**: `charts/document_tree_panel.py` (botão, exposição dos pendentes/texto, atualização do catálogo), `app_actions.py` (orquestração do lote no padrão de `_adquirir_documentos`), `app_tab_layout.py` (injeção do callback), `app_status.py` (restauração do botão) e `llm/config_dialog.py` (callback `on_saved`).
- **Job**: novo job de resumo em lote (fila + thread), análogo a `documentos_job.py`.
- **Aplicação/presenter**: uso da autoridade única de estado ocupado e do relatório de progresso existentes; modo estrito de geração que propaga o erro em vez de suprimi-lo.
- **Change dependente**: `cache-texto-documentos` fornece o texto em cache e o predicado `tem_texto`; `centralizar-controle-cursor` fornece `busy()`/`enter`/`exit` e o watchdog do job de documentos.
- **Testes**: unitários do job/fases, do estado do botão, da interrupção por erro, do pulo de documentos sem texto e do refresh após salvar a configuração.

## Dependencies

- Depende de `centralizar-controle-cursor`: o lote é uma operação longa e DEVE usar a autoridade única de estado ocupado e o padrão de watchdog ali definidos, sem criar um segundo mecanismo de cursor/estado. Implementar após aquela change.
- Depende de `cache-texto-documentos`: a fase de preparação lê/grava o texto pelo cache e usa `tem_texto` para decidir se resume. Implementar após aquela change.
