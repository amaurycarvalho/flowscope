## 1. Retry no adaptador

- [x] 1.1 Definir as constantes de retry no adaptador (`RETRY_DELAYS` padrão e limite de tentativas) e verificar que o módulo importa sem erro.
- [x] 1.2 Adicionar ao construtor `LiteLLMChatAdapter` os pontos de injeção de sono e de jitter, com defaults de produção, e verificar que os testes existentes de `test_adapter.py` continuam passando.
- [x] 1.3 Implementar o loop de retry em `complete`, adquirindo `RateLimiter.acquire()` por tentativa e repetindo apenas exceções transitórias; verificar com teste que uma falha transitória seguida de sucesso retorna a resposta.
- [x] 1.4 Garantir que erros permanentes propagam sem retry e que o esgotamento de tentativas propaga a última exceção de domínio; verificar com testes que a chamada ao provedor ocorre uma vez no permanente e N vezes no transitório esgotado.

## 2. Testes e verificação

- [x] 2.1 Adicionar testes cobrindo: sucesso após retry, esgotamento de tentativas, erro permanente sem retry, espera de backoff com jitter determinístico e contagem de aquisições do rate limiter por tentativa; verificar com `pytest tests/test_infrastructure/test_llm/test_adapter.py`.
- [x] 2.2 Ajustar os testes de mapeamento transiente que hoje assumem uma única chamada, injetando espera nula/relógio falso; verificar que `TestMapeamentoExcecoes` passa sem esperas reais.
- [x] 2.3 Rodar a suíte do adapter e o lint/typecheck (`pytest tests/test_infrastructure/test_llm/test_adapter.py` e `ruff check src tests`) e confirmar tudo verde.
