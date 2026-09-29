## 1. Domínio — Uso de tokens

- [x] 1.1 Estender `LLMUsage` (`domain/llm/ports.py`) com `entrada_cache: int = 0` e `cache_write: int = 0`, e verificar que consumidores existentes (guidance, RAG) seguem passando
- [x] 1.2 Ajustar os testes de domínio do `LLMUsage` e verificar cenários com e sem cache

## 2. Infraestrutura — Adaptador liteLLM

- [x] 2.1 Extrair `usage.prompt_tokens_details.cached_tokens` e `cache_creation_tokens`/`cache_write_tokens` em `_extrair_uso` (`infrastructure/llm/adapter.py`), tolerando ausência, `dict` e objeto, e verificar com respostas fake com/sem detalhes
- [x] 2.2 Adicionar teste do adaptador com `usage` contendo cache-hit e cache-write

## 3. Infraestrutura — Presets e janela de contexto

- [x] 3.1 Associar `context_window` e suporte a cache por preset em `infrastructure/llm/presets.py`, e verificar os presets existentes
- [x] 3.2 Resolver a janela preferindo `litellm.get_model_info(model)["max_input_tokens"]` e cair no preset como fallback, e verificar com liteLLM disponível e ausente
- [x] 3.3 Expor a janela resolvida e o suporte a cache pela infraestrutura (porta/adapte de config), sem a apresentação importar liteLLM, e verificar o contrato

## 4. Aplicação — Estimativa determinística de cache

- [x] 4.1 Receber no `ConsultarChatUseCase` o contador de tokens e a flag de suporte a cache (injetados), e verificar a construção
- [x] 4.2 Informar se a assinatura do prefixo estável é a mesma de uma completion anterior, e verificar o sinal com/sem mudança de contexto
- [x] 4.3 Estimar `entrada_cache` apenas quando provedor suporta cache, assinatura inalterada e provedor não reportou cache; memoizar por assinatura, e verificar os quatro cenários do spec
- [x] 4.4 Preencher `LLMUsage.entrada_cache` antes de chamar `ao_uso`, e verificar que `ao_uso` recebe o uso estimado

## 5. Apresentação — Contador e rótulo

- [x] 5.1 Ajustar `ContadorTokens.acumular` (`presentation/gui/chat/tokens.py`) para somar `entrada - entrada_cache`, e verificar com uso com/sem cache
- [x] 5.2 Rastrear o `prompt_tokens` bruto da completion mais recente para o percentual da janela, e verificar o valor bruto preservado
- [x] 5.3 Formatar o rótulo com o percentual inteiro entre parênteses e omiti-lo quando a janela for desconhecida, e verificar o formato no teste de `tokens.py`
- [x] 5.4 Ligar a janela resolvida ao painel/callback do rótulo no wiring, e verificar com teste headless do rótulo

## 6. Testes de Integração

- [x] 6.1 Teste do fluxo completo (adaptador fake com cache → use case estima → contador → texto do rótulo) e verificar o total de entrada ajustado
- [x] 6.2 Teste do percentual com janela de preset e com janela enriquecida, e verificar o arredondamento inteiro

## 7. Quality Gate

- [x] 7.1 `make lint` e `make complexity` limpos
- [x] 7.2 `pytest -m "not llm"` + `pytest -m "llm"` passam
- [x] 7.3 Testes existentes sem regressão (chat, statusbar, guidance)
- [x] 7.4 Executar `openspec validate llm-chat-contabilidade-tokens` e garantir que a change permanece válida
