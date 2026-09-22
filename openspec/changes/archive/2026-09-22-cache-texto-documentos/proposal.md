## Why

Ao ler um documento na sub-aba "Documentos", o texto é extraído novamente a cada sessão (`pypdf`/`BeautifulSoup` em `document_preview.py`) — só existe um cache em memória que se perde ao trocar de ticker ou fechar a aplicação. Além disso, documentos sem texto extraível ainda passam pelo texto substituto até a camada de exibição, sem uma marca persistente que impeça o resumo LLM e a extração de guidance de rodarem sobre conteúdo inexistente. Persistir o texto extraído por documento elimina a reconversão, dá uma fonte única de texto para as demais funcionalidades da sub-aba e permite curto-circuitar todo o processamento quando não há texto.

## What Changes

- Cache **persistente do texto extraído por documento** em `~/.cache/flowscope/document-texts/<TICKER>.json`, com escrita atômica e tolerância a arquivo ausente ou corrompido, no mesmo modelo de `document_summaries.py`. O payload é **apenas o texto original extraído** do documento (sem resumo nem análise), chaveado pelo caminho relativo à raiz de cache (`chave_documento`).
- A pré-visualização lê o texto do cache; a conversão (`pypdf`/`BeautifulSoup`) só ocorre em *miss*, e o resultado é gravado para os acessos seguintes. Sem invalidação por alteração do arquivo, igual aos resumos.
- Quando não houver texto extraível, o cache registra o marcador `Sem texto extraível para pré-visualização.` (o mesmo `SEM_TEXTO` já exibido), tratado por um predicado compartilhado `tem_texto()`.
- Sem texto extraível, **não** se gera resumo LLM, **não** se tenta extrair guidance e **não** se executa qualquer outro processamento do texto do documento. A abertura do documento ("Abrir documento", duplo clique, Enter) permanece disponível.
- Corrige a **barra de rolagem vertical** da árvore e do campo de texto da sub-aba "Documentos": hoje os `ttk.Scrollbar` existem mas não são mapeados porque o conteúdo é empacotado antes da barra e, quando o painel é mais estreito que a largura requisitada do conteúdo, a barra é espremida para fora. A barra passa a ser empacotada primeiro (ou por `grid` com pesos), tornando-se visível e funcional, inclusive com rolagem pela roda do mouse.
- Atualiza a change `fii-guidance-informacoes-adicionais` para consumir o texto do novo cache (em vez de reextrair) e para **não avaliar guidance quando não houver texto extraível**, declarando a dependência desta change.

## Capabilities

### New Capabilities
- `documento-texto-cache`: cache persistente, por documento, do texto original extraído (ou do marcador de ausência), com escrita atômica, tolerância a ausência/corrupção e leitura sem reconversão.

### Modified Capabilities
- `documentos-ticker-panel`: a "Pré-visualização textual" passa a ler o texto do cache e só converter em *miss*; a "Geração de resumo sob demanda" passa a ser suprimida quando não há texto extraível; e um novo requisito garante rolagem vertical visível e funcional na árvore e no campo de texto.

## Impact

- **Infraestrutura**: novo store de texto por ticker (modelo de `infrastructure/document_summaries.py`) e leitura/gravação atômicas via `_atomic_write_bytes`.
- **Aplicação**: porta do store de texto e predicado `tem_texto()` compartilhado, consumidos pela pré-visualização e, futuramente, pela avaliação de guidance.
- **Apresentação**: `charts/document_tree_panel.py` (cache no fluxo de seleção, guarda do resumo), `charts/document_preview.py` (`SEM_TEXTO`/`tem_texto`) e `charts/document_tree_view.py` + `_build_preview` (ordem de empacotamento da barra de rolagem).
- **Change dependente**: `fii-guidance-informacoes-adicionais` (proposta, design, spec e tarefas) passa a reconhecer o cache e a depender desta implementação.
- **Testes**: unitários do store (miss/hit/corrupção/marcador), do fluxo de cache no painel, da supressão de resumo/guidance sem texto e da presença/mapeamento da barra de rolagem (requer `DISPLAY`).

## Dependencies

- Depende de `centralizar-controle-cursor`: a extração/carregamento da pré-visualização roda em thread de trabalho e o novo fluxo de cache deve ser construído sobre a autoridade única de estado ocupado e o watchdog ali definidos, evitando um segundo mecanismo paralelo de cursor/estado. Implementar esta change após aquela.
- É pré-requisito de `fii-guidance-informacoes-adicionais`, que passa a ler o texto deste cache.
