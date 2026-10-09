## Why

A sub-aba "Documentos" hoje apresenta a árvore como uma única cadeia ticker → ano → mês → categoria → arquivos, sem expor o guidance já avaliado nem reservar espaço para os direitos e obrigações do ativo. Ao mesmo tempo, a árvore de conhecimento da aba "Chat AI" não oferece navegação para o guidance, e o lote "Resumir pendentes" não remonta a árvore ao terminar, deixando-a desatualizada em relação aos resumos/guidance recém-gravados.

## What Changes

- A árvore da sub-aba "Documentos" passa a ter, sob o nome do ticker, três ramos: **Guidance**, **Documentos** e **Direitos e obrigações**.
- **Guidance** (somente FII, com base nos documentos `Relatorio`): sub-ramos ano e mês, com uma folha por guidance que possui valor em cache. Clicar na folha exibe o texto do guidance (`formatar_guidance`) e, em linha separada ao final, o rótulo curado do RG associado; duplo-clique salta para a folha do RG na ramificação Documentos. Clicar em Guidance/ano/mês exibe, no campo de texto, todos os guidances do ramo no mesmo formato Markdown dos demais agrupamentos. FII sem guidance exibe o ramo vazio.
- **Documentos** mantém a ramificação e o comportamento atuais.
- **Direitos e obrigações** introduz os sub-ramos "Direitos" (ativos) e "Obrigações" (passivos), vazios por enquanto, preenchidos por changes futuras.
- Ao entrar na sub-aba pela primeira vez na sessão (ou ao mudar o ticker), a árvore fica expandida apenas até o primeiro nível (os três ramos visíveis, recolhidos).
- A árvore de conhecimento da aba "Chat AI" ganha navegação para o guidance e para "Direitos e obrigações", com os caminhos canônicos refletidos no manifesto e na assinatura de estado.
- Após "Resumir pendentes", a árvore é remontada (sub-abas "Documentos" e "Notícias"), preservando o arquivo selecionado.

## Capabilities

### New Capabilities
- `direitos-obrigacoes`: ramos placeholder "Direitos" (ativos) e "Obrigações" (passivos) na árvore de documentos e na árvore de conhecimento do chat, vazios até changes futuras.

### Modified Capabilities
- `documentos-ticker-panel`: a árvore passa de cadeia única para três ramos (Guidance/Documentos/Direitos e obrigações), com expansão de primeiro nível, interações do ramo Guidance (texto, duplo-clique) e remontagem após o lote de resumos.
- `relatorio-gerencial-guidance`: as entradas do ledger com valor passam a ser expostas em modo somente-leitura para montar o ramo Guidance e a navegação do chat.
- `llm-chat-tree`: novos ramos `/guidance/...` e `/direitos-obrigacoes/...`, com atualização do mapa canônico, dos metadados e da assinatura de estado.
- `noticias-panel`: a árvore de notícias é remontada ao término de "Resumir pendentes".

## Impact

- **Apresentação**: `presentation/gui/charts/document_tree_view.py`, `document_grouping.py`, `document_tree_panel.py`, `document_flow_mixin.py` (índice reverso, expansão, reflexão de guidance), `app_actions.py` (leitura do ramo no worker), `app_resumos_actions.py` (remontagem pós-lote), `charts/noticias_panel.py`.
- **Aplicação**: `application/documentos/document_guidance.py` (leitura do ledger), `application/chat/montar.py` e novas fontes de ramo em `application/chat/`, `application/chat/manifesto.py` (mapa e assinatura).
- **Domínio/infra**: reuso de `JsonGuidanceStore.avaliacoes` (leitura) e do catálogo de documentos; sem novas dependências e sem mudança de formato de cache.
- **Coordenação**: convive com `guidance-preview-rg` (em finalização), que já alterou a pré-visualização e o botão do mesmo painel.
