## Why

O primeiro `import litellm` do processo dispara automaticamente um download do catálogo remoto de preços/janelas de contexto (`model_prices_and_context_window.json` no GitHub). Em máquinas offline ou com rede instável isso gera o warning `LiteLLM: model cost map fetch attempt 1/3 failed (...) Falling back to local backup`, atrasa o uso da aba Chat AI e tenta novamente em background. O FlowScope só precisa do catálogo local embutido no pacote para contagem de tokens e janela de contexto, então a busca externa deve ser desativada.

**Dependência:** esta change DEVE ser executada somente após `resiliencia-resolucao-fundos-b3` estar implementada (e preferencialmente arquivada).

## What Changes

- Definir `LITELLM_LOCAL_MODEL_COST_MAP=True` antes do primeiro `import litellm`, preservando um override explícito do usuário (`setdefault`).
- Centralizar esse preparo em um helper compartilhado em vez de duplicar em `presets.py` e `adapter.py`.
- Garantir que a primeira importação do liteLLM não realize busca externa do model cost map, mantendo `get_model_cost_map_source_info()["source"] == "local"`.
- Manter `litellm.suppress_debug_info = True` e o comportamento de contagem de tokens/janela de contexto.
- Cobrir com teste que o import do adaptador/presets usa a fonte local e não dispara a busca remota.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `llm-provider`: a primeira importação do liteLLM passa a usar explicitamente o catálogo local de model cost map, sem busca automática externa, e a garantia de ausência de escrita de depuração passa a incluir esse warning de rede.

## Impact

- `infrastructure/llm/presets.py` e `infrastructure/llm/adapter.py`: preparo do ambiente antes do import do liteLLM.
- `infrastructure/llm/__init__.py` ou novo módulo auxiliar compartilhado: helper único de configuração/importação.
- Testes de infraestrutura LLM: verificação de que a fonte do model cost map é local e que nenhuma requisição ao GitHub é feita no import.
- Sem novas dependências e sem mudança no contrato externo da porta `LLMPort`.
- Follow-up: registrar no CHANGELOG depois da `resiliencia-resolucao-fundos-b3`.
