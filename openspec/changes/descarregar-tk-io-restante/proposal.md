## Why

As fatias `background-job-manager`, `carga-principal-background`, `leituras-catalogo-background` e `cache-prompt-chat` moveram para o `BackgroundManager` o processamento pesado (carga, fundamentos, catálogos, notícias, evolução, resumo/preview de documentos e envio do chat). Restaram três pontos que ainda executam I/O ou espera na thread do Tk e que são migráveis para background: a leitura de cache e a avaliação de resumo/guidance **antes** de submeter a pré-visualização de documentos; o envio da figura ao clipboard por `subprocess` (`xclip`/PowerShell/osascript); e o laço de `after` que faz polling da thread de cancelamento das notícias. Cada um congela a interface por um intervalo perceptível em disco/rede lenta ou com muitos itens.

## What Changes

- A pré-visualização de documentos deixa de ler o cache de texto e de avaliar `precisa_resumo`/`precisa_guidance` na thread do Tk; a decisão e a leitura passam para o worker do job de preview, mantendo o estado de carregamento e a exibição do resumo já existentes.
- A cópia de gráfico para o clipboard deixa de bloquear a thread do Tk no `subprocess` de transferência; o rendering da figura permanece serializado com a thread do Tk e a transferência roda em background, com feedback de sucesso/erro na barra de status.
- A remontagem da árvore de notícias após cancelamento passa a ser disparada pelo término do job (evento do manager) em vez de um laço de `after` que consulta `thread.is_alive()` na thread do Tk.
- Não altera as portas `LLMPort`, `ClipboardPort` nem `DocumentTextStore`: a melhoria é de orquestração na apresentação.
- Fora de escopo: I/O curto de preferências/atalho (`save_preferences`, `_on_create_shortcut`) e spawn de aplicativos externos (`xdg-open`/`webbrowser`), por custo desprezível.

## Capabilities

### New Capabilities
<!-- Nenhuma: ajusta fluxos já definidos. -->

### Modified Capabilities
- `documentos-ticker-panel`: a pré-visualização textual lê o cache e avalia resumo/guidance fora da thread da interface, sem bloquear o Tk.
- `clipboard-export`: a transferência da imagem do gráfico para o clipboard do sistema ocorre fora da thread da interface, mantendo a responsividade.
- `noticias-panel`: a remontagem da árvore após cancelamento é dirigida pelo término do job, sem polling da thread de trabalho na thread do Tk.

## Impact

- `src/flowscope/presentation/gui/charts/document_flow_mixin.py`: mover `_texto_cacheado`/`precisa_resumo`/`_precisa_guidance` para o worker de `_trabalhar`, publicando o resultado do preview.
- `src/flowscope/presentation/gui/app_actions.py`: `_copy_chart` submete a transferência ao `BackgroundManager` e mantém o estado ocupado pela autoridade única.
- `src/flowscope/infrastructure/clipboard_image.py`: separar o rendering da figura (thread do Tk) da transferência ao clipboard (background), preservando a porta `ClipboardPort`.
- `src/flowscope/presentation/gui/noticias_actions.py`: remover `_reagendar_remontagem`/`_LIMITE_REMONTAGEM` e reagir ao término do job pelo `ao_termino` do manager.
- Testes: converter os cenários correspondentes para headless (fake de manager/JobContext), conforme `reduzir-testes-ui`; nenhum `@needs_display` novo.
- **Dependências**: `background-job-manager` (manager, eventos e token), `leituras-catalogo-background` (catálogo de notícias já em background), `reduzir-testes-ui` (estratégia de teste headless e orçamento de UI).
- Sem impacto em `domain` e `application`.
