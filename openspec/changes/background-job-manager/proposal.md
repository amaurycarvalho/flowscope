## Why

A orquestração de processamento em background está duplicada em cinco implementações independentes (`FundamentalJob`, `DocumentosJob`, `NoticiasJob`, `ResumosPendentesJob` e as threads inline de preview, chat, config LLM e verificação de versão). Cada uma repete thread + fila + drenagem na thread do Tk + watchdog de inatividade, e cada cópia pode divergir — o bug de "fila não drenada no cancelamento" já nasceu dessa duplicação. Sem um componente único, mover os processamentos que ainda rodam na thread do Tk (carga principal, varreduras de catálogo) exigiria repetir o padrão ainda mais vezes.

## What Changes

- Introduz o `BackgroundManager` na camada de apresentação: submissão de trabalho assíncrono com políticas de agendamento (`latest_wins`, `serialize`, `parallel`), token de cancelamento **por job** e um único pump de drenagem na thread do Tk.
- Extrai um `JobContext` entregue ao worker para publicar progresso, resultado, erro e término sem tocar em widgets.
- Porta os quatro jobs existentes (`FundamentalJob`, `DocumentosJob`, `NoticiasJob`, `ResumosPendentesJob`) para o manager, removendo a coreografia duplicada de thread/fila/watchdog.
- Unifica under o mesmo manager as demais threads inline de background já existentes.
- Nenhuma mudança de comportamento observável: rótulos, mensagens, estados de botão e ordem de exibição permanecem idênticos.
- `OperationGuard` permanece como guarda de UI contra reentrada do mesmo clique; a semântica de supersede passa a ser do manager.

## Capabilities

### New Capabilities
- `background-jobs`: submissão, agendamento, ciclo de vida e cancelamento centralizados de processamentos assíncronos na camada de apresentação.

### Modified Capabilities
<!-- Nenhuma capacidade existente tem requisitos alterados nesta fatia: é refatoração sem mudança de comportamento observável. -->

## Impact

- Novo pacote `src/flowscope/presentation/gui/background/` (manager, scheduler, pump, job/context, eventos).
- `src/flowscope/presentation/gui/{fundamental,documentos,noticias,resumos}_job.py` passam a descrever apenas o trabalho e sua política, sem thread própria.
- `controller_fundamental.py`, `app_actions.py`, `noticias_actions.py`, `app_resumos_actions.py`, `charts/document_flow_mixin.py`, `chat/envio.py`, `llm/config_dialog.py`, `app_about_actions.py` passam a usar o manager.
- `presentation/gui/presenter.py`: a contabilização de estado ocupado passa a reagir a eventos do manager; token único dá lugar a tokens por job.
- Sem impacto em `domain`, `application` e `infrastructure`; `layer-boundaries` preservado (o pacote não importa `infrastructure`).
- Testes: novo teste de ciclo de vida de thread/queue do manager; testes de job adaptados; orçamento de testes de UI inalterado.
