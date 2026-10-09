## Why

A navegação da árvore de conhecimento do chat apresentou dois problemas em uso: ramos internos sem itens (`/flowscope/indicadores`, `/flowscope/abas`, `/fundamentos/valores`, ...) tornavam-se folhas vazias e devolviam `nao_interno` quando listados; e, sem backend vetorial, a LLM não tinha orientação para recorrer à busca determinística por regex, levando a listagens descontroladas de grupos grandes (ex.: `/noticias/Geral`), inflando o contexto sem responder à pergunta.

## What Changes

- Ramos internos sem itens são omitidos da árvore de conhecimento em vez de existirem como folhas vazias: `/flowscope/abas`, `/flowscope/indicadores`, `/fundamentos/tickers`, `/fundamentos/campos` e `/fundamentos/valores`.
- O mapa canônico e a descrição do manifesto passam a anunciar **apenas os ramos existentes** na árvore corrente (deixa de citar caminhos inexistentes).
- O protocolo/manifesto e o prompt de sistema passam a orientar a LLM a usar a busca determinística `buscar(caminho, regex, em=[...])` sempre que `buscar_semantico` responder `indice_indisponivel`, e a preferir o nó `indice`/`buscar` a listar grupos grandes inteiros.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities
- `llm-chat-tree`: o requisito de árvore cache-only passa a proibir nós internos vazios (ramos sem itens são omitidos); o requisito de manifesto passa a descrever apenas ramos existentes; o requisito do protocolo de navegação passa a orientar explicitamente o fallback para a busca determinística por regex e o uso do `indice`/`buscar` em ramos grandes.
- `llm-chat-context`: os ramos `/flowscope/abas`, `/flowscope/indicadores` e os sub-ramos de `/fundamentos` deixam de ser expostos quando não têm itens, em vez de aparecerem como folhas vazias.

## Impact

- **Aplicação**: `application/chat/arvore.py` (`ramo_flowscope`, `ramo_fundamentos`), `application/chat/manifesto.py` (mapa dinâmico e texto do protocolo), `application/chat/consultar.py` (`SYSTEM_PROMPT`).
- **Testes**: `tests/test_application/test_chat_arvore.py`, `test_chat_manifesto.py`, `test_chat_protocolo.py`, `test_chat_consulta.py`.
- Sem mudança de formato de cache, dependências ou persistência; convive com a change `documentos-arvore-ramos` (que adiciona os ramos `/guidance` e `/direitos-obrigacoes`).
