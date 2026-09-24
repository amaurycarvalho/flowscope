## Context

Ver `proposal.md` — Why. A `llm-core` (arquivada, implementada) persiste um único bloco plano `llm.chat` (`provider`, `api_url`, `model`, `api_key`, `rpm`) via `load_llm_config`/`save_llm_config` em `infrastructure/llm/config.py`. O diálogo `LLMConfigDialog` (`presentation/gui/llm/config_dialog.py`) lê esse bloco ao abrir e, em `_on_preset_change`, sobrescreve apenas `model`/`api_url` com os defaults do preset, deixando o campo de chave intacto — o que transporta a chave de um provedor para outro.

Consumidores que dependem do formato plano e NÃO devem mudar: `create_llm_provider(load_llm_config())` em `factory.py`, `document_summary.py`, `document_guidance.py` e `app_tab_layout.py`. O bloco `llm.guidance` e o futuro `llm.embedding` são sub-blocos irmãos e ficam fora do escopo.

## Goals / Non-Goals

**Goals:**
- Memória independente por provedor em `llm.chat.providers`, com restauração automática ao trocar a seleção.
- Manter `load_llm_config()` devolvendo o dicionário plano do provedor ativo, sem tocar nos consumidores.
- Migrar arquivos no formato antigo sem perda de configuração.

**Non-Goals:**
- Perfis `custom` múltiplos (um único slot `custom`, como hoje).
- `llm.embedding` por provedor (change `llm-chat-rag`).
- Criptografia das chaves de API (comportamento atual mantido).
- Redesenho do diálogo, do botão "Testar" ou do log de falhas.

## Decisions

### 1. `providers` como fonte única e leitura plana derivada

O bloco passa a ser `{"provider": <ativo>, "providers": {<nome>: {api_url, model, api_key, rpm}}}`. `providers` é a única fonte de verdade; `load_llm_config()` resolve o provedor ativo a partir dele e devolve o dict plano (defaults quando ausente). Nada é duplicado no arquivo.

Alternativa considerada: manter também os campos planos do ativo como espelho para compatibilidade de downgrade. Rejeitada por criar duas fontes de verdade no arquivo; um downgrade não apaga o dado (a chave continua em `providers`) e volta a funcionar ao reatualizar.

### 2. Compatibilidade de leitura e migração no primeiro save

A leitura aceita os dois formatos: se houver `providers`, usa-o; se houver apenas o formato plano antigo, trata os campos planos como a entrada `providers[provider]`. A gravação sempre produz o formato novo. Assim a migração é implícita, sem passo manual e sem perder a `api_key`.

### 3. API de configuração no módulo `config.py`

- `load_provider_configs(path)` → mapa normalizado `providers`, já migrando o formato antigo.
- `load_llm_config(path)` → dict plano do ativo (assinatura atual preservada).
- `save_llm_config(config, path)` → *read-modify-write*: grava `providers[provider]` com os campos do ativo, atualiza `provider` e preserva os demais provedores e os outros blocos do arquivo.

O diálogo usa `load_provider_configs` para restaurar na troca e `save_llm_config` para gravar o ativo. `create_llm_provider` e os demais consumidores permanecem inalterados.

### 4. Stash em memória e tratamento de `none` no diálogo

O diálogo mantém `self._working` (cópia de `providers`) durante a sessão. Ao trocar o provedor: descarrega o formulário atual em `self._working[atual]` (exceto quando `atual == "none"`, que é efêmero), carrega `self._working[novo]` se existir, senão aplica defaults do preset com `api_key` vazia. `none` limpa os campos e não cria entrada. "Salvar" grava apenas o provedor ativo; "Cancelar"/fechar descarta `self._working`. O campo de chave é sempre limpo quando não há entrada salva, eliminando o vazamento entre provedores.

### 5. Escopo da memória por provedor

Cada entrada guarda `api_url`, `model`, `api_key` e `rpm`, pois o usuário pode editar modelo/URL mesmo em presets nomeados e o RPM varia por provedor.

### 6. `none` e provedores desconhecidos

`none` nunca entra em `providers`. Um valor de `provider` fora dos presets continua sendo lido e exibido, mas o combobox `readonly` não permite selecioná-lo — comportamento atual mantido.

## Risks / Trade-offs

- **[Risco] Chave de um provedor aparecer em outro** → no carregamento de provedor sem entrada salva, `api_key` é sempre esvaziada; cenário coberto por spec e teste.
- **[Risco] Downgrade para versão anterior** → o formato novo não é lido pela versão antiga (campos planos ausentes), mas nada é apagado; o dado volta ao reatualizar. Documentado como não-objetivo de compatibilidade reversa.
- **[Trade-off] `custom` único** → só um conjunto de modelo/URL/chave custom é lembrado; perfis múltiplos ficam para uma evolução futura.
- **[Risco] `save_llm_config` preservar provedores antigos** → o *read-modify-write* garante que salvar o ativo não apaga as entradas já gravadas; coberto por teste de roundtrip.

## Migration Plan

Sem passo manual: arquivos no formato antigo são lidos normalmente e reescritos no formato novo na próxima gravação. Rollback = reverter o código; a configuração antiga deixa de ser lida pela versão anterior, mas permanece no arquivo (em `providers`), sendo recuperada ao reinstalar a versão com esta mudança.
