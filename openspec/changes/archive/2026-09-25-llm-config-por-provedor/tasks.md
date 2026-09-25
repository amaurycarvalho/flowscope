## 1. Persistência por provedor em `config.py`

- [x] 1.1 Adicionar `load_provider_configs(path)` que devolve o mapa `providers` normalizado e migra o formato plano antigo (campos planos de `llm.chat` viram a entrada do provedor ativo), verificando com testes de arquivo no formato novo e no formato antigo
- [x] 1.2 Ajustar `load_llm_config(path)` para resolver o provedor ativo a partir de `providers`, mantendo o dict plano com defaults, verificando que os testes de leitura existentes continuam passando
- [x] 1.3 Ajustar `save_llm_config(config, path)` para _read-modify-write_ em `llm.chat`: gravar a entrada do provedor ativo em `providers`, atualizar `provider` e preservar os demais provedores, `llm.embedding` e `llm.guidance`, verificando com teste de roundtrip que salvar um provedor não apaga os outros
- [x] 1.4 Garantir que a gravação de uma config no formato antigo resulta no formato novo preservando `api_key` e `rpm`, verificando com teste de migração no primeiro save

## 2. Diálogo de configuração

- [x] 2.1 Carregar `self._working` a partir de `load_provider_configs` na abertura e preencher os campos do provedor ativo, verificando com teste de abertura que exibe a config salva do ativo
- [x] 2.2 Alterar o handler de troca de provedor para descarregar o formulário atual em `self._working` (exceto `none`), restaurar a entrada do provedor selecionado quando existir e aplicar defaults do preset com chave vazia quando não existir, verificando com testes de restauração e de limpeza de chave ao trocar
- [x] 2.3 Tratar `none` limpando os campos sem criar entrada em `self._working` nem remover os demais provedores, verificando com teste de seleção de `none` e retorno a um provedor configurado
- [x] 2.4 Salvar apenas o provedor ativo via `save_llm_config`, mantendo edições não salvas apenas em memória, verificando com teste de que trocar de provedor sem salvar (ou cancelar) não altera o `config.json`

## 3. Verificação final

- [x] 3.1 Rodar `python -m pytest tests/test_infrastructure/test_llm/test_config.py tests/test_presentation/test_llm_config_dialog.py tests/test_presentation/test_preferences.py` e confirmar que passam
- [x] 3.2 Rodar `make lint`, `make complexity` e `openspec validate llm-config-por-provedor` sem erros
