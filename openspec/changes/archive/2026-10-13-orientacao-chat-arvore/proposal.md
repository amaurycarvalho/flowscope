## Why

O texto de orientação da aba "Chat AI" em `TAB_CONTENT` (`app_tabs.py`) ainda descreve o mecanismo antigo de **cascata** (documentos com resumos curtos/longos e notícias filtradas por título, com confirmação de envio do índice). Após a `chat-arvore-navegavel`, o chat opera sobre uma **árvore de conhecimento navegável** por um loop de protocolo JSON; a orientação exibida ao usuário — e também enviada à LLM pelo ramo `/flowscope` — ficou desatualizada e contradiz o comportamento real.

## What Changes

- Atualizar o texto de orientação da aba "Chat AI" em `TAB_CONTENT` para descrever a árvore de conhecimento navegável (ramos de origem do contexto), o protocolo de navegação da LLM, os orçamentos e a leitura somente de cache.
- Manter a estrutura do `body` do `TAB_CONTENT` (título + seções Objetivo, Responde a pergunta, Como usar, Contexto enviado, Como interpretar) e o enquadramento dos ramos disponíveis.
- Não alterar o comportamento do chat nem o protocolo da árvore; a mudança é de conteúdo de orientação (interface e conhecimento do `/flowscope`).

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `llm-chat-gui`: o requisito de orientação no quadro textual da aba "Chat AI" passa a exigir que a orientação descreva a árvore de conhecimento navegável, as origens do contexto como ramos, o protocolo de navegação da LLM, os orçamentos e a leitura somente de cache, no lugar da cascata de contexto.

## Impact

- **Código:** `src/flowscope/presentation/gui/app_tabs.py` (entrada `CHAT_AI_TAB` de `TAB_CONTENT`).
- **Conhecimento da LLM:** o texto também compõe o ramo `/flowscope` via `estrutura_conhecimento`, de modo que a atualização corrige igualmente o que a LLM lê sobre a própria aba.
- **Documentação:** `docs/misc/panels.md` e `docs/misc/indicators.md` já descrevem o comportamento atual; conferir consistência.
- **Testes:** não há asserção sobre o corpo da orientação da aba "Chat AI"; os testes existentes verificam apenas o título e o ramo de conhecimento.
- Sem dependências novas, sem alterações de API ou infraestrutura.
