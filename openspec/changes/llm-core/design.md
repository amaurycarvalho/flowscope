## Context

Ver `proposal.md` para a motivação. O estado atual relevante:

- `~/.flowscope/config.json` é lido/escrito por `load_preferences`/`save_preferences` em `presentation/gui/app.py`, com um dicionário plano de preferências; não existe bloco `llm`.
- `domain/chat/` já expõe as portas de indexação (`DocumentoIndexavel`, `DocumentSource`), mas não há porta de LLM nem infraestrutura de LLM.
- A sub-aba "Documentos" é o `DocumentTreePanel` (`presentation/gui/charts/document_tree_panel.py`), cuja barra hoje tem apenas "Atualizar" e "Abrir documento"; o painel é instanciado em `app_tab_layout.py` com callbacks.
- `pypdf>=4` já é dependência base; `[llm]` ainda não existe no `pyproject.toml`.
- O ADR-002 §14–§20 define liteLLM como camada de chat, protocolos separados para embedding e chat (§15), `llm` no `config.json` (§19) e dependências opcionais `[llm]` (§20). A `llm-chat` ainda concentra a camada de chat que esta change extrai.

## Goals / Non-Goals

**Goals:**
- Porta `LLMPort` genérica de completion, reutilizável por `llm-chat` e pela futura change de resumo.
- Adaptador liteLLM com presets e `custom_llm_provider`.
- Rate limiter configurável por RPM (default 5), thread-safe e com enfileiramento.
- Exceções tipadas que permitam aos consumidores decidir.
- Configuração persistida em `llm.chat`, sem quebrar as preferências existentes.
- Diálogo de configuração com presets, chave mascarada e teste de conexão.

**Non-Goals:**
- Embeddings, VectorStore, RAG, chunking e ChatPanel (permanecem na `llm-chat`).
- O serviço `resumir(texto)` (change futura).
- Suporte a streaming, histórico persistente e modelos locais de chat (fora do escopo).
- CLI de configuração de LLM.

## Decisions

### 1. Bloco de configuração `llm.chat` (forma aninhada)

**Decisão:** Persistir a configuração de completion em `llm.chat`, com `provider`, `api_url`, `model`, `api_key` e `rpm`.

**Alternativa considerada:** bloco plano `llm.{provider, api_url, model, api_key, rpm}`.
**Rejeitada porque:** o ADR-002 §19 já definiu `llm` com sub-blocos, e a `llm-chat` precisa de `llm.embedding` (ciclo de vida e provedor distintos). A forma aninhada mantém a base de completion isolada do embedding e evita migração futura de schema.

**Consequências:** `rpm` fica em `llm.chat.rpm` (o rate limit incide sobre chamadas de completion). A leitura preenche defaults; a gravação faz read-modify-write preservando as demais chaves de `llm` e do arquivo.

### 2. Presets com `api_url` + `custom_llm_provider="openai"`

**Decisão:** Cada preset define `model` e `api_url`; o adaptador chama `litellm.completion(model=..., api_base=..., custom_llm_provider="openai", api_key=...)`. Provedores: `none`, `openai`, `gemini`, `copilot`, `claude`, `deepseek`, `ollama`, `custom`.

**Alternativa considerada:** prefixos nativos do liteLLM (`openai/...`, `anthropic/...`, `gemini/...`).
**Rejeitada porque:** o padrão de presets do projeto adota endpoints OpenAI-compatible com `api_url` configurável, o que também habilita `ollama`, gateways e proxies sem código novo.

**Consequências:** os presets `claude` e `gemini` pressupõem endpoints OpenAI-compatible nas URLs informadas; caso o provedor não exponha esse formato, a chamada resulta em `LLMProviderError` com a mensagem do provedor. Adicionar prefixos nativos depois é uma evolução aditiva.

### 3. Layout de módulos

```
domain/llm/
  exceptions.py     LLMError e subclasses
  ports.py          LLMPort
infrastructure/llm/
  presets.py        PROVIDER_PRESETS, resolve_provider
  config.py         load_llm_config / save_llm_config / check_llm_deps / get_presets
  rate_limiter.py   RateLimiter (RPM)
  adapter.py        LiteLLMChatAdapter
  factory.py        create_llm_provider
presentation/gui/llm/
  config_dialog.py  LLMConfigDialog
```

**Decisão:** domínio para a porta e as exceções; infraestrutura para liteLLM, config e rate limiter; GUI em subpacote próprio.
**Alternativa considerada:** tudo em `infrastructure/llm/`.
**Rejeitada porque:** a porta e as exceções são contratos de domínio consumidos por aplicação e GUI; mantê-las em `domain/` respeita a arquitetura de portas/adaptadores já usada no projeto.

### 4. Rate limiter por janela deslizante

**Decisão:** `RateLimiter(rpm)` com um `deque` de timestamps monotônicos protegido por `threading.Lock`; `acquire()` descarta timestamps fora da janela de 60s e, se a janela estiver cheia, dorme até o timestamp mais antigo expirar. Chamadas excedentes aguardam (enfileiramento), sem erro.

**Alternativa considerada:** token bucket com rajada (burst).
**Rejeitada porque:** o requisito é não estourar a cota do provedor; uma janela estrita evita rajadas e é mais simples de testar com relógio injetável.

**Consequências:** o limiter é síncrono e bloqueante; por isso as chamadas de LLM devem ocorrer em threads de trabalho (o diálogo de teste já segue o padrão de fila + polling do projeto).

### 5. Porta `LLMPort` orientada a completion

**Decisão:** `LLMPort.complete(messages, system_prompt=None) -> str`, com assinatura equivalente à `ChatPort` da `llm-chat`, para que a `llm-chat` consuma a base sem adaptação.

**Alternativa considerada:** porta unificada `LLMPort` com `embed()` e `complete()`.
**Rejeitada porque:** o ADR-002 §15 separa embedding e chat por ciclo de vida e provedor. A `LLMPort` desta change é apenas de completion (não unifica embedding), preservando a decisão do ADR.

### 6. Mapeamento de exceções do liteLLM

**Decisão:** o adaptador traduz exceções do liteLLM para a hierarquia do domínio: `Timeout`/`APIConnectionError` → `LLMCommunicationError`; `RateLimitError` → `LLMRateLimitError`; `AuthenticationError`/`APIError`/`BadRequestError` → `LLMProviderError`. `ImportError` do liteLLM e provedor `none` → `LLMUnavailableError`. Configuração `custom` incompleta → `LLMConfigurationError`.

**Alternativa considerada:** propagar as exceções nativas do liteLLM.
**Rejeitada porque:** os consumidores não devem depender do liteLLM para tratar erros (a dependência é opcional); a hierarquia do domínio desacopla a decisão do consumidor.

### 7. Integração com o `config.json` existente

**Decisão:** `infrastructure/llm/config.py` lê o arquivo inteiro, mescla defaults de `llm.chat` e, ao salvar, relê o arquivo, substitui apenas `llm.chat` e regrava — sem importar `presentation`.

**Alternativa considerada:** reutilizar `load_preferences`/`save_preferences` de `presentation/gui/app.py`.
**Rejeitada porque:** inverteria a dependência (infraestrutura → apresentação). O read-modify-write preserva as preferências da GUI e o futuro `llm.embedding`.

### 8. Botão "I.A." via callback no painel

**Decisão:** `DocumentTreePanel` ganha um terceiro botão `_ia_btn` (após `_open_btn`) e um callback opcional `ia_callback`; `app_tab_layout.py` injeta o método que abre o `LLMConfigDialog`. O botão permanece habilitado independentemente de haver documentos em cache ou ticker selecionado, mas é incluído em `all_buttons()` e, portanto, desabilitado e restaurado junto com os demais botões do painel durante as cargas de dados (bloqueio global).

**Alternativa considerada:** o painel instanciar o diálogo diretamente.
**Rejeitada porque:** o painel é hoje agnóstico de LLM e testável sem Tk; o callback mantém essa separação e permite teste unitário do acionamento.

### 9. Teste de conexão assíncrono

**Decisão:** o botão "Testar" desabilita-se enquanto o teste roda, executa `create_llm_provider` + `complete([{"role": "user", "content": "hello"}])` em thread de trabalho e publica o desfecho na thread do Tk por fila, exibindo sucesso ou a mensagem da exceção tipada.

**Alternativa considerada:** chamada síncrona na thread da interface.
**Rejeitada porque:** o rate limiter pode bloquear e a rede pode demorar, congelando a GUI.

### 10. Composição de `[llm]` e adaptação da `llm-chat`

**Decisão:** `llm-core` cria `[llm] = ["litellm>=1.50"]`; a `llm-chat` estende o grupo com `fastembed` (pypdf já é base). A `llm-chat` deixa de definir cliente de chat, config de chat e `ConfigDialog`, passando a consumir `LLMPort`, `create_llm_provider` e `load_llm_config`; mantém embeddings, VectorStore, RAG, ChatPanel e o prompt RAG.

**Alternativa considerada:** grupos separados `[llm]` e `[llm-local]`.
**Rejeitada porque:** manter um único grupo opcional `[llm]` simplifica a instrução de instalação já documentada no ADR-002 §20.

### 11. Diálogo de configuração modal e não redimensionável

**Decisão:** o `LLMConfigDialog` é uma janela `Toplevel` não redimensionável (`resizable(False, False)`), transiente da janela principal (`transient`) e modal (`grab_set`), com foco inicial (`focus_set`). O tamanho é definido pelo conteúdo do formulário.

**Alternativa considerada:** janela redimensionável e não modal.
**Rejeitada porque:** o diálogo é um formulário curto de configuração; travar o redimensionamento preserva o layout e o modal evita edições concorrentes na janela principal, inclusive enquanto o teste de conexão roda em thread de trabalho.

### 12. liteLLM embutido no executável do PyInstaller

**Decisão:** o alvo `build` do Makefile instala `.[llm]` antes de empacotar, e `flowscope.spec` coleta os submódulos (`collect_submodules`) e os arquivos de dados (`collect_data_files`, exceto os assets do proxy web) do `litellm`, falhando com mensagem clara se o pacote não estiver instalado. Assim o executável inclui o LLM e `check_llm_deps()` retorna verdadeiro em máquinas sem Python/pip.

**Alternativa considerada:** manter o liteLLM fora do binário e depender de `pip install flowscope[llm]` na máquina de destino.
**Rejeitada porque:** máquinas que rodam apenas o executável do PyInstaller não têm Python nem pip; sem embutir, os recursos de I.A. ficam inacessíveis nesses ambientes.

**Consequências:** o binário cresce (passa a incluir o liteLLM e sua tabela de preços/contexto) e o build passa a exigir o grupo `[llm]`; o PyInstaller detecta o import tardio do adaptador apenas quando o pacote está presente no ambiente de build.

### 13. Registro em log das falhas do teste de conexão

**Decisão:** as falhas do botão "Testar" são registradas via `logging.getLogger("flowscope")` em nível `WARNING`, com provedor, modelo, API URL e o tipo/mensagem do erro — nunca a chave de API. O log é feito na thread da interface, em `_verificar_teste`, ao consumir o desfecho da fila; a exibição na tela permanece inalterada.

**Alternativa considerada:** registrar o log diretamente na thread de trabalho, dentro de `_executar_teste`.
**Rejeitada porque:** o registro em thread de trabalho interfere na captura de logs do pytest/Tk do ambiente de testes e atrasa a publicação do desfecho; concentrar o registro na thread da interface mantém o padrão do projeto (a thread de trabalho só publica na fila) e evita concorrência no handler de log.

**Consequências:** a fila do teste passa a carregar também a configuração e a exceção, e o log vai para o arquivo rotativo `~/.flowscope/logs/flowscope.log`.

## Risks / Trade-offs

- **[Risco] `custom_llm_provider="openai"` não funciona em endpoints nativos de Anthropic/Gemini** → Mitigação: documentar que os presets exigem endpoints OpenAI-compatible; erros chegam como `LLMProviderError` com a mensagem do provedor; prefixos nativos podem ser adicionados depois sem quebrar a porta.
- **[Risco] chave de API em texto claro no `config.json`** → Mitigação: arquivo local do usuário, chave mascarada na GUI; sem log de segredos.
- **[Risco] rate limiter bloqueante na thread da GUI** → Mitigação: todas as chamadas ocorrem em threads de trabalho com fila.
- **[Trade-off] rate limit global por processo** → Simplifica; múltiplas instâncias do FlowScope não compartilham o limite. Aceitável para uso desktop.
- **[Trade-off] `litellm` é uma dependência grande** → Embutida no executável para funcionar em máquinas sem Python/pip; o binário cresce, mas os recursos de I.A. ficam disponíveis sem instalação. Em instalações via código-fonte permanece opcional em `[llm]`.
- **[Risco] teste de conexão consome cota real** → Aceitável; é acionado manualmente e o rate limiter protege a cota configurada.

## Migration Plan

1. Adicionar `domain/llm/` (porta + exceções) e `infrastructure/llm/` (presets, config, rate limiter, adaptador, factory) com testes.
2. Adicionar o grupo `[llm]` ao `pyproject.toml` e o marcador `pytest.mark.llm`.
3. Adicionar o `LLMConfigDialog`, o callback e o botão "I.A." no `DocumentTreePanel`, com testes de GUI.
4. Atualizar o README com `pip install flowscope[llm]`.
5. Adaptar a change `llm-chat` para consumir a base.

**Rollback:** mudanças aditivas e opcionais via `[llm]`; remover o bloco `llm.chat` do `config.json` restaura o comportamento anterior (provider `none`).
