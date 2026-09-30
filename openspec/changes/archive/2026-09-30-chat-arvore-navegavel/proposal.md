## Why

O mecanismo atual do "Chat AI" monta um prefixo estável grande e pré-computado (conhecimento + fundamentos + resumos de toda a watchlist) e resolve perguntas por uma cascata binária de até três chamadas (resumos → texto integral). O custo do cache-hit cresce com a watchlist, a granularidade é grosseira, a LLM não participa da seleção e a navegação não é reusada entre turnos. A RFC-015 define o destino: expor o estado local como uma **árvore de conhecimento navegável**, com **manifesto pequeno e estável** como prefixo cacheável e **protocolo JSON determinístico**.

## What Changes

- **Nova capability `llm-chat-tree`**: árvore de conhecimento cache-only (índice de caminhos em memória + conteúdo no cache de arquivos), manifesto estável (teto de 4K tokens) e protocolo JSON de navegação (`listar`, `obter`, `contar`, `existe`, `buscar`, `buscar_semantico`, `resetar_navegacao`) com gates de tokens e iterações.
- `llm-chat-llm` **modificada**: a cascata de até três chamadas é substituída por um **loop de navegação** (até 10 ciclos) sobre a porta `LLMPort`; o contrato de resposta passa de `{resposta, documentos}` para `{resposta, solicitacoes:[{op,...}]}`; o prefixo estável (manifesto) e a estimativa de cache são preservados.
- `llm-chat-context` **modificada**: a cascata de documentos e toda a máquina de `input_limitado` são substituídas por **fontes de nós** (conhecimento, fundamentos, documentos, notícias) e resolução por caminho.
- **BREAKING** `llm-config` e `llm-gui`: o campo `input_limitado` é **eliminado** (config, caixa de seleção, confirmação de recursos); a chave antiga é ignorada na leitura.
- `llm-chat-tokens` **modificada**: contadores e cotas separados de **diálogo** e **navegação**, rótulo com `nav: W/32K` e gate de janela total a 80%.
- `noticias-chat-context` **modificada**: as notícias passam a ser o **ramo `/noticias`** navegável pela LLM; o filtro determinístico por pergunta e a escalada em duas camadas são substituídos por `listar`/`buscar`/`obter`.
- `llm-chat-rag` (change existente, implementação **postergável**): ajuste apenas de planejamento — a fonte vetorial deixa de compor o sufixo do prompt e passa a **retroalimentar a op `buscar_semantico`** da árvore, com a dependência re-apontada de `cache-prompt-chat` para `chat-arvore-navegavel`.

## Capabilities

### New Capabilities

- `llm-chat-tree`: árvore de conhecimento navegável (índice de caminhos, manifesto estável, protocolo JSON de operações, resolução de nós, gates de tokens/iterações, reuso e invalidação de navegação, segurança de regex).

### Modified Capabilities

- `llm-chat-llm`: orquestração deixa de ser cascata de até três chamadas e passa a ser loop de navegação; contrato de resposta estruturada muda para `solicitacoes`; tetos e negativa estruturada.
- `llm-chat-context`: o contexto deixa de ser bloco estável pré-computado + cascata e passa a ser árvore de nós; `input_limitado` e o contexto inicial sob demanda são removidos.
- `llm-config`: remoção do campo `input_limitado` do bloco `llm.chat` (leitura tolerante à chave antiga).
- `llm-gui`: remoção da caixa "janela de entrada limitada" e do diálogo de confirmação de recursos iniciais.
- `llm-chat-tokens`: cotas separadas de diálogo e navegação e novo rótulo de tokens.
- `noticias-chat-context`: índice e leitura sob demanda passam a ser nós da árvore navegados pela LLM, sem filtro determinístico por pergunta nem confirmação de envio.

## Impact

- **Código**: novos `src/flowscope/application/chat/{arvore,manifesto,protocolo,seguranca_regex}.py`; `consultar.py` reescrito (loop); `contexto.py` reduzido a fontes de nós; `noticias.py`, `documentos.py`, `fundamentos.py`, `conhecimento.py` viram provedores de ramos; `presentation/gui/chat/` ajusta display de tokens e remove a confirmação de recursos; `infrastructure/llm/config.py` e `presets.py` removem `input_limitado`.
- **Dependências**: `regex` (timeout de busca) no grupo opcional `[llm]`; `buscar_semantico` não introduz dependência obrigatória (backend opcional pela `llm-chat-rag`).
- **Specs substituídas**: requisitos de `llm-chat-context` e `llm-chat-llm` provenientes de `llm-chat-contexto-sob-demanda` e `cache-prompt-chat` (arquivadas) são redefinidos.
- **Coordenação**: `llm-chat-rag` (muda apenas o planejamento; implementação fica pendente e opcional).
