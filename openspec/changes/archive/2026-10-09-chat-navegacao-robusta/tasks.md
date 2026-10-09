## 1. Ramos internos vazios omitidos

- [x] 1.1 Ajustar `ramo_flowscope` (`application/chat/arvore.py`) para só anexar `/flowscope/abas` e `/flowscope/indicadores` quando houver itens; verificar que `existe()` é falso para ramos vazios com teste em `tests/test_application/test_chat_arvore.py`
- [x] 1.2 Ajustar `ramo_fundamentos` (`application/chat/arvore.py`) para só anexar `/fundamentos/tickers`, `/fundamentos/campos` e `/fundamentos/valores` quando preenchidos; verificar com teste que sub-ramos vazios são omitidos

## 2. Manifesto descreve apenas ramos existentes

- [x] 2.1 Substituir o mapa constante por `_mapa_arvore(arvore)`/`_descricao(arvore)` em `application/chat/manifesto.py`, consultando `arvore.existe(...)` e detalhando sub-ramos de `/flowscope` e `/fundamentos`; verificar que caminhos de ramos ausentes não aparecem no manifesto com teste
- [x] 2.2 Verificar determinismo do manifesto (byte-a-byte) e teto de 4.000 tokens com os ramos existentes, incluindo o teste de regressão de teto

## 3. Orientação de fallback da busca

- [x] 3.1 Atualizar o texto de `PROTOCOLO` (`application/chat/manifesto.py`) para orientar `buscar(caminho, regex, em=[...])` quando `buscar_semantico` responder `indice_indisponivel` e para preferir o nó `indice`/`buscar` a listar ramos grandes; verificar o texto no manifesto com teste
- [x] 3.2 Atualizar `SYSTEM_PROMPT` (`application/chat/consultar.py`) com a mesma orientação; verificar com teste que o prompt cita a busca por regex quando a semântica não estiver disponível

## 4. Verificação integrada

- [x] 4.1 Executar `make lint` e `make complexity` sem erros
- [x] 4.2 Executar `make test` (cobertura ≥ 85%) sem erros.
- [x] 4.3 Confirmar manualmente no Chat AI: `listar(/flowscope/indicadores)` e `listar(/fundamentos/valores)` inexistentes deixam de existir; o manifesto não cita ramos ausentes; ao receber `indice_indisponivel`, a LLM recorre a `buscar`/`indice` em vez de despejar `/noticias/Geral`
