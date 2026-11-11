# Proposal

## Why

Hoje a aba "Chat AI" concatena a lista de fontes consultadas no corpo de cada resposta exibida, e o prompt de sistema ainda instrui a LLM a citar as fontes dentro do texto. Isso polui a leitura e faz a apresentação das fontes depender de como cada agente de IA formata a resposta. Separar, no payload do chat, pergunta, resposta e fontes — com as fontes ancoradas nos caminhos reais da árvore de conhecimento — padroniza o contrato entre agentes e permite controlar a exibição na tela.

## What Changes

- O JSON de resposta do protocolo de navegação passa a aceitar um campo opcional `fontes`, com entradas `{caminho, rotulo}`, declaradas pela LLM no turno final.
- A LLM deixa de ser instruída a citar fontes no corpo de `resposta`; as fontes passam a ser declaradas no campo estruturado.
- As fontes exibidas têm origem na árvore: a aplicação deriva os caminhos efetivamente navegados (`listar`, `obter`, `buscar`, `buscar_semantico`), deduplica e usa os rótulos declarados pela LLM quando existirem; caminhos declarados inexistentes são descartados.
- A extração derivada é corrigida para cobrir `obter` e as buscas, que hoje não entram na lista.
- A mensagem do assistente passa a guardar as fontes como itens estruturados (`caminho` + `rotulo` opcional), sem concatená-las ao texto.
- A aba "Chat AI" ganha o checkbox "Exibir fontes" (desmarcado por padrão). Marcado, mostra as fontes de cada resposta com separação clara; desmarcado, oculta-as. A alternância re-renderiza todas as respostas anteriores.
- "Copiar chat" e a cópia de CSV da aba passam a copiar exatamente o que está na tela, seguindo o checkbox.
- A orientação da aba e a documentação do chat são atualizadas para descrever o novo contrato.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `llm-chat-tree`: o protocolo JSON de navegação passa a admitir `fontes` no turno final, proíbe a citação de fontes no corpo da resposta e define a derivação determinística das fontes a partir das operações de navegação, com merge de rótulos declarados.
- `llm-chat-domain`: `ChatMessage.sources` passa a representar fontes estruturadas (`caminho` e `rotulo` opcional), coerentes com o tipo declarado e com o contrato do protocolo.
- `llm-chat-gui`: a aba "Chat AI" passa a oferecer o checkbox "Exibir fontes", renderiza as fontes separadas do corpo e re-renderiza as respostas ao alternar; a cópia segue o estado do checkbox.

## Impact

- **Código:** `src/flowscope/application/chat/consultar.py` (protocolo, extração de fontes, merge), `manifesto.py` (persona/formato), `protocolo.py` (parse de `fontes`), `src/flowscope/domain/chat/models.py` (fonte estruturada), `src/flowscope/presentation/gui/chat/chat_panel.py` (checkbox, render, cópia), `src/flowscope/presentation/gui/app_tabs.py` (orientação).
- **Documentação:** `docs/misc/panels.md`; possivelmente `docs/rfcs/RFC-015`.
- **Testes:** protocolo, consulta, painel, orquestração e entidades de domínio.
- **Compatibilidade:** campo `fontes` é opcional; respostas em texto puro e o resumo forçado por limite de iterações continuam funcionando com fallback para as fontes derivadas.
- Sem dependências novas.
