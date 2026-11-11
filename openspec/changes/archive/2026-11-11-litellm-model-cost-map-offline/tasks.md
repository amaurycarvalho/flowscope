# Tasks

## 0. Pré-requisito bloqueante

- [x] 0.1 Confirmar que `resiliencia-resolucao-fundos-b3` foi implementada e arquivada antes de iniciar esta change; verificar com `openspec status --change resiliencia-resolucao-fundos-b3` e com a ausência da change ativa em `openspec/changes/` (arquivada)

## 1. Preparo offline do liteLLM

- [x] 1.1 Criar o helper compartilhado `preparar_litellm()` com `os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")` em `infrastructure/llm/__init__.py` e chamá-lo no topo do pacote; verificar com teste unitário que a variável é definida quando ausente e preservada quando já definida
- [x] 1.2 Usar o helper em `presets.py::_import_litellm` e `adapter.py::_import_litellm` imediatamente antes de `import litellm`, mantendo `suppress_debug_info = True`; verificar com teste que os dois caminhos chamam o helper antes do import
- [x] 1.3 Adicionar teste em subprocesso que importa `flowscope.infrastructure.llm.adapter` sem a variável definida e confirma `get_model_cost_map_source_info()["source"] == "local"` e ausência do warning de tentativa de fetch; verificar que o teste passa isolado e em conjunto
- [x] 1.4 Adicionar teste de override: com `LITELLM_LOCAL_MODEL_COST_MAP=False` definido no ambiente, o helper NÃO DEVE sobrescrever o valor; verificar com teste unitário

## 2. Documentação e verificação

- [x] 2.1 Documentar em `docs/misc/llm-payloads.md` que o FlowScope usa o catálogo local por padrão, a variável `LITELLM_LOCAL_MODEL_COST_MAP=True` e como optar pelo catálogo remoto; verificar que o texto descreve o comportamento implementado
- [x] 2.2 Executar os testes impactados de infraestrutura LLM e apresentação que usam `_import_litellm`; verificar que passam
- [x] 2.3 Executar `make lint` e `make complexity`; verificar que concluem sem erros

## Workflow follow-up

- Registrar esta change no CHANGELOG somente após a `resiliencia-resolucao-fundos-b3`.
- Arquivar a change depois da revisão do projeto.
- Execução manual do usuário: suíte completa (`make test`) e quality gate completo (`make quality-gate`), se desejar, por precaução.
