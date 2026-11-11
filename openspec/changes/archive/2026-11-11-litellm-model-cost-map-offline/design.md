## Context

Ver `proposal.md` — Why. O liteLLM carrega o model cost map em `litellm/__init__.py` no primeiro import, antes de qualquer configuração do FlowScope. Hoje o preparo do ambiente e o `suppress_debug_info` acontecem depois do import, em dois helpers duplicados (`presets.py` e `adapter.py`). A change depende de `resiliencia-resolucao-fundos-b3`; executar somente depois dela.

## Goals / Non-Goals

**Goals:**
- Garantir que a primeira importação do liteLLM use o catálogo local, sem requisição externa.
- Eliminar o warning de tentativa de fetch e o retry em background quando não há rede.
- Centralizar o preparo do liteLLM num único helper reutilizado pelos dois pontos de import.
- Preservar a possibilidade de o usuário optar conscientemente pelo catálogo remoto.

**Non-Goals:**
- Não remover nem substituir o liteLLM por outra biblioteca.
- Não alterar a contagem de tokens, a resolução de janela ou os presets.
- Não desativar outras integrações opcionais do liteLLM que não são acionadas neste fluxo.
- Não mudar contratos públicos da porta `LLMPort`.

## Decisions

### 1. Variável de ambiente antes do import

Definir `LITELLM_LOCAL_MODEL_COST_MAP=True` **antes** de `import litellm`. O liteLLM checa essa variável no início de `get_model_cost_map`, e o valor precisa ser `true`/`True` (a comparação é `lower() == "true"`). Alternativa descartada: apontar `LITELLM_MODEL_COST_MAP_URL` para um arquivo local; exigiria distribuir/servir o JSON e não elimina a tentativa de rede.

### 2. `setdefault` para respeitar override

Usar `os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")`. Se o usuário já definiu a variável (inclusive `False` para forçar o remoto), o FlowScope não sobrescreve. Alternativa descartada: atribuição direta, que impediria o override e surpreenderia quem depende do catálogo remoto.

### 3. Helper compartilhado

Criar `preparar_litellm()` (em `infrastructure/llm/__init__.py` ou módulo auxiliar do pacote) que executa o `setdefault`. Chamá-lo no topo do pacote `infrastructure/llm` e imediatamente antes de cada `import litellm` em `presets.py` e `adapter.py`. O topo do pacote cobre importações futuras de qualquer submódulo; a chamada junto ao import preserva a garantia mesmo se o helper for usado isoladamente.

Alternativa descartada: manter o `setdefault` duplicado nos dois `_import_litellm`. Funciona, mas repete a política em dois pontos e volta a divergir com o tempo.

### 4. Manter `suppress_debug_info`

O helper continua setando `litellm.suppress_debug_info = True` após o import, preservando a supressão do banner existente. A variável de ambiente atua antes do import; o flag atua depois.

### 5. Teste em subprocesso

Testar em subprocesso para isolar o estado global de importação do liteLLM: importar `flowscope.infrastructure.llm.adapter` com a variável ausente e verificar `get_model_cost_map_source_info()["source"] == "local"` e `is_env_forced` verdadeiro, além de ausência do warning. Um teste unitário do helper cobre o `setdefault` e a preservação do override. Alternativa descartada: `importlib.reload`, que não garante reexecução do `__init__` do liteLLM e pode depender da ordem dos testes.

## Risks / Trade-offs

- **Catálogo local pode ficar defasado em relação ao remoto** → o FlowScope só usa janela/contagem; modelos novos caem no fallback `context_window` do preset e a atualização acompanha a versão do liteLLM.
- **Usuário querendo o remoto** → `setdefault` preserva a variável definida por ele.
- **Import direto do liteLLM fora do pacote LLM** → o `setdefault` no topo de `infrastructure/llm` cobre o caminho do app; importações externas deliberadas continuam sob controle de quem as fizer.
- **Teste em subprocesso mais lento** → custo pequeno e isolamento confiável do estado global.

## Migration Plan

1. Aplicar o helper e as chamadas; nenhum dado persistido é afetado.
2. Reiniciar o app; a primeira importação do liteLLM passa a usar o catálogo local.
3. Rollback: remover as chamadas/helper; o comportamento remoto volta a ocorrer.

## Open Questions

Nenhuma.
