## 1. Ajuste da orientação

- [x] 1.1 Reescrever o corpo da entrada `("Chat AI", "Chat AI")` de `TAB_CONTENT` em `src/flowscope/presentation/gui/app_tabs.py` para descrever a árvore de conhecimento navegável (ramos de origem do contexto), o loop de protocolo JSON da LLM, os orçamentos e a leitura somente do cache local; verificar por inspeção do texto que não há menção a cascata, resumos curtos/longos encadeados nem filtragem das notícias por casamento de título
- [x] 1.2 Conferir que a entrada mantém o formato `(titulo, body)` com as seções Objetivo, Responde a pergunta, Como usar, Contexto enviado e Como interpretar, e que `estrutura_conhecimento` continua derivando o ramo `/flowscope` sem erro

## 2. Verificação

- [x] 2.1 Executar `make lint` e verificar que passa
- [x] 2.2 Executar os testes relacionados/impactados (`pytest tests/test_presentation/test_chat_integration.py tests/test_application/test_chat_conhecimento.py tests/test_presentation/test_chat_tokens.py`) e verificar que passam
- [x] 2.3 Conferir a consistência da orientação com `docs/misc/panels.md` (seção "Chat AI") e `docs/misc/indicators.md` (seção "Contexto do Chat com I.A.")
