## Context

Ver `proposal.md - Why`. O estado atual que molda o desenho:

- A barra do painel é montada em `DocumentTreePanel._build_toolbar` (`document_tree_panel.py:97`) com `Atualizar`, `Abrir documento` e `I.A.`; `all_buttons()` (`:174`) alimenta o bloqueio global (`app_status.py:101`) e `refresh_open_button()` é reavaliado em `_restore_all_buttons` (`app_status.py:123`).
- A geração de resumo por seleção é `_iniciar_preview` → thread `_trabalhar` → `DocumentSummaryService.gerar` + `persistir` (`document_tree_panel.py:282-354`, `document_summary.py:93`). `gerar` **suprime** `LLMError` e devolve `None` — comportamento correto para a seleção, incompatível com "interromper no erro".
- `DocumentSummaryService.disponivel()` (`document_summary.py:57`) é "LLM configurada"; o `LLMConfigDialog._salvar` (`config_dialog.py:205`) grava e destrói sem notificar o painel.
- O padrão de operação longa em background já existe: `_adquirir_documentos` + `_poll_documentos_job` (`app_actions.py:166-210`) usam `presenter.on_operation_started/finished` e `on_progress`; `ProgressReporter` (`progress.py`) já suporta fases ponderadas e é usado em `controller_data.py:32`.
- `cache-texto-documentos` passa a persistir o texto por documento e a expor `tem_texto`; `centralizar-controle-cursor` passa a expor a autoridade única de estado ocupado (`busy()`/`enter`/`exit`) e o watchdog do job de documentos.
- A view de progresso mostra o percentual **da fase local** (`app_status.py:33`), comportamento já usado na carga de dados (barra reinicia entre fases).

## Goals / Non-Goals

**Goals:**
- Processar em lote os documentos pendentes do ticker exibido, reusando o mesmo caminho de texto/resumo da seleção.
- Exibir progresso em duas fases e interromper em qualquer erro, reportando documento e motivo.
- Manter o botão sempre visível com estado derivado (habilitado/desabilitado), reavaliado após salvar a configuração de I.A. e ao término do lote.
- Reusar a autoridade única de estado ocupado e o padrão de job/watchdog existentes.

**Non-Goals:**
- Processar documentos de outros tickers (varredura global do cache).
- Alterar o formato/limites do resumo, o comportamento da seleção individual ou a abertura de documentos.
- Gerar resumos com concorrência (o rate limiter já faz o *pacing*); a ordem é sequencial.
- Invalidar o cache de texto (decisão herdada de `cache-texto-documentos`).

## Decisions

### 1. Escopo: apenas o ticker apresentado

O lote opera sobre o snapshot dos arquivos do `_catalogo_atual` (via `_itens.values()`), na ordem da árvore (mais recente primeiro), sem varredura global.

- **Por quê:** o painel só conhece o catálogo corrente; a sub-aba é por ticker; evita descobrir tickers nas raízes de cache.
- **Alternativas:** varrer todos os tickers com documentos (rejeitado: exige índice global e total de progresso agregado, sem ganho para o pedido).

### 2. Orquestração no app-layer, no padrão de `_adquirir_documentos`

O painel dispara o lote por um callback injetado (`resumir_callback`, como `ia_callback`/`acquire_callback`). O `ActionsMixin` conduz: guarda de reentrância (`_resumos_job is None`), snapshot dos pendentes, `presenter.enter()`, criação/início do job e poll da fila na thread do Tk.

- **Por quê:** o `presenter` vive no app-layer; o bloqueio/cursor/progresso são política do presenter. O painel não deve conhecer a view global.
- **Alternativas:** painel autônomo com thread própria (rejeitado: duplicaria a política de cursor/estado e o tratamento de progresso).

### 3. Job de lote em duas fases com `ProgressReporter`

Novo `ResumosPendentesJob` (modelo de `DocumentosJob`) recebe o snapshot de arquivos e uma fachada de documentos do painel, roda em thread e publica na fila: progresso, resultado por documento, erro e término.

- Fase 1 — **"Preparando textos"** (`total = N`): para cada arquivo, obtém o texto pelo cache (conversão só em *miss*), gravando o resultado.
- Fase 2 — **"Resumindo documentos"** (`total = M`, apenas os com `tem_texto`): gera o resumo e persiste.
- O app-layer cria um `ProgressReporter(on_update=presenter.on_progress)` e traduz as mensagens da fila em `start_phase`/`advance`/`finish_phase`.

- **Por quê:** atende "duas fases" com o relator já existente e o mesmo padrão de progresso da carga de dados. O job mantém os textos preparados em memória para a fase 2, sem tocar widgets.
- **Alternativas:** fase única com conversão+resumo por documento (rejeitado: o pedido é explícito em duas fases); usar `DocumentosJob` (rejeitado: mensagens e semântica diferentes).

### 4. Modo estrito de geração que propaga o erro

Adicionar `DocumentSummaryService.gerar_estrito(arquivo, texto)` que chama o `ResumirDocumentoUseCase` e **propaga** `LLMError` (e exceções inesperadas), mantendo `gerar` tolerante para a seleção individual.

- **Por quê:** "qualquer erro interrompe" só é implementável se o erro chegar ao job. `gerar` hoje o suprime (`document_summary.py:103`).
- **Alternativas:** parâmetro `propagar` em `gerar` (rejeitado: sinaliza mal a diferença de contrato entre os dois usos).

### 5. Estado ocupado pela autoridade única

O app-layer chama `presenter.enter()` ao iniciar o job e `presenter.exit()` no término — sucesso, erro ou troca de ticker — sempre no caminho de poll. Não há cursor local no painel.

- **Por quê:** o job é assíncrono, então não segura o `with presenter.busy()`; `enter`/`exit` são a base do context manager definido em `centralizar-controle-cursor`. Isso preserva o balanceamento e o watchdog.
- **Alternativas:** cursor/flag próprios no painel (rejeitado: reintroduz o vazamento que aquela change elimina).

### 6. Interrupção por erro e desfecho

O job captura qualquer exceção por documento, publica `(erro, arquivo, exceção)` e encerra. O poll registra em log, exibe `Resumos interrompidos em <nome>: <motivo>` com ícone de aviso e chama `presenter.exit()`. No sucesso, exibe `Resumos gerados: M de N (K sem texto).` e um flash.

- **Por quê:** atende "reportar qual foi o erro" sem prosseguir com a LLM indisponível; a mensagem cita o documento.
- **Alternativas:** continuar nos erros de provedor por documento (rejeitado: o pedido é interromper em qualquer erro).

### 7. Estado do botão derivado e reavaliado

O botão é sempre visível. `DocumentTreePanel.refresh_resumir_button()` calcula `habilitado = _summary.disponivel() and ha_pendentes`; `all_buttons()` passa a incluir o botão (o bloqueio global cobre o "durante o lote/carga") e `_restore_all_buttons` chama `refresh_resumir_button()` ao lado de `refresh_open_button()`. O `LLMConfigDialog` ganha `on_saved` e `_abrir_config_llm` injeta o refresh.

- **Por quê:** segue o padrão do botão "Abrir documento" e atende "desabilitar em vez de esconder" e a reavaliação após salvar.
- **Alternativas:** esconder quando a LLM não está configurada (rejeitado pela decisão do usuário); recalcular só na troca de aba (rejeitado: o botão não refletiria o salvamento imediato).

### 8. Aplicação dos resultados na thread do Tk e descarte por ticker

A thread de trabalho não toca widgets: publica na fila. O poll chama `painel.aplicar_resumo(arquivo, resumo)` (atualiza `_itens`/`_por_caminho` e, se o documento estiver selecionado, recompõe a pré-visualização) e descarta resultados quando o ticker apresentado mudou.

- **Por quê:** mantém a thread-safety e evita que o lote de um ticker contamine outro; espelha `_aplicar_preview`/`_atualizar_resumo`.
- **Alternativas:** aplicar direto no worker (rejeitado: mutação de estado da UI fora da thread do Tk).

## Risks / Trade-offs

- **[Barra reinicia entre fases]** → comportamento já existente na carga de dados; aceito por consistência. Se incomodar, o `ProgressReporter` poderia reportar o percentual global, mas isso é fora do escopo.
- **[Lote longo com muitos documentos]** → o rate limiter limita o RPM e o progresso mantém o usuário informado; o watchdog herdado de `centralizar-controle-cursor` cobre travamento.
- **[Erro em um documento aborta todo o lote]** → decisão explícita do usuário; o desfecho indica o documento e o motivo, permitindo reexecutar após corrigir.
- **[Conversão de texto grande na fase 1]** → reutiliza o cache de `cache-texto-documentos`; só converte em *miss*.
- **[Sobreposição com a seleção individual]** → o bloqueio global desabilita a barra durante o lote, mas a seleção na árvore continua possível; um resumo coincidente pode ser gerado duas vezes. Aceito (idempotente: o último `persistir` vence).
- **[Troca de ticker no meio do lote]** → resultados descartados por comparação do ticker; o job termina e libera os controles.

## Migration Plan

- Aditivo: novo botão e novo job; nenhum dado migrado. O botão inicia desabilitado quando não há LLM configurada ou pendentes.
- Rollback: remover o botão/callback, o job e o modo estrito; a geração sob demanda permanece intacta.

## Open Questions

- Nenhuma.
