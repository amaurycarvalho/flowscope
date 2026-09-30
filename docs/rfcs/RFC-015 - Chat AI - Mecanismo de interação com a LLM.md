# RFC-015: Mecanismo de interação da aba "Chat AI" com a LLM via árvore de conhecimento navegável

> RFC descritiva no formato **PROBE** (Problem, Root Cause, Options, Better Solution, Evaluate). Documenta o funcionamento **atual** do mecanismo de interação com a LLM na aba de topo "Chat AI", com foco em: troca de mensagens, dados envolvidos, sequência de navegação, origens dos dados e estrutura do payload. Esta revisão substitui o mecanismo anterior de cascata determinística por uma **árvore de conhecimento navegável por protocolo JSON**, com foco em **máximo cache-hit** e **mínimo de input tokens por turno**.

---

## 1. Problem (Problema)

A aba "Chat AI" precisa responder perguntas em linguagem natural sobre o **estado local** do FlowScope — a watchlist carregada, a tabela de fundamentos, os documentos corporativos e as notícias/informações regulatórias em cache, além do próprio funcionamento da ferramenta — **sem** que o modelo de linguagem tenha sido treinado com esses dados e **sem** consultar a B3/CVM a cada pergunta.

O problema é responder à pergunta do usuário com **contexto suficiente, atual e rastreável**, respeitando simultaneamente:

- **Limite de janela de contexto** dos modelos (de ~128K a ~1M tokens nos presets suportados).
- **Custo e latência** por token, que crescem a cada turno se o contexto inteiro for reenviado.
- **Precisão**: sem contexto, a LLM alucina; com contexto excessivo e ruidoso, ela se perde e responde pior.
- **Operação offline/cache-only**: o chat é **estritamente leitor de cache** — nunca resume nem extrai texto sob demanda, para não gerar custo escondido nem efeitos colaterais no cache.
- **Desacoplamento**: a interface não pode depender de uma biblioteca específica (liteLLM) nem bloquear a thread do Tk durante a chamada de rede.

Gargalos específicos do mecanismo anterior que motivam esta revisão:

1. **Prefixo estável grande por construção.** Todos os resumos (curto + longo) de todos os tickers da watchlist entram no prefixo já na 1ª chamada. Apesar de cacheável, o custo absoluto do cache-hit cresce com a watchlist.
2. **Granularidade grosseira.** A escalada é binária: "resumo" ou "texto integral". Não há como a LLM pedir um campo específico, um título de notícia, ou um parágrafo.
3. **Contexto pré-computado, não navegável.** O mecanismo decide o que entra com base em heurísticas de aplicação; a LLM não participa da seleção.
4. **Sem reuso entre turnos.** Cada nova pergunta recomeça a seleção do zero; a navegação anterior é descartada.
5. **Índice de notícias inteiro no sufixo** (até 64K chars) sempre que há casamento de regex, sem granularidade por grupo ou por item.

O problema, portanto, não é "chamar uma LLM", mas **expor o estado local como uma árvore navegável de granularidade fina, com protocolo determinístico, prefixo estável pequeno e cache-hit máximo**.

---

## 2. Root Cause (Causa Raiz)

As causas estruturais que tornam o problema não trivial:

1. **A LLM é stateless e alheia ao estado local.** Cada chamada é independente; todo o conhecimento precisa ser injetado no payload.
2. **O estado relevante é heterogêneo e vive em origens distintas.** Fundamentos em memória, resumos e textos em cache de arquivos por ticker, notícias em catálogo próprio. Formatos, granularidades e custos de leitura diferentes.
3. **Enviar tudo sempre é inviável e enviar nada é inútil.** A assimetria entre a riqueza do estado local e a janela obriga a uma política de seleção.
4. **Reenviar contexto estável a cada turno desperdiça tokens.** Sem um prefixo estável, cada turno paga integralmente pelo bloco.
5. **A informação nem sempre é recuperável.** Documentos e notícias pendentes de resumo/extração não existem no cache; o chat precisa omiti-los em silêncio.
6. **O contexto é pré-computado, não navegável.** O mecanismo entrega "tudo o que pode caber" em vez de "o que a LLM pediu".
7. **A granularidade do cache e da navegação é a mesma do armazenamento**, não a do consumo. Resumos e fundamentos são empacotados como bloco monolítico.

A causa raiz é a **falta de um mecanismo que traduza um estado local grande, heterogêneo e parcialmente indisponível em uma árvore navegável de granularidade fina, com manifesto pequeno e estável (cacheável) e navegação orientada pela própria LLM via protocolo determinístico**.

---

## 3. Options (Opções)

### Opção A — Enviar todo o estado local em toda pergunta

- **Prós**: simplicidade.
- **Contras**: estoura a janela; custo e latência proibitivos; degradação por ruído.

### Opção B — Enviar apenas a pergunta (zero contexto)

- **Prós**: barato e rápido.
- **Contras**: respostas genéricas ou alucinadas.

### Opção C — Fine-tuning / modelo dedicado ao domínio

- **Prós**: contexto "embutido".
- **Contras**: custo de treino; dados mudam a cada carga; incompatível com multi-provedor.

### Opção D — RAG vetorial (embeddings + VectorStore + top-k)

- **Prós**: escala; recuperação semântica.
- **Contras**: pipeline de indexação; novas dependências; complexidade prematura para o volume atual. _Permanece como evolução prevista (`llm-chat-rag`), agora plugando-se como povoamento de nós da árvore._

### Opção E — Cascata determinística não vetorial, cache-only, com prefixo estável (mecanismo anterior)

- **Prós**: sem dependências novas; determinística.
- **Contras**: prefixo grande; granularidade grosseira; LLM não participa da seleção; sem reuso entre turnos.

### Opção F — Uso de ferramentas / function calling (agente)

- **Prós**: o modelo decide o que consultar.
- **Contras**: nem todos os presets suportam de forma homogênea; múltiplas idas-e-vindas; complexidade de segurança.

### Opção G — Árvore de conhecimento navegável com protocolo JSON determinístico

- **Prós**: prefixo estável pequeno e fixo (manifesto) → cache-hit máximo; granularidade fina (a LLM pede nós específicos); busca orientada pela LLM com regex determinístico; reuso de navegação entre turnos; substitui `input_limitado` e os gates anteriores por um gate único de tokens; provedor-agnóstico (JSON, sem tool calls); testável offline com LLM fake.
- **Contras**: exige a LLM seguir JSON estrito (mitigável com `_extrair_json` tolerante + fallback); risco de ReDoS (mitigável com timeout + limites); mais iterações por prompt (mitigável com paralelismo e gates).

---

## 4. Better Solution (Solução Superior)

A solução adotada é a **Opção G**: uma **árvore de conhecimento navegável**, com **manifesto estável pequeno** como prefixo, **protocolo JSON determinístico**, **busca regex orientada pela LLM**, **gates de tokens e iterações** e **reuso de navegação entre turnos**. As fontes adicionais e a evolução vetorial plugam-se como **povoamento de nós**, sem alterar o protocolo.

### 4.1 Visão de camadas e contratos

| Camada             | Papel                                                                           | Artefato principal                                                                    |
| ------------------ | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Apresentação (GUI) | Painel, sessão em memória, display e coordenação assíncrona                     | `ChatPanel`, `EnvioMixin`, `ContadorTokens`                                           |
| Aplicação          | Árvore, manifesto, protocolo, gates e orquestração                              | `ArvoreConhecimento`, `ManifestoArvore`, `ProtocoloNavegacao`, `ConsultarChatUseCase` |
| Domínio            | Entidades de conversa e porta de completion                                     | `ChatSession`, `ChatMessage`, `LLMPort`, `LLMUsage`                                   |
| Infraestrutura     | Adaptador liteLLM, rate limiter, leitura de config, presets, segurança de regex | `LiteLLMChatAdapter`, `RateLimiter`, `config.py`, `presets.py`, `seguranca_regex.py`  |

O único contrato de saída para o provedor permanece a porta de domínio `LLMPort` (`domain/llm/ports.py`):

```python
def complete(self, messages: list[dict], system_prompt: str | None = None) -> LLMResposta
```

`LLMResposta` carrega `texto` e `uso` (`LLMUsage` com `entrada`, `saida`, `entrada_cache`, `cache_write`). Nenhum consumidor importa o liteLLM diretamente.

### 4.2 Estrutura da árvore de conhecimento

A árvore é montada **cache-only**, em memória (índice de caminhos) + cache de arquivos sob demanda (conteúdo pesado). Caminhos canônicos:

```
/flowscope
  /abas                              → lista (nome + propósito)
  /abas/<aba>/subabas                → lista (nome + propósito + o que contém)
  /indicadores                       → lista (nome + propósito)
  /meta                              → versão, licença, repositório

/fundamentos
  /tickers                           → lista de tickers da watchlist
  /campos                            → lista de campos + propósito
  /valores/<ticker>                  → linha serializada do ticker

/documentos
  /tickers                           → lista de tickers com documento
  /<ticker>/curto                    → resumo curto
  /<ticker>/longo                    → resumo longo
  /<ticker>/texto                    → texto integral (truncado por teto)

/noticias
  /grupos                            → 4 grupos fixos (Censuras Públicas, Condições
                                       Excepcionais, Programas de Aquisição, Geral)
  /<grupo>/indice                    → índice compacto (data, tipo, título, chave n<sha1[:10]>)
  /<grupo>/<chave>/titulo            → título
  /<grupo>/<chave>/resumo            → resumo (quando cacheado)
  /<grupo>/<chave>/texto             → texto integral (quando cacheado)
```

Regras:

- Nós folha retornam **conteúdo**; nós internos retornam **filhos imediatos** (nome + metadado curto).
- Todo nó é **resolvível por caminho**.
- Nós sem dado (pendente de resumo/extração) **não existem**; `listar` os omite silenciosamente.
- O índice (`listar`/`contar`/`existe`) vive em memória; o conteúdo pesado (`obter`/`buscar` em texto) é lido do **cache de arquivos** quando necessário.
- **Versionamento do índice**: hash do conjunto de arquivos + mtime; invalida o manifesto quando muda.

### 4.3 Manifesto da árvore (prefixo estável)

Bloco único, **byte-a-byte idêntico entre turnos** enquanto a assinatura do estado não mudar. Contém:

- **PERSONA E REGRAS** (herdado do `SYSTEM_PROMPT`).
- **DESCRIÇÃO DA ÁRVORE**: o que é, como está organizada, o que cada ramo contém.
- **METADADOS CURTOS**: propósito de cada aba, sub-aba, indicador, campo e grupo de notícias. Curadoria em arquivo de configuração; ausência degrada para "só chave".
- **PROTOCOLO DE NAVEGAÇÃO**: operações permitidas + esquema JSON de resposta.
- **LISTAS DE CHAVES**: tickers, campos, abas, indicadores, grupos (apenas chaves; sem valores pesados).

**Teto rígido do manifesto: 4.000 tokens.** Se estourar, o ramo mais volumoso degrada para "só chaves" e a LLM descobre propósito via `obter`. Um teste de regressão falha se o manifesto passar do teto em uma watchlist canônica.

Exemplo (trecho):

```
## Árvore de conhecimento do FlowScope

Você tem acesso a uma árvore navegável montada a partir do estado local.
Ela contém: /flowscope, /fundamentos, /documentos, /noticias.

### Operações
- listar(caminho)                        → filhos imediatos (nome + metadado curto)
- obter(caminho)                         → conteúdo do nó
- contar(caminho)                        → nº de nós na subárvore
- existe(caminho)                        → booleano
- buscar(caminho, regex, em=[...], max)  → nós cujos campos casam com o regex
- resetar_navegacao()                    → descarta o histórico de navegação

### Formato de resposta (JSON estrito)
{"resposta": "<texto ou null>", "solicitacoes": [
  {"op": "contar", "caminho": "/documentos/PETR4/*"},
  {"op": "listar", "caminho": "/noticias/Censuras Públicas/indice"}
]}
Se `solicitacoes` estiver vazio, `resposta` é final.

### Limites
- Até 8 operações por turno.
- Busca regex: timeout 100 ms, máx. 50 resultados, padrões catastróficos bloqueados.
- Recomendado: usar `contar`/`existe` antes de `listar` em ramos grandes.
```

O `SYSTEM_PROMPT` instrui a LLM a:

- Responder só com base no contexto navegado.
- Citar fontes (tickers, chaves de notícia, caminhos).
- Inferir o ticker da pergunta; **pedir esclarecimento** quando ambíguo.
- Usar `contar`/`existe` antes de listar ramos grandes.
- Declarar quando a resposta vem de navegação anterior e não do estado corrente.
- Em caso de negativa (`{"negado": true, ...}`), mudar de estratégia ou resumir o que já tem.

### 4.4 Protocolo de navegação (JSON)

A LLM emite, a cada turno, um JSON estrito. O `_extrair_json` tolerante (já existente) tenta, em ordem: bloco cercado por ` ```json ... ``` `, texto cru, trecho entre primeira `{` e última `}`. Só aceita dicionário com `"resposta"`. Sem JSON reconhecido, **todo o texto é a resposta final** e o loop encerra.

Esquema de `solicitacoes` (lista, até 8 ops):

| `op`                | Campos obrigatórios | Campos opcionais              | Retorno                                  |
| ------------------- | ------------------- | ----------------------------- | ---------------------------------------- |
| `listar`            | `caminho`           | —                             | filhos imediatos (nome + metadado curto) |
| `obter`             | `caminho`           | —                             | conteúdo do nó                           |
| `contar`            | `caminho`           | —                             | inteiro                                  |
| `existe`            | `caminho`           | —                             | booleano                                 |
| `buscar`            | `caminho`, `regex`  | `em` (lista de campos), `max` | lista de nós + metadados                 |
| `resetar_navegacao` | —                   | —                             | confirmação                              |

Validação antes de executar:

- Op desconhecida → erro estruturado devolvido à LLM (conta iteração).
- Caminho inválido → erro estruturado.
- `regex` inválida ou bloqueada → erro estruturado com motivo.

As operações de um mesmo turno são executadas **sequencialmente na ordem da lista** (determinismo), agregadas num único bloco `[RESULTADO_NAVEGACAO]`:

```json
{"resultados": [
  {"op": "contar", "caminho": "/documentos/PETR4/*", "dados": 3},
  {"op": "listar", "caminho": "/noticias/Censuras Públicas/indice", "dados": [...]},
  {"op": "buscar", "caminho": "/noticias", "regex": "PETR4",
   "dados": [...], "truncado": false}
]}
```

### 4.5 Loop de navegação (payload e sequência)

Estrutura do array de mensagens:

```
[system]    manifesto (estável, byte-a-byte)
[user]      pergunta do usuário
[assistant] {"resposta": null, "solicitacoes": [...]}          ← turno 1
[user]      [RESULTADO_NAVEGACAO] {...}                        ← resultado 1
[assistant] {"resposta": null, "solicitacoes": [...]}          ← turno 2
[user]      [RESULTADO_NAVEGACAO] {...}                        ← resultado 2
...
[assistant] {"resposta": "...", "solicitacoes": []}            ← final
```

Pontos-chave:

- O **system prompt nunca muda** enquanto a assinatura do estado não mudar → cache-hit em todos os turnos.
- Cada `[RESULTADO_NAVEGACAO]` é serializado **deterministicamente** (ordem estável, sem timestamps).
- O histórico de diálogo do usuário fica **antes** dos turnos de navegação, para não ser expulso.
- **Reuso entre turnos**: os turnos de navegação da pergunta anterior permanecem no contexto (cota separada, ver 4.7). A LLM pode responder a nova pergunta consultando a navegação anterior.
- **Invalidação por mudança de estado**: quando fundamentos são recarregados, um novo resumo é cacheado, ou a watchlist muda, o manifesto é recomputado (assinatura muda) e o histórico de navegação é **descartado** automaticamente.
- **Limpeza manual**: "Limpar" no painel reinicia a sessão e descarta o histórico de navegação.
- **`resetar_navegacao`**: a LLM pode pedir explicitamente o descarte, se detectar mudança de assunto.

Sequência ponta a ponta:

```
[Tk] _enviar ─┬─ snapshot fundamentos/watchlist/histórico
              ├─ registra "user"
              └─ BackgroundManager.submit(grupo=chat, LATEST_WINS)
                          │
[worker] _executar ── heartbeat(30s)
              │   ArvoreConhecimento.montar_manifesto
              │   loop de navegação (até 10 ciclos):
              │       ├─ completion
              │       ├─ _extrair_json
              │       ├─ [se negativa] devolve negativa estruturada
              │       ├─ ProtocoloNavegacao.validar
              │       ├─ [gate de tokens do turno]
              │       ├─ [gate de iterações]
              │       ├─ ArvoreConhecimento.executar(solicitacoes)
              │       └─ serializa [RESULTADO_NAVEGACAO]
              └─ ctx.resultado(RespostaChat)
                          │
[Tk] _concluir_ok ── registra "assistant" + fontes + tokens
```

### 4.6 Gates, limites e confirmações

| Gate                                  | Valor padrão            | Parametrizável | Ação                                  |
| ------------------------------------- | ----------------------- | -------------- | ------------------------------------- |
| Teto do manifesto                     | 4K tokens               | sim            | Degradação para "só chaves"           |
| Tokens de navegação por turno         | 64K tokens              | sim            | Pede autorização ao usuário           |
| Tokens de navegação acumulados (cota) | 32K tokens              | sim            | Descarta turnos mais antigos em pares |
| Iterações por pergunta                | 10 ciclos               | sim            | Pede autorização ao usuário           |
| Operações por turno                   | 8                       | sim            | Erro estruturado à LLM                |
| Resultados por `buscar`               | 50                      | sim            | Trunca com `truncado: true`           |
| Timeout de regex                      | 100 ms                  | sim            | Aborta busca, erro à LLM              |
| Varredura em disco por `buscar`       | 500 ms / 200 arquivos   | sim            | Trunca varredura                      |
| Janela total (system+diálogo+nav)     | 80% da janela do modelo | sim            | Alerta no display                     |

**Diálogo de confirmação**: informa **apenas tokens** (número adicional do turno). A negativa é devolvida à LLM como mensagem estruturada:

```json
{ "negado": true, "motivo": "custo", "tokens_solicitados": 45000 }
```

Motivos canônicos: `"custo"`, `"limite_iteracoes"`, `"timeout_regex"`, `"resultado_truncado"`.

Comportamento esperado da LLM por motivo (instrução no `SYSTEM_PROMPT`):

- `"custo"` → usar estratégia mais barata (busca mais específica, `contar` antes de `listar`).
- `"limite_iteracoes"` → **resumo final obrigatório** do que já tem.
- `"timeout_regex"` → regex mais simples ou `listar` direto.
- `"resultado_truncado"` → refinar a busca.

**Repetição de negativa**: se a LLM repetir o mesmo pedido já negado, o worker **não executa** e devolve erro estruturado, forçando o resumo.

### 4.7 Seleção do histórico (diálogo × navegação)

Duas cotas separadas, cada uma com teto próprio:

- **Diálogo**: mensagens com `enviar_ao_modelo=True` e conteúdo não vazio, de trás para frente, até **10 mensagens** e **8.000 caracteres**. Erros e avisos do assistente são registrados com `enviar_ao_modelo=False` e **não** entram.
- **Navegação**: pares `(assistant, [RESULTADO_NAVEGACAO])`, **reusados entre perguntas** por padrão, até **32K tokens**. Ao estourar, descarta os pares mais antigos **em conjunto** (nunca assistant órfão).

Ordem no payload: `system (manifesto) → diálogo → navegação acumulada → turno de navegação corrente`.

### 4.8 Cache de prompt e contabilidade de tokens

- O adaptador extrai `usage.prompt_tokens`, `completion_tokens` e detalhes de cache de forma tolerante (fallbacks: `cache_read_input_tokens`, `prompt_cache_hit_tokens`, `cache_creation_input_tokens`).
- `_ajustar_uso`: se o provedor reporta cache-hit, usa-o; caso contrário, **estima** quando há contador de tokens injetado, o provedor **suporta cache** e o prefixo é repetido. Estimativa = `token_counter(prefixo)`, memoizada por prefixo.
- **Contadores separados**: `entrada`, `saida`, `entrada_cache`, `ultimo_prompt`, e **duas cotas** (`dialogo`, `navegacao`). `entrada` acumula `max(0, entrada - entrada_cache)`.
- Rótulo na barra de status: `Tokens: X entrada / Y saída / Z contexto (N%) · nav: W/32K`.
- **Gate de janela total**: quando `system + diálogo + navegação` > 80% da janela do modelo, o display destaca em cor de alerta.
- Provedores sem cache de prompt (ex.: Ollama local) **não têm desconto financeiro**; o benefício é apenas menos tokens trafegados. Documentado no Evaluate.
- **Memoização da contagem de tokens por caminho + versão do dado** para evitar `token_counter` caro em watchlists grandes.

### 4.9 Segurança do regex

Decisão: usar a biblioteca **`regex`** (suporta `timeout=`) como dependência do chat.

- **Timeout por busca**: 100 ms (parametrizável).
- **Limite de resultados**: 50 por busca.
- **Bloqueio de padrões catastróficos**: heurística sobre lookarounds aninhados, `.*` ilimitado e backreferences. Falso positivo → erro estruturado pedindo regex mais simples.
- **Varredura em disco**: teto de 500 ms / 200 arquivos para `buscar` em conteúdo pesado.
- **Índice invertido em memória** para campos quentes (tickers, títulos) acelera `buscar` sem tocar disco no caso comum.

### 4.10 Execução assíncrona, cancelamento e confirmações

- **Manager local por painel** (`EnvioMixin`, `envio.py`): isola thread/fila do chat do `BackgroundManager` global.
- **Política `LATEST_WINS`**: novo envio substitui o anterior; desfecho tardio é descartado.
- **Heartbeat** a cada 30 s mantém `ultima_atividade` fresco durante chamadas longas e espera de confirmação; o **watchdog** (inatividade de 120 s) não mata o job. Cancelamento interrompe o grupo `chat`.
- **Confirmação via evento `Confirmacao`**: worker publica e bloqueia; interface responde na thread do Tk; timeout padrão de **300 s**.
- O botão "Limpar" reinicia a sessão e descarta o histórico de navegação.

### 4.11 Configuração, presets e limite de taxa

- Configuração em `~/.flowscope/config.json`, bloco `llm.chat`, com `provider` ativo e mapa `providers` (`api_url`, `model`, `api_key`, `rpm`). Gravação _read-modify-write_.
- **`input_limitado` deixa de existir.** Chave antiga é ignorada na leitura (migração silenciosa).
- Presets (`infrastructure/llm/presets.py`): `none`, `openai`, `gemini`, `copilot`, `claude`, `deepseek`, `ollama`, `custom`. Adaptador usa sempre endpoints OpenAI-compatible (`custom_llm_provider="openai"`).
- `RateLimiter`: RPM padrão **5**, janela deslizante de 60 s, enfileira excedentes.
- "Enviar" só habilita com LLM configurada (`provider != none` e liteLLM presente) **e** fundamentos carregados.

### 4.12 Tratamento de erros

- Exceções nativas do liteLLM traduzidas para hierarquia de domínio (`LLMCommunicationError`, `LLMRateLimitError`, `LLMProviderError`, `LLMServiceUnavailableError`, `LLMUnavailableError`).
- `LLMUnavailableError` → `dados="indisponivel"` (painel volta a "não configurado").
- Demais `LLMError` e exceções inesperadas → `dados="erro"` (mensagem amigável + log).
- **Erros de protocolo** (JSON inválido, op desconhecida, caminho inválido): devolvidos à LLM como erro estruturado; contam iteração; não encerram o loop.
- **Erros de regex**: erro estruturado com motivo; contam iteração.
- Mensagens de erro do assistente são registradas com `enviar_ao_modelo=False`.

### 4.13 Ponto de extensão

A árvore é o novo ponto de extensão. `llm-chat-rag` deixa de ser "plugar fonte no sufixo" e passa a **enriquecer nós da árvore** (ex.: `/documentos/<ticker>/chunks/<n>` populado por indexação vetorial), mantendo o protocolo de navegação intacto. Novas fontes (ex.: novos catálogos) plugam-se criando ramos no manifesto e resolvendo caminhos na árvore.

### 4.14 Migração do mecanismo anterior

- **Removidos**: `input_limitado` e `MANIFESTO_RECURSOS`; `## Recursos iniciais`; `_escalar_sob_demanda`; modo `input_limitado` de 3 completions.
- **Substituídos**: `FonteNoticias` (sufixo volátil) → provider do ramo `/noticias`; gate 3/4–7/8+ docs → gate único de tokens; `_escalar` → loop de navegação; tetos em caracteres (12k/doc, 40k docs, 64k índice, 48k notícias) → tetos em tokens (por nó, por operação, agregado do turno, cota de navegação).
- **Preservados**: porta `LLMPort`, `_extrair_json` tolerante, `RateLimiter`, `ContadorTokens` (estendido), execução assíncrona, heartbeat, `LATEST_WINS`, evento `Confirmacao`.
- **Chave antiga `input_limitado`** em `config.json` é ignorada.

---

## 5. Evaluate (Avaliação)

### Vantagens

- **Cache-hit máximo**: prefixo estável (manifesto) pequeno e fixo, byte-a-byte idêntico entre turnos.
- **Mínimo de input tokens**: granularidade fina; a LLM pede só o que precisa; `contar`/`existe` antes de `listar`.
- **Seleção orientada pela LLM**: protocolo determinístico e auditável, sem caixa-preta.
- **Reuso entre turnos**: navegação anterior responde a novas perguntas sem re-navegar.
- **Cache-only e sem efeitos colaterais**: nada é resumido nem extraído durante o chat.
- **Provedor-agnóstico**: JSON no corpo, sem tool calls; presets cobrem OpenAI-compatible e Ollama.
- **UI responsiva e cancelável**: execução fora do Tk, heartbeat, `LATEST_WINS`, cancelamento cooperativo.
- **Controle de custo visível**: contador de tokens em duas cotas + gate de janela total.
- **Testável offline**: protocolo determinístico permite LLM fake.

### Limitações e mitigações

| Limitação                                   | Mitigação                                                                          |
| ------------------------------------------- | ---------------------------------------------------------------------------------- |
| Manifesto com metadados curtos pode crescer | Teto de 4K tokens + degradação para "só chaves" + teste de regressão               |
| LLM pode não seguir JSON estrito            | `_extrair_json` tolerante + fallback textual + retry único                         |
| Contexto total pode crescer (reuso + cotas) | Gate de janela total a 80% + cota de navegação a 32K                               |
| Staleness por reuso                         | Invalidação por mudança de estado + `resetar_navegacao` + instrução no prompt      |
| ReDoS                                       | Lib `regex` com timeout + limite de resultados + bloqueio de padrões catastróficos |
| Busca em disco lenta                        | Índice invertido em memória + teto de varredura (500 ms / 200 arquivos)            |
| Custo de `token_counter`                    | Memoização por caminho + versão do dado                                            |
| LLM ignora negativa                         | Worker recusa repetição do mesmo pedido negado                                     |
| Mais iterações (latência)                   | Paralelismo de ops + `contar`/`existe` + gates                                     |
| Sem desconto de cache em provedores locais  | Documentado; ganho é menos tokens, não desconto                                    |
| Sem persistência de histórico entre sessões | Sessão em memória por design; "Limpar" reinicia                                    |
| Tickers ambíguos dependem da LLM            | `SYSTEM_PROMPT` instrui a pedir esclarecimento                                     |

### Conclusão

A árvore de conhecimento navegável resolve o problema com **cache-hit máximo e input mínimo**: o manifesto pequeno e estável é o prefixo cacheável; a LLM navega por granularidade fina, pede buscas regex determinísticas e recebe apenas o resultado; gates explícitos protegem o usuário de custos e de loops. A arquitetura **manifesto + diálogo + navegação em cotas separadas** e o **ponto de extensão por nós da árvore** deixam espaço para a evolução vetorial (`llm-chat-rag`) sem reescrever o protocolo nem romper a porta `LLMPort`.

---

## 6. Referências de implementação

| Tema                                                    | Arquivo                                                             |
| ------------------------------------------------------- | ------------------------------------------------------------------- |
| Painel, sessão e display                                | `src/flowscope/presentation/gui/chat/chat_panel.py`                 |
| Envio assíncrono e confirmações                         | `src/flowscope/presentation/gui/chat/envio.py`                      |
| Contador/formatação de tokens                           | `src/flowscope/presentation/gui/chat/tokens.py`                     |
| Árvore de conhecimento (índice + resolução de caminhos) | `src/flowscope/application/chat/arvore.py` _(novo)_                 |
| Manifesto da árvore (prefixo estável)                   | `src/flowscope/application/chat/manifesto.py` _(novo)_              |
| Protocolo de navegação (parser + validador + executor)  | `src/flowscope/application/chat/protocolo.py` _(novo)_              |
| Loop de navegação e payload                             | `src/flowscope/application/chat/consultar.py` _(reescrito)_         |
| Segurança de regex                                      | `src/flowscope/application/chat/seguranca_regex.py` _(novo)_        |
| Cascata de documentos (cache-only)                      | `src/flowscope/application/chat/documentos.py`                      |
| Fundamentos compactos                                   | `src/flowscope/application/chat/fundamentos.py`                     |
| Bloco de conhecimento                                   | `src/flowscope/application/chat/conhecimento.py`                    |
| Fonte de notícias (2 camadas)                           | `src/flowscope/application/chat/noticias.py`                        |
| Índice de notícias e filtro                             | `src/flowscope/application/noticias/fonte_chat.py`                  |
| Entidades de conversa                                   | `src/flowscope/domain/chat/models.py`                               |
| Porta de completion                                     | `src/flowscope/domain/llm/ports.py`                                 |
| Adaptador liteLLM                                       | `src/flowscope/infrastructure/llm/adapter.py`                       |
| Configuração e presets                                  | `src/flowscope/infrastructure/llm/config.py`, `presets.py`          |
| Factory do provedor                                     | `src/flowscope/infrastructure/llm/factory.py`                       |
| Rate limiter                                            | `src/flowscope/infrastructure/llm/rate_limiter.py`                  |
| Wiring da aba                                           | `src/flowscope/presentation/gui/app_tab_layout.py`, `app_wiring.py` |
| Diálogo de configuração                                 | `src/flowscope/presentation/gui/llm/config_dialog.py`               |
| Manager/contexto/eventos de background                  | `src/flowscope/presentation/gui/background/`                        |

---

## Apêndice A — Decisões consolidadas

| #   | Decisão                       | Efeito                                                               |
| --- | ----------------------------- | -------------------------------------------------------------------- |
| 1   | Metadados curtos no manifesto | Contexto para a LLM escolher ramos; teto de 4K tokens com degradação |
| 2   | Protocolo em JSON             | Provedor-agnóstico; reusa `_extrair_json`; testável offline          |
| 3   | Paralelizar operações         | Até 8 ops/turno; resultado agregado determinístico                   |
| 4   | `contar` e `existe`           | Dimensionar antes de listar; O(1)–O(filhos)                          |
| 5   | Cota separada de navegação    | 32K tokens; descarte em pares                                        |
| 6   | Reuso de navegação            | Invalidação por mudança de estado + `resetar_navegacao` + "Limpar"   |
| 7   | Sem desconto local            | Documentado; ganho é menos tokens                                    |
| 8   | Gate de 64K por turno         | + gate de janela total a 80%                                         |
| 9   | Iterações por ciclo           | Orçamento por pergunta                                               |
| 10  | Negativa estruturada          | Motivos canônicos; worker recusa repetição                           |
| 11  | `input_limitado` removido     | Chave antiga ignorada                                                |
| 12  | Gate antigo substituído       | Só tokens no diálogo                                                 |
| 13  | Tetos em tokens               | Memoização por caminho + versão                                      |
| 14  | Segurança de regex            | Lib `regex` + timeout + limite + bloqueio                            |
| 15  | Cache de arquivos             | Índice em memória + conteúdo em disco                                |

## Apêndice B — Ordem de implementação

1. Árvore + manifesto (validar teto de 4K, curadoria de metadados, índice híbrido).
2. Protocolo JSON com `listar`, `obter`, `contar`, `existe` (sem `buscar`).
3. Loop de navegação substituindo a cascata; contadores separados.
4. Gates (64K/turno, iterações, janela total) + negativa estruturada.
5. `buscar` com regex + segurança (lib `regex`, timeout, limite, bloqueio).
6. Reuso + invalidação por mudança de estado.
7. Remoção de `input_limitado`, gate antigo, tetos em caracteres.
8. RAG plugando nós na árvore (change `llm-chat-rag`).

## Apêndice C — Riscos residuais

| Risco                         | Mitigação                                               |
| ----------------------------- | ------------------------------------------------------- |
| Manifesto estoura teto        | Degradação + teste de regressão                         |
| LLM não segue JSON            | `_extrair_json` + fallback + retry único                |
| Contexto total estoura janela | Gate de janela total a 80%                              |
| Staleness por reuso           | Invalidação por mudança de estado + `resetar_navegacao` |
| ReDoS                         | Lib `regex` + timeout + limite + bloqueio               |
| Busca em disco lenta          | Índice invertido + teto de varredura                    |
| Custo de `token_counter`      | Memoização por caminho + versão                         |
| LLM ignora negativa           | Worker recusa repetição                                 |
